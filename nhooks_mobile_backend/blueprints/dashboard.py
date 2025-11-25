from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    try:
        current_user_id = get_jwt_identity()
        
        # Get user data
        user_data = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate date ranges
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        this_week = today - timedelta(days=today.weekday())
        this_month = today.replace(day=1)
        
        # Reading statistics
        reading_stats = {
            'total_books': current_app.mongo.db.books.count_documents({'user_id': ObjectId(current_user_id)}),
            'finished_books': current_app.mongo.db.books.count_documents({
                'user_id': ObjectId(current_user_id),
                'status': 'finished'
            }),
            'currently_reading': current_app.mongo.db.books.count_documents({
                'user_id': ObjectId(current_user_id),
                'status': 'reading'
            }),
            'to_read': current_app.mongo.db.books.count_documents({
                'user_id': ObjectId(current_user_id),
                'status': 'to_read'
            })
        }
        
        # Reading sessions today
        today_reading_sessions = list(current_app.mongo.db.reading_sessions.find({
            'user_id': ObjectId(current_user_id),
            'date': {'$gte': today}
        }))
        
        reading_stats['pages_read_today'] = sum(session.get('pages_read', 0) for session in today_reading_sessions)
        reading_stats['reading_time_today'] = sum(session.get('duration_minutes', 0) for session in today_reading_sessions)
        
        # Productivity statistics
        productivity_stats = {
            'total_tasks': current_app.mongo.db.completed_tasks.count_documents({'user_id': ObjectId(current_user_id)}),
            'tasks_today': current_app.mongo.db.completed_tasks.count_documents({
                'user_id': ObjectId(current_user_id),
                'completed_at': {'$gte': today}
            }),
            'tasks_this_week': current_app.mongo.db.completed_tasks.count_documents({
                'user_id': ObjectId(current_user_id),
                'completed_at': {'$gte': this_week}
            }),
            'tasks_this_month': current_app.mongo.db.completed_tasks.count_documents({
                'user_id': ObjectId(current_user_id),
                'completed_at': {'$gte': this_month}
            })
        }
        
        # Focus time today
        today_tasks = list(current_app.mongo.db.completed_tasks.find({
            'user_id': ObjectId(current_user_id),
            'completed_at': {'$gte': today}
        }))
        
        productivity_stats['focus_time_today'] = sum(task.get('actual_duration', 0) for task in today_tasks)
        
        # Rewards and gamification
        rewards_stats = {
            'total_points': user_data.get('points', 0),
            'level': user_data.get('level', 1),
            'total_badges': current_app.mongo.db.user_badges.count_documents({'user_id': ObjectId(current_user_id)})
        }
        
        # Recent rewards (last 5)
        recent_rewards = list(current_app.mongo.db.rewards.find({
            'user_id': ObjectId(current_user_id)
        }).sort('earned_at', -1).limit(5))
        
        for reward in recent_rewards:
            reward['_id'] = str(reward['_id'])
            reward['user_id'] = str(reward['user_id'])
            if isinstance(reward.get('earned_at'), datetime):
                reward['earned_at'] = reward['earned_at'].isoformat()
        
        # Calculate streaks
        reading_streak = calculate_reading_streak(current_user_id)
        productivity_streak = calculate_productivity_streak(current_user_id)
        
        # Active timer
        active_timer = current_app.mongo.db.active_timers.find_one({'user_id': ObjectId(current_user_id)})
        if active_timer:
            active_timer['_id'] = str(active_timer['_id'])
            active_timer['user_id'] = str(active_timer['user_id'])
            if isinstance(active_timer.get('started_at'), datetime):
                active_timer['started_at'] = active_timer['started_at'].isoformat()
            if isinstance(active_timer.get('paused_at'), datetime):
                active_timer['paused_at'] = active_timer['paused_at'].isoformat()
        
        # Recent activity
        recent_books = list(current_app.mongo.db.books.find({
            'user_id': ObjectId(current_user_id)
        }).sort('added_at', -1).limit(3))
        
        for book in recent_books:
            book['_id'] = str(book['_id'])
            book['user_id'] = str(book['user_id'])
            if isinstance(book.get('added_at'), datetime):
                book['added_at'] = book['added_at'].isoformat()
        
        return jsonify({
            'user': {
                'username': user_data['username'],
                'points': user_data.get('points', 0),
                'level': user_data.get('level', 1),
                'theme': user_data.get('profile', {}).get('theme', 'light')
            },
            'reading_stats': reading_stats,
            'productivity_stats': productivity_stats,
            'rewards_stats': rewards_stats,
            'streaks': {
                'reading_streak': reading_streak,
                'productivity_streak': productivity_streak
            },
            'recent_rewards': recent_rewards,
            'active_timer': active_timer,
            'recent_books': recent_books
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get dashboard summary', 'details': str(e)}), 500

@dashboard_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_detailed_analytics():
    try:
        current_user_id = get_jwt_identity()
        days = int(request.args.get('days', 30))
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily reading progress
        daily_reading = []
        for i in range(days):
            date = datetime.utcnow().date() - timedelta(days=i)
            day_sessions = list(current_app.mongo.db.reading_sessions.find({
                'user_id': ObjectId(current_user_id),
                'date': {
                    '$gte': datetime.combine(date, datetime.min.time()),
                    '$lt': datetime.combine(date + timedelta(days=1), datetime.min.time())
                }
            }))
            
            daily_reading.append({
                'date': date.isoformat(),
                'pages_read': sum(session.get('pages_read', 0) for session in day_sessions),
                'reading_time': sum(session.get('duration_minutes', 0) for session in day_sessions),
                'sessions': len(day_sessions)
            })
        
        daily_reading.reverse()
        
        # Daily productivity
        daily_productivity = []
        for i in range(days):
            date = datetime.utcnow().date() - timedelta(days=i)
            day_tasks = list(current_app.mongo.db.completed_tasks.find({
                'user_id': ObjectId(current_user_id),
                'completed_at': {
                    '$gte': datetime.combine(date, datetime.min.time()),
                    '$lt': datetime.combine(date + timedelta(days=1), datetime.min.time())
                }
            }))
            
            daily_productivity.append({
                'date': date.isoformat(),
                'tasks_completed': len(day_tasks),
                'focus_time': sum(task.get('actual_duration', 0) for task in day_tasks),
                'avg_mood': sum(task.get('mood_rating', 0) for task in day_tasks if task.get('mood_rating')) / max(1, len([t for t in day_tasks if t.get('mood_rating')]))
            })
        
        daily_productivity.reverse()
        
        # Category breakdown for tasks
        task_categories = list(current_app.mongo.db.completed_tasks.aggregate([
            {'$match': {'user_id': ObjectId(current_user_id), 'completed_at': {'$gte': start_date}}},
            {'$group': {
                '_id': '$category',
                'count': {'$sum': 1},
                'total_time': {'$sum': '$actual_duration'}
            }},
            {'$sort': {'count': -1}}
        ]))
        
        # Genre breakdown for books
        book_genres = list(current_app.mongo.db.books.aggregate([
            {'$match': {'user_id': ObjectId(current_user_id)}},
            {'$group': {
                '_id': '$genre',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]))
        
        # Points earned over time
        daily_points = []
        for i in range(days):
            date = datetime.utcnow().date() - timedelta(days=i)
            day_rewards = list(current_app.mongo.db.rewards.find({
                'user_id': ObjectId(current_user_id),
                'earned_at': {
                    '$gte': datetime.combine(date, datetime.min.time()),
                    '$lt': datetime.combine(date + timedelta(days=1), datetime.min.time())
                }
            }))
            
            daily_points.append({
                'date': date.isoformat(),
                'points': sum(reward.get('points', 0) for reward in day_rewards),
                'sources': {}
            })
            
            # Group by source
            for reward in day_rewards:
                source = reward.get('source', 'unknown')
                if source not in daily_points[-1]['sources']:
                    daily_points[-1]['sources'][source] = 0
                daily_points[-1]['sources'][source] += reward.get('points', 0)
        
        daily_points.reverse()
        
        return jsonify({
            'daily_reading': daily_reading,
            'daily_productivity': daily_productivity,
            'daily_points': daily_points,
            'task_categories': task_categories,
            'book_genres': book_genres
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get detailed analytics', 'details': str(e)}), 500

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