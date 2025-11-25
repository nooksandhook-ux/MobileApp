from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

themes_bp = Blueprint('themes', __name__)

@themes_bp.route('/', methods=['GET'])
@jwt_required()
def get_themes():
    try:
        themes = [
            {
                'id': 'light',
                'name': 'Light',
                'description': 'Clean and bright theme for daytime use',
                'primary_color': '#007bff',
                'background_color': '#ffffff',
                'text_color': '#333333',
                'is_premium': False
            },
            {
                'id': 'dark',
                'name': 'Dark',
                'description': 'Easy on the eyes for low-light environments',
                'primary_color': '#bb86fc',
                'background_color': '#121212',
                'text_color': '#ffffff',
                'is_premium': False
            },
            {
                'id': 'retro',
                'name': 'Retro',
                'description': 'Vintage-inspired with warm colors',
                'primary_color': '#ff6b35',
                'background_color': '#f4f1de',
                'text_color': '#3d405b',
                'is_premium': False
            },
            {
                'id': 'neon',
                'name': 'Neon',
                'description': 'Cyberpunk-style with bright accents',
                'primary_color': '#00ffff',
                'background_color': '#0a0a0a',
                'text_color': '#00ff00',
                'is_premium': True
            },
            {
                'id': 'forest',
                'name': 'Forest',
                'description': 'Nature-inspired with earth tones',
                'primary_color': '#2d5016',
                'background_color': '#f0f4ec',
                'text_color': '#1b3409',
                'is_premium': True
            },
            {
                'id': 'ocean',
                'name': 'Ocean',
                'description': 'Calm and serene with blue tones',
                'primary_color': '#0077be',
                'background_color': '#e6f3ff',
                'text_color': '#003d5c',
                'is_premium': True
            }
        ]
        
        return jsonify({'themes': themes}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get themes', 'details': str(e)}), 500

@themes_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_theme():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        theme_id = data.get('theme_id')
        if not theme_id:
            return jsonify({'error': 'Theme ID is required'}), 400
        
        # Update user's theme preference
        current_app.mongo.db.users.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$set': {'profile.theme': theme_id}}
        )
        
        return jsonify({'message': 'Theme applied successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to apply theme', 'details': str(e)}), 500