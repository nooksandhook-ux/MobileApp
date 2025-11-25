from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin privileges"""
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        
        if not user or not user.get('is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def get_admin_dashboard():
    try:
        # Get system statistics
        total_users = current_app.mongo.db.users.count_documents({})
        active_users = current_app.mongo.db.users.count_documents({'is_active': True})
        total_books = current_app.mongo.db.books.count_documents({})
        total_tasks = current_app.mongo.db.completed_tasks.count_documents({})
        pending_quotes = current_app.mongo.db.quote_submissions.count_documents({'status': 'pending'})
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        new_users_week = current_app.mongo.db.users.count_documents({
            'created_at': {'$gte': week_ago}
        })
        
        new_books_week = current_app.mongo.db.books.count_documents({
            'added_at': {'$gte': week_ago}
        })
        
        completed_tasks_week = current_app.mongo.db.completed_tasks.count_documents({
            'completed_at': {'$gte': week_ago}
        })
        
        # Top users by points
        top_users = list(current_app.mongo.db.users.find(
            {},
            {'username': 1, 'points': 1, 'level': 1}
        ).sort('points', -1).limit(10))
        
        for user in top_users:
            user['_id'] = str(user['_id'])
        
        return jsonify({
            'stats': {
                'total_users': total_users,
                'active_users': active_users,
                'total_books': total_books,
                'total_tasks': total_tasks,
                'pending_quotes': pending_quotes,
                'new_users_week': new_users_week,
                'new_books_week': new_books_week,
                'completed_tasks_week': completed_tasks_week
            },
            'top_users': top_users
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get admin dashboard', 'details': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '')
        
        # Build query
        query = {}
        if search:
            query['$or'] = [
                {'username': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}}
            ]
        
        # Get users with pagination
        skip = (page - 1) * limit
        users_cursor = current_app.mongo.db.users.find(
            query,
            {'password_hash': 0}  # Exclude password hash
        ).sort('created_at', -1).skip(skip).limit(limit)
        
        users = []
        for user in users_cursor:
            user['_id'] = str(user['_id'])
            if isinstance(user.get('created_at'), datetime):
                user['created_at'] = user['created_at'].isoformat()
            if isinstance(user.get('last_login'), datetime):
                user['last_login'] = user['last_login'].isoformat()
            users.append(user)
        
        # Get total count
        total_count = current_app.mongo.db.users.count_documents(query)
        
        return jsonify({
            'users': users,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get users', 'details': str(e)}), 500

@admin_bp.route('/quotes/pending', methods=['GET'])
@jwt_required()
@admin_required
def get_pending_quotes():
    try:
        # Get pending quote submissions
        quotes = list(current_app.mongo.db.quote_submissions.find({
            'status': 'pending'
        }).sort('submitted_at', 1))
        
        # Add user and book information
        for quote in quotes:
            quote['_id'] = str(quote['_id'])
            quote['user_id'] = str(quote['user_id'])
            quote['book_id'] = str(quote['book_id'])
            
            if isinstance(quote.get('submitted_at'), datetime):
                quote['submitted_at'] = quote['submitted_at'].isoformat()
            
            # Get user info
            user = current_app.mongo.db.users.find_one({'_id': ObjectId(quote['user_id'])})
            if user:
                quote['username'] = user['username']
            
            # Get book info
            book = current_app.mongo.db.books.find_one({'_id': ObjectId(quote['book_id'])})
            if book:
                quote['book_title'] = book['title']
                quote['book_authors'] = book.get('authors', [])
        
        return jsonify({'quotes': quotes}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get pending quotes', 'details': str(e)}), 500

@admin_bp.route('/quotes/<quote_id>/verify', methods=['POST'])
@jwt_required()
@admin_required
def verify_quote(quote_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        action = data.get('action')  # 'approve' or 'reject'
        reason = data.get('reason', '')
        
        if action not in ['approve', 'reject']:
            return jsonify({'error': 'Action must be approve or reject'}), 400
        
        # Get quote
        quote = current_app.mongo.db.quote_submissions.find_one({'_id': ObjectId(quote_id)})
        
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        if quote['status'] != 'pending':
            return jsonify({'error': 'Quote has already been processed'}), 409
        
        # Update quote status
        update_data = {
            'status': 'verified' if action == 'approve' else 'rejected',
            'verified_at': datetime.utcnow(),
            'verified_by': ObjectId(current_user_id),
            'verification_reason': reason
        }
        
        current_app.mongo.db.quote_submissions.update_one(
            {'_id': ObjectId(quote_id)},
            {'$set': update_data}
        )
        
        # If approved, award points and create transaction
        if action == 'approve':
            reward_amount = quote.get('reward_amount', 10)
            
            # Award points
            current_app.mongo.db.rewards.insert_one({
                'user_id': quote['user_id'],
                'points': reward_amount,
                'source': 'quotes',
                'description': f'Verified quote reward: ₦{reward_amount}',
                'earned_at': datetime.utcnow(),
                'metadata': {'quote_id': quote_id}
            })
            
            # Update user balance (if implementing cash rewards)
            # current_app.mongo.db.users.update_one(
            #     {'_id': quote['user_id']},
            #     {'$inc': {'balance': reward_amount}}
            # )
        
        return jsonify({
            'message': f'Quote {action}d successfully',
            'quote_id': quote_id,
            'action': action
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to verify quote', 'details': str(e)}), 500