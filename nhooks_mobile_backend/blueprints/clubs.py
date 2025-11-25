from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from models import Club

clubs_bp = Blueprint('clubs', __name__)

@clubs_bp.route('/', methods=['GET'])
@jwt_required()
def get_clubs():
    try:
        current_user_id = get_jwt_identity()
        
        # Get user's clubs
        user_clubs = list(current_app.mongo.db.clubs.find({
            'members': ObjectId(current_user_id)
        }))
        
        # Get public clubs user can join
        public_clubs = list(current_app.mongo.db.clubs.find({
            'is_private': False,
            'members': {'$ne': ObjectId(current_user_id)}
        }).limit(10))
        
        # Convert to Club objects
        user_clubs_list = [Club(club_data).to_dict() for club_data in user_clubs]
        public_clubs_list = [Club(club_data).to_dict() for club_data in public_clubs]
        
        return jsonify({
            'user_clubs': user_clubs_list,
            'public_clubs': public_clubs_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get clubs', 'details': str(e)}), 500

@clubs_bp.route('/', methods=['POST'])
@jwt_required()
def create_club():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Club name is required'}), 400
        
        # Create club
        club_data = {
            'name': data['name'],
            'description': data.get('description', ''),
            'topic': data.get('topic', ''),
            'creator_id': ObjectId(current_user_id),
            'members': [ObjectId(current_user_id)],
            'is_private': data.get('is_private', False),
            'created_at': datetime.utcnow(),
            'current_book': None
        }
        
        result = current_app.mongo.db.clubs.insert_one(club_data)
        club_data['_id'] = result.inserted_id
        
        club = Club(club_data)
        
        return jsonify({
            'message': 'Club created successfully',
            'club': club.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to create club', 'details': str(e)}), 500

@clubs_bp.route('/<club_id>/join', methods=['POST'])
@jwt_required()
def join_club(club_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check if club exists
        club_data = current_app.mongo.db.clubs.find_one({'_id': ObjectId(club_id)})
        
        if not club_data:
            return jsonify({'error': 'Club not found'}), 404
        
        # Check if user is already a member
        if ObjectId(current_user_id) in club_data.get('members', []):
            return jsonify({'error': 'You are already a member of this club'}), 409
        
        # Add user to club
        current_app.mongo.db.clubs.update_one(
            {'_id': ObjectId(club_id)},
            {'$push': {'members': ObjectId(current_user_id)}}
        )
        
        return jsonify({'message': 'Successfully joined the club'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to join club', 'details': str(e)}), 500