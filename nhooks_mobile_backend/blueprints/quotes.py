from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from models import Quote

quotes_bp = Blueprint('quotes', __name__)

@quotes_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_quote():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('book_id') or not data.get('text'):
            return jsonify({'error': 'Book ID and quote text are required'}), 400
        
        # Validate quote length (10-1000 characters)
        quote_text = data['text'].strip()
        if len(quote_text) < 10 or len(quote_text) > 1000:
            return jsonify({'error': 'Quote must be between 10 and 1000 characters'}), 400
        
        # Check if book exists and belongs to user
        book_data = current_app.mongo.db.books.find_one({
            '_id': ObjectId(data['book_id']),
            'user_id': ObjectId(current_user_id)
        })
        
        if not book_data:
            return jsonify({'error': 'Book not found'}), 404
        
        # Create quote submission
        quote_data = {
            'user_id': ObjectId(current_user_id),
            'book_id': ObjectId(data['book_id']),
            'text': quote_text,
            'page': data.get('page', ''),
            'context': data.get('context', ''),
            'status': 'pending',
            'reward_amount': 10,  # ₦10 for Nigerian users
            'submitted_at': datetime.utcnow(),
            'verified_at': None,
            'verified_by': None
        }
        
        result = current_app.mongo.db.quote_submissions.insert_one(quote_data)
        quote_data['_id'] = result.inserted_id
        
        quote = Quote(quote_data)
        
        return jsonify({
            'message': 'Quote submitted for verification',
            'quote': quote.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to submit quote', 'details': str(e)}), 500

@quotes_bp.route('/my-submissions', methods=['GET'])
@jwt_required()
def get_my_submissions():
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status')  # pending, verified, rejected
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # Build query
        query = {'user_id': ObjectId(current_user_id)}
        
        if status:
            query['status'] = status
        
        # Get quotes with pagination
        skip = (page - 1) * limit
        quotes_cursor = current_app.mongo.db.quote_submissions.find(query).sort('submitted_at', -1).skip(skip).limit(limit)
        quotes = []
        
        for quote_data in quotes_cursor:
            quote = Quote(quote_data)
            quote_dict = quote.to_dict()
            
            # Add book title
            book = current_app.mongo.db.books.find_one({'_id': ObjectId(quote_data['book_id'])})
            if book:
                quote_dict['book_title'] = book['title']
            
            quotes.append(quote_dict)
        
        # Get total count
        total_count = current_app.mongo.db.quote_submissions.count_documents(query)
        
        # Calculate earnings
        verified_quotes = current_app.mongo.db.quote_submissions.find({
            'user_id': ObjectId(current_user_id),
            'status': 'verified'
        })
        
        total_earnings = sum(quote.get('reward_amount', 0) for quote in verified_quotes)
        
        return jsonify({
            'quotes': quotes,
            'total_earnings': total_earnings,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get quote submissions', 'details': str(e)}), 500