from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
import requests
from models import Book, Reward

nook_bp = Blueprint('nook', __name__)

def search_google_books(query, max_results=10):
    """Search Google Books API"""
    try:
        api_key = current_app.config.get('GOOGLE_BOOKS_API_KEY')
        url = f"https://www.googleapis.com/books/v1/volumes"
        params = {
            'q': query,
            'maxResults': max_results,
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        books = []
        
        for item in data.get('items', []):
            volume_info = item.get('volumeInfo', {})
            books.append({
                'google_id': item.get('id'),
                'title': volume_info.get('title', ''),
                'authors': volume_info.get('authors', []),
                'description': volume_info.get('description', ''),
                'page_count': volume_info.get('pageCount', 0),
                'cover_image': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                'genre': ', '.join(volume_info.get('categories', [])),
                'isbn': next((identifier['identifier'] for identifier in volume_info.get('industryIdentifiers', []) 
                            if identifier['type'] in ['ISBN_13', 'ISBN_10']), ''),
                'published_date': volume_info.get('publishedDate', '')
            })
        
        return books
    except Exception as e:
        return []

@nook_bp.route('/books', methods=['GET'])
@jwt_required()
def get_books():
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status')  # to_read, reading, finished
        genre = request.args.get('genre')
        sort_by = request.args.get('sort_by', 'added_at')  # added_at, title, progress
        order = request.args.get('order', 'desc')  # asc, desc
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # Build query
        query = {'user_id': ObjectId(current_user_id)}
        
        if status:
            query['status'] = status
        
        if genre:
            query['genre'] = {'$regex': genre, '$options': 'i'}
        
        # Build sort
        sort_direction = 1 if order == 'asc' else -1
        sort_field = sort_by
        
        # Get books with pagination
        skip = (page - 1) * limit
        books_cursor = current_app.mongo.db.books.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
        books = [Book(book_data).to_dict() for book_data in books_cursor]
        
        # Get total count
        total_count = current_app.mongo.db.books.count_documents(query)
        
        # Calculate stats
        stats = {
            'total_books': current_app.mongo.db.books.count_documents({'user_id': ObjectId(current_user_id)}),
            'to_read': current_app.mongo.db.books.count_documents({'user_id': ObjectId(current_user_id), 'status': 'to_read'}),
            'reading': current_app.mongo.db.books.count_documents({'user_id': ObjectId(current_user_id), 'status': 'reading'}),
            'finished': current_app.mongo.db.books.count_documents({'user_id': ObjectId(current_user_id), 'status': 'finished'})
        }
        
        return jsonify({
            'books': books,
            'stats': stats,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get books', 'details': str(e)}), 500

@nook_bp.route('/books/<book_id>', methods=['GET'])
@jwt_required()
def get_book(book_id):
    try:
        current_user_id = get_jwt_identity()
        
        book_data = current_app.mongo.db.books.find_one({
            '_id': ObjectId(book_id),
            'user_id': ObjectId(current_user_id)
        })
        
        if not book_data:
            return jsonify({'error': 'Book not found'}), 404
        
        book = Book(book_data)
        
        # Get reading sessions for this book
        sessions = list(current_app.mongo.db.reading_sessions.find({
            'user_id': ObjectId(current_user_id),
            'book_id': ObjectId(book_id)
        }).sort('date', -1).limit(10))
        
        return jsonify({
            'book': book.to_dict(),
            'recent_sessions': sessions
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get book', 'details': str(e)}), 500

@nook_bp.route('/books', methods=['POST'])
@jwt_required()
def add_book():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        # Create book data
        book_data = {
            'user_id': ObjectId(current_user_id),
            'title': data['title'],
            'authors': data.get('authors', []),
            'description': data.get('description', ''),
            'page_count': data.get('page_count', 0),
            'current_page': data.get('current_page', 0),
            'status': data.get('status', 'to_read'),
            'rating': 0,
            'cover_image': data.get('cover_image', ''),
            'genre': data.get('genre', ''),
            'isbn': data.get('isbn', ''),
            'published_date': data.get('published_date', ''),
            'added_at': datetime.utcnow(),
            'quotes': [],
            'takeaways': []
        }
        
        # Insert book
        result = current_app.mongo.db.books.insert_one(book_data)
        book_data['_id'] = result.inserted_id
        
        # Award points for adding a book
        reward_data = {
            'user_id': ObjectId(current_user_id),
            'points': 5,
            'source': 'nook',
            'description': f'Added book: {data["title"]}',
            'earned_at': datetime.utcnow(),
            'metadata': {'book_id': str(result.inserted_id)}
        }
        
        current_app.mongo.db.rewards.insert_one(reward_data)
        
        # Update user points
        current_app.mongo.db.users.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$inc': {'points': 5}}
        )
        
        book = Book(book_data)
        
        return jsonify({
            'message': 'Book added successfully',
            'book': book.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to add book', 'details': str(e)}), 500

@nook_bp.route('/books/<book_id>', methods=['PUT'])
@jwt_required()
def update_book(book_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Check if book exists and belongs to user
        book_data = current_app.mongo.db.books.find_one({
            '_id': ObjectId(book_id),
            'user_id': ObjectId(current_user_id)
        })
        
        if not book_data:
            return jsonify({'error': 'Book not found'}), 404
        
        # Allowed fields to update
        allowed_fields = [
            'title', 'authors', 'description', 'page_count', 
            'status', 'rating', 'genre', 'isbn'
        ]
        
        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Check if book is being marked as finished
        if data.get('status') == 'finished' and book_data['status'] != 'finished':
            update_data['finished_at'] = datetime.utcnow()
            
            # Award completion points
            reward_data = {
                'user_id': ObjectId(current_user_id),
                'points': 50,
                'source': 'nook',
                'description': f'Finished reading: {book_data["title"]}',
                'earned_at': datetime.utcnow(),
                'metadata': {'book_id': book_id}
            }
            
            current_app.mongo.db.rewards.insert_one(reward_data)
            current_app.mongo.db.users.update_one(
                {'_id': ObjectId(current_user_id)},
                {'$inc': {'points': 50}}
            )
        
        # Update book
        current_app.mongo.db.books.update_one(
            {'_id': ObjectId(book_id)},
            {'$set': update_data}
        )
        
        # Get updated book
        updated_book_data = current_app.mongo.db.books.find_one({'_id': ObjectId(book_id)})
        book = Book(updated_book_data)
        
        return jsonify({
            'message': 'Book updated successfully',
            'book': book.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update book', 'details': str(e)}), 500

@nook_bp.route('/books/<book_id>/progress', methods=['POST'])
@jwt_required()
def update_progress(book_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if 'current_page' not in data:
            return jsonify({'error': 'Current page is required'}), 400
        
        current_page = data['current_page']
        
        # Get book
        book_data = current_app.mongo.db.books.find_one({
            '_id': ObjectId(book_id),
            'user_id': ObjectId(current_user_id)
        })
        
        if not book_data:
            return jsonify({'error': 'Book not found'}), 404
        
        # Calculate pages read in this session
        pages_read = max(0, current_page - book_data.get('current_page', 0))
        
        # Update book progress
        update_data = {'current_page': current_page}
        
        # Auto-update status based on progress
        if current_page > 0 and book_data['status'] == 'to_read':
            update_data['status'] = 'reading'
        elif current_page >= book_data.get('page_count', 0) and book_data['status'] != 'finished':
            update_data['status'] = 'finished'
            update_data['finished_at'] = datetime.utcnow()
        
        current_app.mongo.db.books.update_one(
            {'_id': ObjectId(book_id)},
            {'$set': update_data}
        )
        
        # Create reading session
        session_data = {
            'user_id': ObjectId(current_user_id),
            'book_id': ObjectId(book_id),
            'pages_read': pages_read,
            'current_page': current_page,
            'duration_minutes': data.get('duration_minutes', 0),
            'notes': data.get('session_notes', ''),
            'date': datetime.utcnow()
        }
        
        current_app.mongo.db.reading_sessions.insert_one(session_data)
        
        # Award points for reading (1 point per page, max 20 per session)
        points_earned = min(pages_read, 20)
        if points_earned > 0:
            reward_data = {
                'user_id': ObjectId(current_user_id),
                'points': points_earned,
                'source': 'nook',
                'description': f'Read {pages_read} pages in {book_data["title"]}',
                'earned_at': datetime.utcnow(),
                'metadata': {'book_id': book_id, 'pages_read': pages_read}
            }
            
            current_app.mongo.db.rewards.insert_one(reward_data)
            current_app.mongo.db.users.update_one(
                {'_id': ObjectId(current_user_id)},
                {'$inc': {'points': points_earned}}
            )
        
        # Get updated book
        updated_book_data = current_app.mongo.db.books.find_one({'_id': ObjectId(book_id)})
        book = Book(updated_book_data)
        
        return jsonify({
            'message': 'Progress updated successfully',
            'book': book.to_dict(),
            'points_earned': points_earned
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update progress', 'details': str(e)}), 500

@nook_bp.route('/books/<book_id>/quotes', methods=['POST'])
@jwt_required()
def add_quote(book_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('text'):
            return jsonify({'error': 'Quote text is required'}), 400
        
        # Check if book exists and belongs to user
        book_data = current_app.mongo.db.books.find_one({
            '_id': ObjectId(book_id),
            'user_id': ObjectId(current_user_id)
        })
        
        if not book_data:
            return jsonify({'error': 'Book not found'}), 404
        
        # Create quote
        quote_data = {
            'text': data['text'],
            'page': data.get('page', ''),
            'context': data.get('context', ''),
            'added_at': datetime.utcnow()
        }
        
        # Add quote to book
        current_app.mongo.db.books.update_one(
            {'_id': ObjectId(book_id)},
            {'$push': {'quotes': quote_data}}
        )
        
        # Award points for adding quote
        reward_data = {
            'user_id': ObjectId(current_user_id),
            'points': 3,
            'source': 'nook',
            'description': f'Added quote from {book_data["title"]}',
            'earned_at': datetime.utcnow(),
            'metadata': {'book_id': book_id}
        }
        
        current_app.mongo.db.rewards.insert_one(reward_data)
        current_app.mongo.db.users.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$inc': {'points': 3}}
        )
        
        return jsonify({
            'message': 'Quote added successfully',
            'quote': quote_data
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to add quote', 'details': str(e)}), 500

@nook_bp.route('/books/<book_id>/takeaways', methods=['POST'])
@jwt_required()
def add_takeaway(book_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('takeaway'):
            return jsonify({'error': 'Takeaway text is required'}), 400
        
        # Check if book exists and belongs to user
        book_data = current_app.mongo.db.books.find_one({
            '_id': ObjectId(book_id),
            'user_id': ObjectId(current_user_id)
        })
        
        if not book_data:
            return jsonify({'error': 'Book not found'}), 404
        
        # Create takeaway
        takeaway_data = {
            'takeaway': data['takeaway'],
            'page_reference': data.get('page_reference', ''),
            'added_at': datetime.utcnow()
        }
        
        # Add takeaway to book
        current_app.mongo.db.books.update_one(
            {'_id': ObjectId(book_id)},
            {'$push': {'takeaways': takeaway_data}}
        )
        
        # Award points for adding takeaway
        reward_data = {
            'user_id': ObjectId(current_user_id),
            'points': 2,
            'source': 'nook',
            'description': f'Added takeaway from {book_data["title"]}',
            'earned_at': datetime.utcnow(),
            'metadata': {'book_id': book_id}
        }
        
        current_app.mongo.db.rewards.insert_one(reward_data)
        current_app.mongo.db.users.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$inc': {'points': 2}}
        )
        
        return jsonify({
            'message': 'Takeaway added successfully',
            'takeaway': takeaway_data
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to add takeaway', 'details': str(e)}), 500

@nook_bp.route('/search', methods=['GET'])
@jwt_required()
def search_books():
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search Google Books
        books = search_google_books(query)
        
        return jsonify({
            'books': books,
            'total': len(books)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500

@nook_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    try:
        current_user_id = get_jwt_identity()
        
        # Get date range
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Reading statistics
        total_books = current_app.mongo.db.books.count_documents({'user_id': ObjectId(current_user_id)})
        finished_books = current_app.mongo.db.books.count_documents({
            'user_id': ObjectId(current_user_id),
            'status': 'finished'
        })
        
        # Reading sessions in date range
        sessions = list(current_app.mongo.db.reading_sessions.find({
            'user_id': ObjectId(current_user_id),
            'date': {'$gte': start_date}
        }))
        
        total_pages_read = sum(session.get('pages_read', 0) for session in sessions)
        total_reading_time = sum(session.get('duration_minutes', 0) for session in sessions)
        
        # Calculate reading streak
        reading_streak = 0
        current_date = datetime.utcnow().date()
        
        while True:
            day_sessions = current_app.mongo.db.reading_sessions.count_documents({
                'user_id': ObjectId(current_user_id),
                'date': {
                    '$gte': datetime.combine(current_date, datetime.min.time()),
                    '$lt': datetime.combine(current_date + timedelta(days=1), datetime.min.time())
                }
            })
            
            if day_sessions > 0:
                reading_streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        # Genre distribution
        books_by_genre = list(current_app.mongo.db.books.aggregate([
            {'$match': {'user_id': ObjectId(current_user_id)}},
            {'$group': {'_id': '$genre', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]))
        
        return jsonify({
            'total_books': total_books,
            'finished_books': finished_books,
            'total_pages_read': total_pages_read,
            'total_reading_time': total_reading_time,
            'reading_streak': reading_streak,
            'average_pages_per_session': total_pages_read / max(1, len(sessions)),
            'books_by_genre': books_by_genre,
            'recent_sessions': sessions[-10:] if sessions else []
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get analytics', 'details': str(e)}), 500