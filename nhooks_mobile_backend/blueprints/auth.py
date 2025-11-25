from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
import re
from models import User

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    return len(password) >= 6

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if not validate_password(password):
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        existing_user = current_app.mongo.db.users.find_one({
            '$or': [
                {'email': email},
                {'username': username}
            ]
        })
        
        if existing_user:
            if existing_user['email'] == email:
                return jsonify({'error': 'Email already registered'}), 409
            else:
                return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        user_data = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'is_admin': False,
            'is_active': True,
            'points': 0,
            'level': 1,
            'profile': {
                'theme': 'light',
                'avatar_style': 'initials',
                'display_name': username,
                'bio': '',
                'timezone': 'UTC'
            },
            'preferences': {
                'notifications': True,
                'timer_sound': True,
                'default_timer_duration': 25,
                'animations': True,
                'compact_mode': False,
                'dashboard_layout': 'default'
            },
            'created_at': datetime.utcnow(),
            'last_login': None
        }
        
        result = current_app.mongo.db.users.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        
        # Create access and refresh tokens
        access_token = create_access_token(identity=str(result.inserted_id))
        refresh_token = create_refresh_token(identity=str(result.inserted_id))
        
        # Award registration points
        current_app.mongo.db.rewards.insert_one({
            'user_id': result.inserted_id,
            'points': 10,
            'source': 'system',
            'description': 'Welcome bonus for joining Hooks!',
            'earned_at': datetime.utcnow()
        })
        
        # Update user points
        current_app.mongo.db.users.update_one(
            {'_id': result.inserted_id},
            {'$inc': {'points': 10}}
        )
        
        user = User(user_data)
        
        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('identifier') or not data.get('password'):
            return jsonify({'error': 'Email/username and password are required'}), 400
        
        identifier = data['identifier'].strip()
        password = data['password']
        
        # Find user by email or username
        user_data = current_app.mongo.db.users.find_one({
            '$or': [
                {'email': identifier.lower()},
                {'username': identifier}
            ]
        })
        
        if not user_data:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check password
        if not check_password_hash(user_data['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if account is active
        if not user_data.get('is_active', True):
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Update last login
        current_app.mongo.db.users.update_one(
            {'_id': user_data['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        # Create tokens
        access_token = create_access_token(identity=str(user_data['_id']))
        refresh_token = create_refresh_token(identity=str(user_data['_id']))
        
        user = User(user_data)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        current_user_id = get_jwt_identity()
        
        # Get user data
        user_data = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        
        if not user_data or not user_data.get('is_active', True):
            return jsonify({'error': 'User not found or inactive'}), 404
        
        # Create new access token
        access_token = create_access_token(identity=current_user_id)
        
        user = User(user_data)
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Token refresh failed', 'details': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        
        user_data = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        user = User(user_data)
        
        # Get additional stats
        stats = {
            'total_books': current_app.mongo.db.books.count_documents({'user_id': ObjectId(current_user_id)}),
            'finished_books': current_app.mongo.db.books.count_documents({
                'user_id': ObjectId(current_user_id),
                'status': 'finished'
            }),
            'total_tasks': current_app.mongo.db.completed_tasks.count_documents({'user_id': ObjectId(current_user_id)}),
            'total_badges': current_app.mongo.db.user_badges.count_documents({'user_id': ObjectId(current_user_id)})
        }
        
        return jsonify({
            'user': user.to_dict(),
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get profile', 'details': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Allowed profile fields
        allowed_fields = ['display_name', 'bio', 'timezone', 'theme', 'avatar_style']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[f'profile.{field}'] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update user profile
        result = current_app.mongo.db.users.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'User not found'}), 404
        
        # Get updated user data
        user_data = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        user = User(user_data)
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@auth_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Allowed preference fields
        allowed_fields = [
            'notifications', 'timer_sound', 'default_timer_duration',
            'animations', 'compact_mode', 'dashboard_layout'
        ]
        
        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[f'preferences.{field}'] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update user preferences
        result = current_app.mongo.db.users.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'User not found'}), 404
        
        # Get updated user data
        user_data = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        user = User(user_data)
        
        return jsonify({
            'message': 'Preferences updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update preferences', 'details': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Validate new password
        if not validate_password(new_password):
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        
        # Get user data
        user_data = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if not check_password_hash(user_data['password_hash'], current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        new_password_hash = generate_password_hash(new_password)
        current_app.mongo.db.users.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$set': {'password_hash': new_password_hash}}
        )
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to change password', 'details': str(e)}), 500