from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta
from models import Timer, Reward

hook_bp = Blueprint('hook', __name__)

@hook_bp.route('/timers/active', methods=['GET'])
@jwt_required()
def get_active_timer():
    try:
        current_user_id = get_jwt_identity()
        
        # Get active timer
        timer_data = current_app.mongo.db.active_timers.find_one({'user_id': ObjectId(current_user_id)})
        
        if not timer_data:
            return jsonify({'timer': None}), 200
        
        timer = Timer(timer_data)
        
        return jsonify({'timer': timer.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get active timer', 'details': str(e)}), 500

@hook_bp.route('/timers/start', methods=['POST'])
@jwt_required()
def start_timer():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('task_name') or not data.get('duration'):
            return jsonify({'error': 'Task name and duration are required'}), 400
        
        # Check if user already has an active timer
        existing_timer = current_app.mongo.db.active_timers.find_one({'user_id': ObjectId(current_user_id)})
        
        if existing_timer:
            return jsonify({'error': 'You already have an active timer. Please complete or cancel it first.'}), 409
        
        # Create new timer
        timer_data = {
            'user_id': ObjectId(current_user_id),
            'task_name': data['task_name'],
            'duration': int(data['duration']),  # in minutes
            'category': data.get('category', 'general'),
            'timer_type': data.get('timer_type', 'work'),  # work or break
            'status': 'active',
            'started_at': datetime.utcnow(),
            'paused_at': None,
            'completed_at': None,
            'total_paused_time': 0,
            'mood_rating': None,
            'notes': ''
        }
        
        result = current_app.mongo.db.active_timers.insert_one(timer_data)
        timer_data['_id'] = result.inserted_id
        
        timer = Timer(timer_data)
        
        return jsonify({
            'message': 'Timer started successfully',
            'timer': timer.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to start timer', 'details': str(e)}), 500

@hook_bp.route('/timers/pause', methods=['POST'])
@jwt_required()
def pause_timer():
    try:
        current_user_id = get_jwt_identity()
        
        # Get active timer
        timer_data = current_app.mongo.db.active_timers.find_one({'user_id': ObjectId(current_user_id)})
        
        if not timer_data:
            return jsonify({'error': 'No active timer found'}), 404
        
        current_time = datetime.utcnow()
        
        if timer_data['status'] == 'active':
            # Pause the timer
            current_app.mongo.db.active_timers.update_one(
                {'_id': timer_data['_id']},
                {
                    '$set': {
                        'status': 'paused',
                        'paused_at': current_time
                    }
                }
            )
            message = 'Timer paused'
        
        elif timer_data['status'] == 'paused':
            # Resume the timer
            paused_duration = (current_time - timer_data['paused_at']).total_seconds()
            
            current_app.mongo.db.active_timers.update_one(
                {'_id': timer_data['_id']},
                {
                    '$set': {
                        'status': 'active',
                        'paused_at': None
                    },
                    '$inc': {
                        'total_paused_time': paused_duration
                    }
                }
            )
            message = 'Timer resumed'
        
        else:
            return jsonify({'error': 'Timer cannot be paused/resumed in current state'}), 400
        
        # Get updated timer
        updated_timer_data = current_app.mongo.db.active_timers.find_one({'_id': timer_data['_id']})
        timer = Timer(updated_timer_data)
        
        return jsonify({
            'message': message,
            'timer': timer.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to pause/resume timer', 'details': str(e)}), 500

@hook_bp.route('/timers/complete', methods=['POST'])
@jwt_required()
def complete_timer():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get active timer
        timer_data = current_app.mongo.db.active_timers.find_one({'user_id': ObjectId(current_user_id)})
        
        if not timer_data:
            return jsonify({'error': 'No active timer found'}), 404
        
        current_time = datetime.utcnow()
        
        # Calculate actual duration
        if timer_data['status'] == 'paused':
            actual_duration = (timer_data['paused_at'] - timer_data['started_at']).total_seconds()
        else:
            actual_duration = (current_time - timer_data['started_at']).total_seconds()
        
        actual_duration -= timer_data.get('total_paused_time', 0)
        actual_duration_minutes = max(1, int(actual_duration / 60))  # At least 1 minute
        
        # Update timer as completed
        update_data = {
            'status': 'completed',
            'completed_at': current_time,
            'mood_rating': data.get('mood_rating'),
            'notes': data.get('notes', '')
        }
        
        current_app.mongo.db.active_timers.update_one(
            {'_id': timer_data['_id']},
            {'$set': update_data}
        )
        
        # Move to completed tasks
        completed_task_data = {
            'user_id': ObjectId(current_user_id),
            'task_name': timer_data['task_name'],
            'planned_duration': timer_data['duration'],
            'actual_duration': actual_duration_minutes,
            'category': timer_data['category'],
            'timer_type': timer_data['timer_type'],
            'mood_rating': data.get('mood_rating'),
            'notes': data.get('notes', ''),
            'completed_at': current_time,
            'started_at': timer_data['started_at']
        }
        
        current_app.mongo.db.completed_tasks.insert_one(completed_task_data)
        
        # Remove from active timers
        current_app.mongo.db.active_timers.delete_one({'_id': timer_data['_id']})
        
        # Award points (1 point per 5 minutes of focus time)
        points_earned = max(1, actual_duration_minutes // 5)
        
        # Bonus points for good mood rating
        if data.get('mood_rating') and data['mood_rating'] >= 4:
            points_earned += 2
        
        # Award points
        reward_data = {
            'user_id': ObjectId(current_user_id),
            'points': points_earned,
            'source': 'hook',
            'description': f'Completed {timer_data["task_name"]} ({actual_duration_minutes} min)',
            'earned_at': current_time,
            'metadata': {
                'task_name': timer_data['task_name'],
                'duration': actual_duration_minutes,
                'category': timer_data['category']
            }
        }
        
        current_app.mongo.db.rewards.insert_one(reward_data)
        current_app.mongo.db.users.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$inc': {'points': points_earned}}
        )
        
        return jsonify({
            'message': 'Timer completed successfully',
            'points_earned': points_earned,
            'actual_duration': actual_duration_minutes
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to complete timer', 'details': str(e)}), 500

@hook_bp.route('/timers/cancel', methods=['POST'])
@jwt_required()
def cancel_timer():
    try:
        current_user_id = get_jwt_identity()
        
        # Get active timer
        timer_data = current_app.mongo.db.active_timers.find_one({'user_id': ObjectId(current_user_id)})
        
        if not timer_data:
            return jsonify({'error': 'No active timer found'}), 404
        
        # Remove active timer
        current_app.mongo.db.active_timers.delete_one({'_id': timer_data['_id']})
        
        return jsonify({'message': 'Timer cancelled successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to cancel timer', 'details': str(e)}), 500

@hook_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        category = request.args.get('category')
        days = int(request.args.get('days', 30))
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # Build query
        query = {'user_id': ObjectId(current_user_id)}
        
        if category:
            query['category'] = category
        
        if days > 0:
            start_date = datetime.utcnow() - timedelta(days=days)
            query['completed_at'] = {'$gte': start_date}
        
        # Get tasks with pagination
        skip = (page - 1) * limit
        tasks_cursor = current_app.mongo.db.completed_tasks.find(query).sort('completed_at', -1).skip(skip).limit(limit)
        tasks = list(tasks_cursor)
        
        # Convert ObjectId to string for JSON serialization
        for task in tasks:
            task['_id'] = str(task['_id'])
            task['user_id'] = str(task['user_id'])
            if isinstance(task.get('completed_at'), datetime):
                task['completed_at'] = task['completed_at'].isoformat()
            if isinstance(task.get('started_at'), datetime):
                task['started_at'] = task['started_at'].isoformat()
        
        # Get total count
        total_count = current_app.mongo.db.completed_tasks.count_documents(query)
        
        return jsonify({
            'tasks': tasks,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get tasks', 'details': str(e)}), 500

@hook_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    try:
        current_user_id = get_jwt_identity()
        
        # Get date range
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get completed tasks in date range
        tasks = list(current_app.mongo.db.completed_tasks.find({
            'user_id': ObjectId(current_user_id),
            'completed_at': {'$gte': start_date}
        }))
        
        # Calculate statistics
        total_tasks = len(tasks)
        total_time = sum(task.get('actual_duration', 0) for task in tasks)
        avg_session_length = total_time / max(1, total_tasks)
        
        # Calculate productivity streak
        productivity_streak = 0
        current_date = datetime.utcnow().date()
        
        while True:
            day_tasks = current_app.mongo.db.completed_tasks.count_documents({
                'user_id': ObjectId(current_user_id),
                'completed_at': {
                    '$gte': datetime.combine(current_date, datetime.min.time()),
                    '$lt': datetime.combine(current_date + timedelta(days=1), datetime.min.time())
                }
            })
            
            if day_tasks > 0:
                productivity_streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        # Category breakdown
        category_stats = {}
        for task in tasks:
            category = task.get('category', 'general')
            if category not in category_stats:
                category_stats[category] = {'count': 0, 'time': 0}
            category_stats[category]['count'] += 1
            category_stats[category]['time'] += task.get('actual_duration', 0)
        
        # Daily productivity (last 7 days)
        daily_productivity = []
        for i in range(7):
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
                'tasks': len(day_tasks),
                'time': sum(task.get('actual_duration', 0) for task in day_tasks)
            })
        
        daily_productivity.reverse()  # Show oldest to newest
        
        return jsonify({
            'total_tasks': total_tasks,
            'total_time': total_time,
            'avg_session_length': avg_session_length,
            'productivity_streak': productivity_streak,
            'category_stats': category_stats,
            'daily_productivity': daily_productivity,
            'recent_tasks': tasks[-10:] if tasks else []
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get analytics', 'details': str(e)}), 500

@hook_bp.route('/presets', methods=['GET'])
@jwt_required()
def get_presets():
    try:
        current_user_id = get_jwt_identity()
        
        # Get user preferences
        user_data = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Default presets
        default_presets = [
            {'name': 'Pomodoro', 'duration': 25, 'type': 'work', 'category': 'general', 'color': 'red'},
            {'name': 'Short Break', 'duration': 5, 'type': 'break', 'category': 'break', 'color': 'orange'},
            {'name': 'Long Break', 'duration': 15, 'type': 'break', 'category': 'break', 'color': 'green'},
            {'name': 'Deep Work', 'duration': 90, 'type': 'work', 'category': 'work', 'color': 'blue'},
            {'name': 'Quick Task', 'duration': 10, 'type': 'work', 'category': 'general', 'color': 'purple'}
        ]
        
        # User custom presets
        custom_presets = user_data.get('preferences', {}).get('timer_presets', [])
        
        return jsonify({
            'default_presets': default_presets,
            'custom_presets': custom_presets
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get presets', 'details': str(e)}), 500

@hook_bp.route('/presets', methods=['POST'])
@jwt_required()
def save_preset():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'duration', 'type', 'category']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create preset
        preset = {
            'name': data['name'],
            'duration': int(data['duration']),
            'type': data['type'],
            'category': data['category'],
            'color': data.get('color', 'blue')
        }
        
        # Add to user preferences
        current_app.mongo.db.users.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$push': {'preferences.timer_presets': preset}}
        )
        
        return jsonify({
            'message': 'Preset saved successfully',
            'preset': preset
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to save preset', 'details': str(e)}), 500