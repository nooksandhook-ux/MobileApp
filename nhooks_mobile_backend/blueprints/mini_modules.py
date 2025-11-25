from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime

mini_modules_bp = Blueprint('mini_modules', __name__)

@mini_modules_bp.route('/flashcards', methods=['GET'])
@jwt_required()
def get_flashcards():
    try:
        current_user_id = get_jwt_identity()
        
        flashcards = list(current_app.mongo.db.flashcards.find({
            'user_id': ObjectId(current_user_id)
        }).sort('created_at', -1))
        
        # Convert ObjectId to string
        for card in flashcards:
            card['_id'] = str(card['_id'])
            card['user_id'] = str(card['user_id'])
            if isinstance(card.get('created_at'), datetime):
                card['created_at'] = card['created_at'].isoformat()
        
        return jsonify({'flashcards': flashcards}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get flashcards', 'details': str(e)}), 500

@mini_modules_bp.route('/flashcards', methods=['POST'])
@jwt_required()
def create_flashcard():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('front') or not data.get('back'):
            return jsonify({'error': 'Front and back content are required'}), 400
        
        # Create flashcard
        flashcard_data = {
            'user_id': ObjectId(current_user_id),
            'front': data['front'],
            'back': data['back'],
            'tags': data.get('tags', []),
            'created_at': datetime.utcnow(),
            'last_reviewed': None,
            'review_count': 0,
            'difficulty': 'medium'
        }
        
        result = current_app.mongo.db.flashcards.insert_one(flashcard_data)
        flashcard_data['_id'] = str(result.inserted_id)
        flashcard_data['user_id'] = str(flashcard_data['user_id'])
        flashcard_data['created_at'] = flashcard_data['created_at'].isoformat()
        
        return jsonify({
            'message': 'Flashcard created successfully',
            'flashcard': flashcard_data
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to create flashcard', 'details': str(e)}), 500

@mini_modules_bp.route('/quiz/daily', methods=['GET'])
@jwt_required()
def get_daily_quiz():
    try:
        # Get a sample quiz (in a real app, this would be more sophisticated)
        quiz_questions = [
            {
                'id': 1,
                'question': 'What is the main benefit of the Pomodoro Technique?',
                'options': [
                    'Improved focus and productivity',
                    'Better time management',
                    'Reduced stress',
                    'All of the above'
                ],
                'correct_answer': 3,
                'explanation': 'The Pomodoro Technique helps with focus, time management, and stress reduction.'
            },
            {
                'id': 2,
                'question': 'How long is a standard Pomodoro work session?',
                'options': ['15 minutes', '25 minutes', '30 minutes', '45 minutes'],
                'correct_answer': 1,
                'explanation': 'A standard Pomodoro work session is 25 minutes long.'
            }
        ]
        
        return jsonify({
            'quiz': {
                'id': 'daily_' + datetime.utcnow().strftime('%Y%m%d'),
                'title': 'Daily Productivity Quiz',
                'questions': quiz_questions,
                'time_limit': 300  # 5 minutes
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get daily quiz', 'details': str(e)}), 500