from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta
from models import Reward, Badge, UserBadge

rewards_bp = Blueprint('rewards', __name__)

@rewards_bp.route('/history', methods=['GET'])
@jwt_required()
def get_reward_history():
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        source = request.args.get('source')  # nook, hook, club, quiz, system
        days = int(request.args.get('days', 30))
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # Build query
        query = {'user_id': ObjectId(current_user_id)}
        
        if source:
            query['source'] = source
        
        if days > 0:
            start_date = datetime.utcnow() - timedelta(days=days)
            query['earned_at'] = {'$gte': start_date}
        
        # Get rewards with pagination
        skip = (page - 1) * limit
        rewards_cursor = current_app.mongo.db.rewards.find(query).sort('earned_at', -1).skip(skip).limit(limit)
        rewards = []
        
        for reward_data in rewards_cursor:
            reward = Reward(reward_data)
            rewards.append(reward.to_dict())
        
        # Get total count
        total_count = current_app.mongo.db.rewards.count_documents(query)
        
        # Calculate total points
        total_points = sum(reward['points'] for reward in rewards)
        
        return jsonify({
            'rewards': rewards,
            'total_points': total_points,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get reward history', 'details': str(e)}), 500

@rewards_bp.route('/badges', methods=['GET'])
@jwt_required()
def get_user_badges():
    try:
        current_user_id = get_jwt_identity()
        
        # Get user's badges
        user_badges = list(current_app.mongo.db.user_badges.find({'user_id': ObjectId(current_user_id)}))
        
        # Get badge details
        badge_ids = [ObjectId(ub['badge_id']) for ub in user_badges]
        badges = list(current_app.mongo.db.badges.find({'_id': {'$in': badge_ids}}))
        
        # Combine badge info with earned date
        earned_badges = []
        for user_badge in user_badges:
            badge_info = next((b for b in badges if str(b['_id']) == user_badge['badge_id']), None)
            if badge_info:
                badge = Badge(badge_info)
                badge_dict = badge.to_dict()
                badge_dict['earned_at'] = user_badge['earned_at'].isoformat() if isinstance(user_badge['earned_at'], datetime) else user_badge['earned_at']
                earned_badges.append(badge_dict)
        
        # Get available badges (not yet earned)
        available_badges = list(current_app.mongo.db.badges.find({'_id': {'$nin': badge_ids}}))
        available_badges_list = [Badge(badge_data).to_dict() for badge_data in available_badges]
        
        return jsonify({
            'earned_badges': earned_badges,
            'available_badges': available_badges_list,
            'total_earned': len(earned_badges),
            'total_available': len(available_badges_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get badges', 'details': str(e)}), 500

@rewards_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    try:
        # Get query parameters
        category = request.args.get('category', 'points')  # points, reading, productivity
        limit = int(request.args.get('limit', 10))
        
        if category == 'points':
            # Points leaderboard
            users = list(current_app.mongo.db.users.find(
                {'is_active': True},
                {'username': 1, 'points': 1, 'level': 1, 'profile.display_name': 1}
            ).sort('points', -1).limit(limit))
            
            leaderboard = []
            for i, user in enumerate(users):
                leaderboard.append({
                    'rank': i + 1,
                    'username': user['username'],
                    'display_name': user.get('profile', {}).get('display_name', user['username']),
                    'points': user.get('points', 0),
                    'level': user.get('level', 1)
                })
        
        elif category == 'reading':
            # Reading leaderboard (books finished)
            pipeline = [
                {'$match': {'status': 'finished'}},
                {'$group': {'_id': '$user_id', 'books_finished': {'$sum': 1}}},
                {'$sort': {'books_finished': -1}},
                {'$limit': limit}
            ]
            
            reading_stats = list(current_app.mongo.db.books.aggregate(pipeline))
            
            leaderboard = []
            for i, stat in enumerate(reading_stats):
                user = current_app.mongo.db.users.find_one({'_id': stat['_id']})
                if user:
                    leaderboard.append({
                        'rank': i + 1,
                        'username': user['username'],
                        'display_name': user.get('profile', {}).get('display_name', user['username']),
                        'books_finished': stat['books_finished']
                    })
        
        elif category == 'productivity':
            # Productivity leaderboard (tasks completed)
            pipeline = [
                {'$group': {'_id': '$user_id', 'tasks_completed': {'$sum': 1}}},
                {'$sort': {'tasks_completed': -1}},
                {'$limit': limit}
            ]
            
            productivity_stats = list(current_app.mongo.db.completed_tasks.aggregate(pipeline))
            
            leaderboard = []
            for i, stat in enumerate(productivity_stats):
                user = current_app.mongo.db.users.find_one({'_id': stat['_id']})
                if user:
                    leaderboard.append({
                        'rank': i + 1,
                        'username': user['username'],
                        'display_name': user.get('profile', {}).get('display_name', user['username']),
                        'tasks_completed': stat['tasks_completed']
                    })
        
        return jsonify({
            'leaderboard': leaderboard,
            'category': category
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get leaderboard', 'details': str(e)}), 500

@rewards_bp.route('/achievements', methods=['GET'])
@jwt_required()
def get_achievements():
    try:
        current_user_id = get_jwt_identity()
        
        # Get user stats
        user_data = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate current stats
        stats = {
            'points': user_data.get('points', 0),
            'books_added': current_app.mongo.db.books.count_documents({'user_id': ObjectId(current_user_id)}),
            'books_finished': current_app.mongo.db.books.count_documents({
                'user_id': ObjectId(current_user_id),
                'status': 'finished'
            }),
            'tasks_completed': current_app.mongo.db.completed_tasks.count_documents({'user_id': ObjectId(current_user_id)}),
            'quotes_added': current_app.mongo.db.books.aggregate([
                {'$match': {'user_id': ObjectId(current_user_id)}},
                {'$project': {'quote_count': {'$size': '$quotes'}}},
                {'$group': {'_id': None, 'total': {'$sum': '$quote_count'}}}
            ]),
            'reading_streak': calculate_reading_streak(current_user_id),
            'productivity_streak': calculate_productivity_streak(current_user_id)
        }
        
        # Get quote count
        quote_result = list(stats['quotes_added'])
        stats['quotes_added'] = quote_result[0]['total'] if quote_result else 0
        
        # Define achievement thresholds
        achievements = [
            # Point achievements
            {'name': 'Getting Started', 'description': 'Earn your first 100 points', 'category': 'points', 'threshold': 100, 'current': stats['points'], 'icon': '🎯'},
            {'name': 'Point Collector', 'description': 'Earn 500 points', 'category': 'points', 'threshold': 500, 'current': stats['points'], 'icon': '💎'},
            {'name': 'Point Master', 'description': 'Earn 1,000 points', 'category': 'points', 'threshold': 1000, 'current': stats['points'], 'icon': '👑'},
            {'name': 'Point Legend', 'description': 'Earn 5,000 points', 'category': 'points', 'threshold': 5000, 'current': stats['points'], 'icon': '🏆'},
            
            # Reading achievements
            {'name': 'First Book', 'description': 'Add your first book', 'category': 'reading', 'threshold': 1, 'current': stats['books_added'], 'icon': '📖'},
            {'name': 'Bookworm', 'description': 'Add 10 books to your library', 'category': 'reading', 'threshold': 10, 'current': stats['books_added'], 'icon': '🐛'},
            {'name': 'Book Collector', 'description': 'Add 25 books to your library', 'category': 'reading', 'threshold': 25, 'current': stats['books_added'], 'icon': '📚'},
            {'name': 'Library Master', 'description': 'Add 50 books to your library', 'category': 'reading', 'threshold': 50, 'current': stats['books_added'], 'icon': '🏛️'},
            
            # Completion achievements
            {'name': 'First Finish', 'description': 'Finish your first book', 'category': 'completion', 'threshold': 1, 'current': stats['books_finished'], 'icon': '✅'},
            {'name': 'Dedicated Reader', 'description': 'Finish 5 books', 'category': 'completion', 'threshold': 5, 'current': stats['books_finished'], 'icon': '🎓'},
            {'name': 'Voracious Reader', 'description': 'Finish 25 books', 'category': 'completion', 'threshold': 25, 'current': stats['books_finished'], 'icon': '🦈'},
            
            # Productivity achievements
            {'name': 'First Task', 'description': 'Complete your first focus session', 'category': 'productivity', 'threshold': 1, 'current': stats['tasks_completed'], 'icon': '⏰'},
            {'name': 'Task Master', 'description': 'Complete 50 focus sessions', 'category': 'productivity', 'threshold': 50, 'current': stats['tasks_completed'], 'icon': '💪'},
            {'name': 'Focus Master', 'description': 'Complete 100 focus sessions', 'category': 'productivity', 'threshold': 100, 'current': stats['tasks_completed'], 'icon': '🧠'},
            
            # Quote achievements
            {'name': 'Quote Collector', 'description': 'Add 10 quotes', 'category': 'quotes', 'threshold': 10, 'current': stats['quotes_added'], 'icon': '💬'},
            {'name': 'Wisdom Keeper', 'description': 'Add 50 quotes', 'category': 'quotes', 'threshold': 50, 'current': stats['quotes_added'], 'icon': '🔮'},
            
            # Streak achievements
            {'name': 'Reading Streak', 'description': 'Read for 7 consecutive days', 'category': 'streak', 'threshold': 7, 'current': stats['reading_streak'], 'icon': '🔥'},
            {'name': 'Productivity Streak', 'description': 'Complete tasks for 7 consecutive days', 'category': 'streak', 'threshold': 7, 'current': stats['productivity_streak'], 'icon': '⚡'}
        ]
        
        # Calculate progress for each achievement
        for achievement in achievements:
            achievement['completed'] = achievement['current'] >= achievement['threshold']
            achievement['progress'] = min(100, (achievement['current'] / achievement['threshold']) * 100)
        
        # Group by category
        grouped_achievements = {}
        for achievement in achievements:
            category = achievement['category']
            if category not in grouped_achievements:
                grouped_achievements[category] = []
            grouped_achievements[category].append(achievement)
        
        return jsonify({
            'achievements': grouped_achievements,
            'stats': stats,
            'completed_count': len([a for a in achievements if a['completed']]),
            'total_count': len(achievements)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get achievements', 'details': str(e)}), 500

def calculate_reading_streak(user_id):
    """Calculate current reading streak"""
    try:
        streak = 0
        current_date = datetime.utcnow().date()
        
        while True:
            day_sessions = current_app.mongo.db.reading_sessions.count_documents({
                'user_id': ObjectId(user_id),
                'date': {
                    '$gte': datetime.combine(current_date, datetime.min.time()),
                    '$lt': datetime.combine(current_date + timedelta(days=1), datetime.min.time())
                }
            })
            
            if day_sessions > 0:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    except:
        return 0

def calculate_productivity_streak(user_id):
    """Calculate current productivity streak"""
    try:
        streak = 0
        current_date = datetime.utcnow().date()
        
        while True:
            day_tasks = current_app.mongo.db.completed_tasks.count_documents({
                'user_id': ObjectId(user_id),
                'completed_at': {
                    '$gte': datetime.combine(current_date, datetime.min.time()),
                    '$lt': datetime.combine(current_date + timedelta(days=1), datetime.min.time())
                }
            })
            
            if day_tasks > 0:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    except:
        return 0