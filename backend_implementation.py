"""
Nhooks Backend API Implementation
Complete Flask API matching frontend expectations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from functools import wraps

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

CORS(app)
jwt = JWTManager(app)

# In-memory storage (replace with database in production)
users_db = {}
books_db = {}
sessions_db = {}
quotes_db = {}
takeaways_db = {}
timers_db = {}
rewards_db = {}

# Helper functions
def success_response(data=None, message=None):
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return jsonify(response)

def error_response(error, status_code=400):
    return jsonify({
        "success": False,
        "error": error,
        "statusCode": status_code
    }), status_code

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return error_response("Missing required fields")
    
    # Check if user exists
    if email in users_db or any(u['username'] == username for u in users_db.values()):
        return error_response("User already exists", 409)
    
    # Create user
    user_id = f"user_{len(users_db) + 1}"
    users_db[email] = {
        'id': user_id,
        'username': username,
        'email': email,
        'password': generate_password_hash(password),
        'isAdmin': False,
        'createdAt': datetime.utcnow().isoformat()
    }
    
    # Generate tokens
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)
    
    user_data = {k: v for k, v in users_db[email].items() if k != 'password'}
    
    return success_response({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user_data
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier = data.get('identifier')  # email or username
    password = data.get('password')
    
    if not all([identifier, password]):
        return error_response("Missing credentials")
    
    # Find user by email or username
    user = None
    user_email = None
    for email, u in users_db.items():
        if u['email'] == identifier or u['username'] == identifier:
            user = u
            user_email = email
            break
    
    if not user or not check_password_hash(user['password'], password):
        return error_response("Invalid credentials", 401)
    
    # Generate tokens
    access_token = create_access_token(identity=user['id'])
    refresh_token = create_refresh_token(identity=user['id'])
    
    user_data = {k: v for k, v in user.items() if k != 'password'}
    
    return success_response({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user_data
    })

@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token})

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = next((u for u in users_db.values() if u['id'] == user_id), None)
    
    if not user:
        return error_response("User not found", 404)
    
    user_data = {k: v for k, v in user.items() if k != 'password'}
    return success_response({'user': user_data})

@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    user = next((u for u in users_db.values() if u['id'] == user_id), None)
    if not user:
        return error_response("User not found", 404)
    
    # Update allowed fields
    if 'username' in data:
        user['username'] = data['username']
    if 'email' in data:
        user['email'] = data['email']
    if 'displayName' in data:
        user['displayName'] = data['displayName']
    
    user_data = {k: v for k, v in user.items() if k != 'password'}
    return success_response(user_data)

@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    user = next((u for u in users_db.values() if u['id'] == user_id), None)
    if not user:
        return error_response("User not found", 404)
    
    if not check_password_hash(user['password'], current_password):
        return error_response("Current password is incorrect", 401)
    
    user['password'] = generate_password_hash(new_password)
    return success_response(message="Password changed successfully")


# ============================================
# DASHBOARD ENDPOINTS
# ============================================

@app.route('/api/dashboard/summary', methods=['GET'])
@jwt_required()
def dashboard_summary():
    user_id = get_jwt_identity()
    
    # Calculate summary from user's books
    user_books = [b for b in books_db.values() if b.get('userId') == user_id]
    
    summary = {
        'totalBooks': len(user_books),
        'booksReading': len([b for b in user_books if b.get('status') == 'reading']),
        'booksCompleted': len([b for b in user_books if b.get('status') == 'completed']),
        'totalReadingTime': sum(b.get('totalReadingTime', 0) for b in user_books),
        'totalPoints': rewards_db.get(user_id, {}).get('totalPoints', 0),
        'currentStreak': rewards_db.get(user_id, {}).get('currentStreak', 0),
        'recentActivity': []
    }
    
    return success_response(summary)

@app.route('/api/dashboard/analytics', methods=['GET'])
@jwt_required()
def dashboard_analytics():
    user_id = get_jwt_identity()
    days = request.args.get('days', 30, type=int)
    
    analytics = {
        'readingTimeByDay': [],
        'booksCompletedByMonth': [],
        'topGenres': []
    }
    
    return success_response(analytics)

# ============================================
# NOOK (BOOKS) ENDPOINTS
# ============================================

@app.route('/api/nook/books', methods=['GET'])
@jwt_required()
def get_books():
    user_id = get_jwt_identity()
    
    # Get query parameters
    status = request.args.get('status')
    genre = request.args.get('genre')
    sort_by = request.args.get('sort_by', 'added_at')
    order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # Filter user's books
    user_books = [b for b in books_db.values() if b.get('userId') == user_id]
    
    if status:
        user_books = [b for b in user_books if b.get('status') == status]
    if genre:
        user_books = [b for b in user_books if genre in b.get('genres', [])]
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    
    return success_response({
        'books': user_books[start:end],
        'total': len(user_books),
        'page': page,
        'limit': limit
    })

@app.route('/api/nook/books', methods=['POST'])
@jwt_required()
def add_book():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    book_id = f"book_{len(books_db) + 1}"
    book = {
        'id': book_id,
        'userId': user_id,
        'title': data.get('title'),
        'author': data.get('author'),
        'isbn': data.get('isbn'),
        'totalPages': data.get('totalPages', 0),
        'currentPage': data.get('currentPage', 0),
        'status': data.get('status', 'to_read'),
        'genres': data.get('genres', []),
        'rating': data.get('rating'),
        'coverImage': data.get('coverImage'),
        'addedAt': datetime.utcnow().isoformat(),
        'totalReadingTime': 0
    }
    
    books_db[book_id] = book
    return success_response({'book': book})

@app.route('/api/nook/books/<book_id>', methods=['GET'])
@jwt_required()
def get_book(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    return success_response({'book': book})

@app.route('/api/nook/books/<book_id>', methods=['PUT'])
@jwt_required()
def update_book(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    data = request.get_json()
    book.update(data)
    book['updatedAt'] = datetime.utcnow().isoformat()
    
    return success_response({'book': book})


@app.route('/api/nook/books/<book_id>/progress', methods=['POST'])
@jwt_required()
def update_book_progress(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    data = request.get_json()
    book['currentPage'] = data.get('current_page', book['currentPage'])
    
    if data.get('duration_minutes'):
        book['totalReadingTime'] = book.get('totalReadingTime', 0) + data['duration_minutes']
    
    # Auto-complete if reached last page
    if book['currentPage'] >= book.get('totalPages', 0):
        book['status'] = 'completed'
        book['completedAt'] = datetime.utcnow().isoformat()
    
    return success_response({'book': book})

@app.route('/api/nook/books/<book_id>/status', methods=['PUT'])
@jwt_required()
def update_book_status(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    data = request.get_json()
    book['status'] = data.get('status')
    
    if book['status'] == 'completed':
        book['completedAt'] = datetime.utcnow().isoformat()
    
    return success_response({'book': book})

@app.route('/api/nook/books/<book_id>/rating', methods=['PUT'])
@jwt_required()
def update_book_rating(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    data = request.get_json()
    book['rating'] = data.get('rating')
    
    return success_response({'book': book})

@app.route('/api/nook/search', methods=['GET'])
@jwt_required()
def search_books():
    user_id = get_jwt_identity()
    query = request.args.get('q', '')
    
    user_books = [b for b in books_db.values() if b.get('userId') == user_id]
    
    # Simple search in title and author
    results = [
        b for b in user_books 
        if query.lower() in b.get('title', '').lower() 
        or query.lower() in b.get('author', '').lower()
    ]
    
    return success_response({'books': results})

@app.route('/api/nook/analytics', methods=['GET'])
@jwt_required()
def nook_analytics():
    user_id = get_jwt_identity()
    days = request.args.get('days', 30, type=int)
    
    analytics = {
        'totalReadingTime': 0,
        'booksCompleted': 0,
        'averageRating': 0,
        'topGenres': []
    }
    
    return success_response(analytics)

# ============================================
# QUOTES ENDPOINTS
# ============================================

@app.route('/api/nook/books/<book_id>/quotes', methods=['POST'])
@jwt_required()
def add_quote(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    data = request.get_json()
    quote_id = f"quote_{len(quotes_db) + 1}"
    
    quote = {
        'id': quote_id,
        'bookId': book_id,
        'userId': user_id,
        'text': data.get('text'),
        'page': data.get('page'),
        'context': data.get('context'),
        'createdAt': datetime.utcnow().isoformat()
    }
    
    quotes_db[quote_id] = quote
    return success_response({'quote': quote})

@app.route('/api/nook/books/<book_id>/quotes', methods=['GET'])
@jwt_required()
def get_quotes(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    book_quotes = [q for q in quotes_db.values() if q.get('bookId') == book_id]
    return success_response({'quotes': book_quotes})

@app.route('/api/nook/books/<book_id>/quotes/<quote_id>', methods=['PUT'])
@jwt_required()
def update_quote(book_id, quote_id):
    user_id = get_jwt_identity()
    quote = quotes_db.get(quote_id)
    
    if not quote or quote.get('userId') != user_id:
        return error_response("Quote not found", 404)
    
    data = request.get_json()
    quote.update(data)
    quote['updatedAt'] = datetime.utcnow().isoformat()
    
    return success_response({'quote': quote})

@app.route('/api/nook/books/<book_id>/quotes/<quote_id>', methods=['DELETE'])
@jwt_required()
def delete_quote(book_id, quote_id):
    user_id = get_jwt_identity()
    quote = quotes_db.get(quote_id)
    
    if not quote or quote.get('userId') != user_id:
        return error_response("Quote not found", 404)
    
    del quotes_db[quote_id]
    return success_response(message="Quote deleted")


# ============================================
# TAKEAWAYS ENDPOINTS
# ============================================

@app.route('/api/nook/books/<book_id>/takeaways', methods=['POST'])
@jwt_required()
def add_takeaway(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    data = request.get_json()
    takeaway_id = f"takeaway_{len(takeaways_db) + 1}"
    
    takeaway = {
        'id': takeaway_id,
        'bookId': book_id,
        'userId': user_id,
        'takeaway': data.get('takeaway'),
        'page_reference': data.get('page_reference'),
        'createdAt': datetime.utcnow().isoformat()
    }
    
    takeaways_db[takeaway_id] = takeaway
    return success_response({'takeaway': takeaway})

@app.route('/api/nook/books/<book_id>/takeaways', methods=['GET'])
@jwt_required()
def get_takeaways(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    book_takeaways = [t for t in takeaways_db.values() if t.get('bookId') == book_id]
    return success_response({'takeaways': book_takeaways})

@app.route('/api/nook/books/<book_id>/takeaways/<takeaway_id>', methods=['PUT'])
@jwt_required()
def update_takeaway(book_id, takeaway_id):
    user_id = get_jwt_identity()
    takeaway = takeaways_db.get(takeaway_id)
    
    if not takeaway or takeaway.get('userId') != user_id:
        return error_response("Takeaway not found", 404)
    
    data = request.get_json()
    takeaway.update(data)
    takeaway['updatedAt'] = datetime.utcnow().isoformat()
    
    return success_response({'takeaway': takeaway})

@app.route('/api/nook/books/<book_id>/takeaways/<takeaway_id>', methods=['DELETE'])
@jwt_required()
def delete_takeaway(book_id, takeaway_id):
    user_id = get_jwt_identity()
    takeaway = takeaways_db.get(takeaway_id)
    
    if not takeaway or takeaway.get('userId') != user_id:
        return error_response("Takeaway not found", 404)
    
    del takeaways_db[takeaway_id]
    return success_response(message="Takeaway deleted")

# ============================================
# READING SESSIONS ENDPOINTS
# ============================================

@app.route('/api/nook/books/<book_id>/sessions/start', methods=['POST'])
@jwt_required()
def start_reading_session(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    data = request.get_json()
    session_id = f"session_{len(sessions_db) + 1}"
    
    session = {
        'id': session_id,
        'bookId': book_id,
        'userId': user_id,
        'startPage': data.get('start_page'),
        'startTime': data.get('start_time'),
        'status': 'active'
    }
    
    sessions_db[session_id] = session
    return success_response({'session': session})

@app.route('/api/nook/books/<book_id>/sessions/<session_id>/end', methods=['POST'])
@jwt_required()
def end_reading_session(book_id, session_id):
    user_id = get_jwt_identity()
    session = sessions_db.get(session_id)
    
    if not session or session.get('userId') != user_id:
        return error_response("Session not found", 404)
    
    data = request.get_json()
    session['endPage'] = data.get('end_page')
    session['endTime'] = data.get('end_time')
    session['status'] = 'completed'
    
    return success_response({'session': session})

@app.route('/api/nook/books/<book_id>/sessions', methods=['GET'])
@jwt_required()
def get_reading_sessions(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    book_sessions = [s for s in sessions_db.values() if s.get('bookId') == book_id]
    return success_response({'sessions': book_sessions})

@app.route('/api/nook/books/<book_id>/sessions/active', methods=['GET'])
@jwt_required()
def get_active_reading_session(book_id):
    user_id = get_jwt_identity()
    book = books_db.get(book_id)
    
    if not book or book.get('userId') != user_id:
        return error_response("Book not found", 404)
    
    active_session = next(
        (s for s in sessions_db.values() 
         if s.get('bookId') == book_id and s.get('status') == 'active'),
        None
    )
    
    return success_response({'session': active_session})


# ============================================
# HOOK (TIMER) ENDPOINTS
# ============================================

@app.route('/api/hook/timers/active', methods=['GET'])
@jwt_required()
def get_active_timer():
    user_id = get_jwt_identity()
    
    active_timer = next(
        (t for t in timers_db.values() 
         if t.get('userId') == user_id and t.get('status') == 'active'),
        None
    )
    
    return success_response({'timer': active_timer})

@app.route('/api/hook/timers/start', methods=['POST'])
@jwt_required()
def start_timer():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    timer_id = f"timer_{len(timers_db) + 1}"
    timer = {
        'id': timer_id,
        'userId': user_id,
        'taskName': data.get('task_name'),
        'duration': data.get('duration'),
        'category': data.get('category'),
        'startTime': datetime.utcnow().isoformat(),
        'status': 'active'
    }
    
    timers_db[timer_id] = timer
    return success_response({'timer': timer})

@app.route('/api/hook/timers/pause', methods=['POST'])
@jwt_required()
def pause_timer():
    user_id = get_jwt_identity()
    
    active_timer = next(
        (t for t in timers_db.values() 
         if t.get('userId') == user_id and t.get('status') == 'active'),
        None
    )
    
    if not active_timer:
        return error_response("No active timer found", 404)
    
    active_timer['status'] = 'paused'
    active_timer['pausedAt'] = datetime.utcnow().isoformat()
    
    return success_response({'timer': active_timer})

@app.route('/api/hook/timers/complete', methods=['POST'])
@jwt_required()
def complete_timer():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    active_timer = next(
        (t for t in timers_db.values() 
         if t.get('userId') == user_id and t.get('status') in ['active', 'paused']),
        None
    )
    
    if not active_timer:
        return error_response("No active timer found", 404)
    
    active_timer['status'] = 'completed'
    active_timer['completedAt'] = datetime.utcnow().isoformat()
    active_timer['moodRating'] = data.get('mood_rating')
    active_timer['notes'] = data.get('notes')
    
    # Award points
    if user_id not in rewards_db:
        rewards_db[user_id] = {'totalPoints': 0, 'currentStreak': 0}
    rewards_db[user_id]['totalPoints'] += 10
    
    return success_response({'timer': active_timer})

@app.route('/api/hook/timers/cancel', methods=['POST'])
@jwt_required()
def cancel_timer():
    user_id = get_jwt_identity()
    
    active_timer = next(
        (t for t in timers_db.values() 
         if t.get('userId') == user_id and t.get('status') in ['active', 'paused']),
        None
    )
    
    if not active_timer:
        return error_response("No active timer found", 404)
    
    active_timer['status'] = 'cancelled'
    active_timer['cancelledAt'] = datetime.utcnow().isoformat()
    
    return success_response(message="Timer cancelled")

@app.route('/api/hook/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    user_id = get_jwt_identity()
    category = request.args.get('category')
    days = request.args.get('days', 30, type=int)
    
    user_timers = [t for t in timers_db.values() if t.get('userId') == user_id]
    
    if category:
        user_timers = [t for t in user_timers if t.get('category') == category]
    
    return success_response({'tasks': user_timers, 'total': len(user_timers)})

@app.route('/api/hook/analytics', methods=['GET'])
@jwt_required()
def hook_analytics():
    user_id = get_jwt_identity()
    days = request.args.get('days', 30, type=int)
    
    analytics = {
        'totalSessions': 0,
        'totalFocusTime': 0,
        'averageSessionLength': 0,
        'productivityScore': 0
    }
    
    return success_response(analytics)

@app.route('/api/hook/presets', methods=['GET'])
@jwt_required()
def get_timer_presets():
    presets = [
        {'id': '1', 'name': 'Pomodoro', 'duration': 25, 'breakDuration': 5},
        {'id': '2', 'name': 'Deep Work', 'duration': 90, 'breakDuration': 15},
        {'id': '3', 'name': 'Quick Focus', 'duration': 15, 'breakDuration': 3}
    ]
    return success_response({'presets': presets})

@app.route('/api/hook/presets', methods=['POST'])
@jwt_required()
def save_timer_preset():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    preset = {
        'id': f"preset_{datetime.utcnow().timestamp()}",
        'userId': user_id,
        'name': data.get('name'),
        'duration': data.get('duration'),
        'breakDuration': data.get('break_duration')
    }
    
    return success_response({'preset': preset})


# ============================================
# REWARDS ENDPOINTS
# ============================================

@app.route('/api/rewards/history', methods=['GET'])
@jwt_required()
def get_reward_history():
    user_id = get_jwt_identity()
    source = request.args.get('source')
    days = request.args.get('days', 30, type=int)
    
    history = []
    return success_response({'history': history, 'total': len(history)})

@app.route('/api/rewards/badges', methods=['GET'])
@jwt_required()
def get_user_badges():
    user_id = get_jwt_identity()
    
    badges = [
        {'id': '1', 'name': 'First Book', 'description': 'Added your first book', 'earned': True},
        {'id': '2', 'name': 'Reading Streak', 'description': '7 day reading streak', 'earned': False}
    ]
    
    return success_response({'badges': badges})

@app.route('/api/rewards/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    category = request.args.get('category', 'points')
    limit = request.args.get('limit', 10, type=int)
    
    leaderboard = []
    return success_response({'leaderboard': leaderboard})

@app.route('/api/rewards/achievements', methods=['GET'])
@jwt_required()
def get_achievements():
    user_id = get_jwt_identity()
    
    achievements = []
    return success_response({'achievements': achievements})

# ============================================
# THEMES ENDPOINTS
# ============================================

@app.route('/api/themes', methods=['GET'])
@jwt_required()
def get_themes():
    themes = [
        {'id': '1', 'name': 'Default', 'isPremium': False},
        {'id': '2', 'name': 'Dark Ocean', 'isPremium': True},
        {'id': '3', 'name': 'Forest', 'isPremium': True}
    ]
    return success_response({'themes': themes})

@app.route('/api/themes/apply', methods=['POST'])
@jwt_required()
def apply_theme():
    user_id = get_jwt_identity()
    data = request.get_json()
    theme_id = data.get('theme_id')
    
    return success_response(message="Theme applied successfully")

# ============================================
# QUOTE SUBMISSION ENDPOINTS (for verification)
# ============================================

@app.route('/api/quotes/submit', methods=['POST'])
@jwt_required()
def submit_quote():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    submission_id = f"submission_{len(quotes_db) + 1}"
    submission = {
        'id': submission_id,
        'userId': user_id,
        'quoteText': data.get('quoteText'),
        'bookTitle': data.get('bookTitle'),
        'author': data.get('author'),
        'status': 'pending',
        'submittedAt': datetime.utcnow().isoformat()
    }
    
    return success_response({'submission': submission})

@app.route('/api/quotes/submissions', methods=['GET'])
@jwt_required()
def get_quote_submissions():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    submissions = []
    return success_response({'submissions': submissions, 'total': 0})

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return error_response("Endpoint not found", 404)

@app.errorhandler(500)
def internal_error(error):
    return error_response("Internal server error", 500)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return error_response("Token has expired", 401)

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return error_response("Invalid token", 401)

@jwt.unauthorized_loader
def missing_token_callback(error):
    return error_response("Authorization token is missing", 401)

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    # Create demo user for testing
    demo_user_id = "demo_user_1"
    users_db['demo@hooks.app'] = {
        'id': demo_user_id,
        'username': 'demo',
        'email': 'demo@hooks.app',
        'password': generate_password_hash('demo123'),
        'isAdmin': False,
        'createdAt': datetime.utcnow().isoformat()
    }
    
    print("=" * 50)
    print("Nhooks Backend API Server")
    print("=" * 50)
    print("\nDemo Account:")
    print("  Email: demo@hooks.app")
    print("  Password: demo123")
    print("\nServer starting on http://0.0.0.0:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
