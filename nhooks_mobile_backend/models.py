from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.is_admin = user_data.get('is_admin', False)
        self.active = user_data.get('is_active', True)
        self.profile = user_data.get('profile', {})
        self.preferences = user_data.get('preferences', {})
        self.points = user_data.get('points', 0)
        self.level = user_data.get('level', 1)
        self.created_at = user_data.get('created_at', datetime.utcnow())

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.active

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'profile': self.profile,
            'preferences': self.preferences,
            'points': self.points,
            'level': self.level,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

class Book:
    def __init__(self, book_data):
        self.id = str(book_data['_id']) if '_id' in book_data else None
        self.user_id = str(book_data['user_id'])
        self.title = book_data['title']
        self.authors = book_data.get('authors', [])
        self.description = book_data.get('description', '')
        self.page_count = book_data.get('page_count', 0)
        self.current_page = book_data.get('current_page', 0)
        self.status = book_data.get('status', 'to_read')  # to_read, reading, finished
        self.rating = book_data.get('rating', 0)
        self.cover_image = book_data.get('cover_image', '')
        self.genre = book_data.get('genre', '')
        self.isbn = book_data.get('isbn', '')
        self.added_at = book_data.get('added_at', datetime.utcnow())
        self.finished_at = book_data.get('finished_at')
        self.quotes = book_data.get('quotes', [])
        self.takeaways = book_data.get('takeaways', [])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'authors': self.authors,
            'description': self.description,
            'page_count': self.page_count,
            'current_page': self.current_page,
            'status': self.status,
            'rating': self.rating,
            'cover_image': self.cover_image,
            'genre': self.genre,
            'isbn': self.isbn,
            'added_at': self.added_at.isoformat() if isinstance(self.added_at, datetime) else self.added_at,
            'finished_at': self.finished_at.isoformat() if isinstance(self.finished_at, datetime) else self.finished_at,
            'quotes': self.quotes,
            'takeaways': self.takeaways,
            'progress_percentage': (self.current_page / max(1, self.page_count)) * 100
        }

class Timer:
    def __init__(self, timer_data):
        self.id = str(timer_data['_id']) if '_id' in timer_data else None
        self.user_id = str(timer_data['user_id'])
        self.task_name = timer_data['task_name']
        self.duration = timer_data['duration']  # in minutes
        self.category = timer_data.get('category', 'general')
        self.timer_type = timer_data.get('timer_type', 'work')  # work, break
        self.status = timer_data.get('status', 'active')  # active, paused, completed, cancelled
        self.started_at = timer_data.get('started_at', datetime.utcnow())
        self.paused_at = timer_data.get('paused_at')
        self.completed_at = timer_data.get('completed_at')
        self.total_paused_time = timer_data.get('total_paused_time', 0)
        self.mood_rating = timer_data.get('mood_rating')
        self.notes = timer_data.get('notes', '')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_name': self.task_name,
            'duration': self.duration,
            'category': self.category,
            'timer_type': self.timer_type,
            'status': self.status,
            'started_at': self.started_at.isoformat() if isinstance(self.started_at, datetime) else self.started_at,
            'paused_at': self.paused_at.isoformat() if isinstance(self.paused_at, datetime) else self.paused_at,
            'completed_at': self.completed_at.isoformat() if isinstance(self.completed_at, datetime) else self.completed_at,
            'total_paused_time': self.total_paused_time,
            'mood_rating': self.mood_rating,
            'notes': self.notes
        }

class Club:
    def __init__(self, club_data):
        self.id = str(club_data['_id']) if '_id' in club_data else None
        self.name = club_data['name']
        self.description = club_data.get('description', '')
        self.topic = club_data.get('topic', '')
        self.creator_id = str(club_data['creator_id'])
        self.members = [str(member_id) for member_id in club_data.get('members', [])]
        self.is_private = club_data.get('is_private', False)
        self.created_at = club_data.get('created_at', datetime.utcnow())
        self.current_book = club_data.get('current_book')
        self.member_count = len(self.members)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'topic': self.topic,
            'creator_id': self.creator_id,
            'members': self.members,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'current_book': self.current_book,
            'member_count': self.member_count
        }

class Reward:
    def __init__(self, reward_data):
        self.id = str(reward_data['_id']) if '_id' in reward_data else None
        self.user_id = str(reward_data['user_id'])
        self.points = reward_data['points']
        self.source = reward_data['source']  # nook, hook, club, quiz, etc.
        self.description = reward_data['description']
        self.earned_at = reward_data.get('earned_at', datetime.utcnow())
        self.metadata = reward_data.get('metadata', {})

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'points': self.points,
            'source': self.source,
            'description': self.description,
            'earned_at': self.earned_at.isoformat() if isinstance(self.earned_at, datetime) else self.earned_at,
            'metadata': self.metadata
        }

class Badge:
    def __init__(self, badge_data):
        self.id = str(badge_data['_id']) if '_id' in badge_data else None
        self.name = badge_data['name']
        self.description = badge_data['description']
        self.icon = badge_data.get('icon', '')
        self.category = badge_data.get('category', 'general')
        self.requirements = badge_data.get('requirements', {})
        self.rarity = badge_data.get('rarity', 'common')  # common, rare, epic, legendary

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'category': self.category,
            'requirements': self.requirements,
            'rarity': self.rarity
        }

class UserBadge:
    def __init__(self, user_badge_data):
        self.id = str(user_badge_data['_id']) if '_id' in user_badge_data else None
        self.user_id = str(user_badge_data['user_id'])
        self.badge_id = str(user_badge_data['badge_id'])
        self.earned_at = user_badge_data.get('earned_at', datetime.utcnow())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'badge_id': self.badge_id,
            'earned_at': self.earned_at.isoformat() if isinstance(self.earned_at, datetime) else self.earned_at
        }

class Quote:
    def __init__(self, quote_data):
        self.id = str(quote_data['_id']) if '_id' in quote_data else None
        self.user_id = str(quote_data['user_id'])
        self.book_id = str(quote_data['book_id'])
        self.text = quote_data['text']
        self.page = quote_data.get('page', '')
        self.context = quote_data.get('context', '')
        self.status = quote_data.get('status', 'pending')  # pending, verified, rejected
        self.reward_amount = quote_data.get('reward_amount', 10)  # Nigerian Naira
        self.submitted_at = quote_data.get('submitted_at', datetime.utcnow())
        self.verified_at = quote_data.get('verified_at')
        self.verified_by = quote_data.get('verified_by')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'text': self.text,
            'page': self.page,
            'context': self.context,
            'status': self.status,
            'reward_amount': self.reward_amount,
            'submitted_at': self.submitted_at.isoformat() if isinstance(self.submitted_at, datetime) else self.submitted_at,
            'verified_at': self.verified_at.isoformat() if isinstance(self.verified_at, datetime) else self.verified_at,
            'verified_by': self.verified_by
        }