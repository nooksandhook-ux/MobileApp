#!/usr/bin/env python3
"""
Database Initialization Script
Creates initial badges, sample data, and indexes for the Nhooks backend
"""

from app import create_app
from datetime import datetime
from bson import ObjectId

def init_badges(mongo):
    """Initialize badge collection with predefined badges"""
    print("Initializing badges...")
    
    badges = [
        # Reading Badges
        {
            'name': 'First Book',
            'description': 'Add your first book to the library',
            'icon': '📖',
            'category': 'reading',
            'requirements': {'books_added': 1},
            'rarity': 'common'
        },
        {
            'name': 'Bookworm',
            'description': 'Add 10 books to your library',
            'icon': '🐛',
            'category': 'reading',
            'requirements': {'books_added': 10},
            'rarity': 'common'
        },
        {
            'name': 'Book Collector',
            'description': 'Add 25 books to your library',
            'icon': '📚',
            'category': 'reading',
            'requirements': {'books_added': 25},
            'rarity': 'rare'
        },
        {
            'name': 'Library Master',
            'description': 'Add 50 books to your library',
            'icon': '🏛️',
            'category': 'reading',
            'requirements': {'books_added': 50},
            'rarity': 'epic'
        },
        
        # Completion Badges
        {
            'name': 'First Finish',
            'description': 'Finish your first book',
            'icon': '✅',
            'category': 'completion',
            'requirements': {'books_finished': 1},
            'rarity': 'common'
        },
        {
            'name': 'Dedicated Reader',
            'description': 'Finish 5 books',
            'icon': '🎓',
            'category': 'completion',
            'requirements': {'books_finished': 5},
            'rarity': 'rare'
        },
        {
            'name': 'Voracious Reader',
            'description': 'Finish 25 books',
            'icon': '🦈',
            'category': 'completion',
            'requirements': {'books_finished': 25},
            'rarity': 'epic'
        },
        {
            'name': 'Reading Legend',
            'description': 'Finish 100 books',
            'icon': '👑',
            'category': 'completion',
            'requirements': {'books_finished': 100},
            'rarity': 'legendary'
        },
        
        # Productivity Badges
        {
            'name': 'First Task',
            'description': 'Complete your first focus session',
            'icon': '⏰',
            'category': 'productivity',
            'requirements': {'tasks_completed': 1},
            'rarity': 'common'
        },
        {
            'name': 'Task Master',
            'description': 'Complete 50 focus sessions',
            'icon': '💪',
            'category': 'productivity',
            'requirements': {'tasks_completed': 50},
            'rarity': 'rare'
        },
        {
            'name': 'Focus Master',
            'description': 'Complete 100 focus sessions',
            'icon': '🧠',
            'category': 'productivity',
            'requirements': {'tasks_completed': 100},
            'rarity': 'epic'
        },
        {
            'name': 'Productivity Legend',
            'description': 'Complete 500 focus sessions',
            'icon': '🏆',
            'category': 'productivity',
            'requirements': {'tasks_completed': 500},
            'rarity': 'legendary'
        },
        
        # Point Badges
        {
            'name': 'Getting Started',
            'description': 'Earn your first 100 points',
            'icon': '🎯',
            'category': 'points',
            'requirements': {'points': 100},
            'rarity': 'common'
        },
        {
            'name': 'Point Collector',
            'description': 'Earn 500 points',
            'icon': '💎',
            'category': 'points',
            'requirements': {'points': 500},
            'rarity': 'rare'
        },
        {
            'name': 'Point Master',
            'description': 'Earn 1,000 points',
            'icon': '👑',
            'category': 'points',
            'requirements': {'points': 1000},
            'rarity': 'epic'
        },
        {
            'name': 'Point Legend',
            'description': 'Earn 5,000 points',
            'icon': '🏆',
            'category': 'points',
            'requirements': {'points': 5000},
            'rarity': 'legendary'
        },
        
        # Streak Badges
        {
            'name': 'Reading Streak',
            'description': 'Read for 7 consecutive days',
            'icon': '🔥',
            'category': 'streak',
            'requirements': {'reading_streak': 7},
            'rarity': 'rare'
        },
        {
            'name': 'Reading Marathon',
            'description': 'Read for 30 consecutive days',
            'icon': '🔥🔥',
            'category': 'streak',
            'requirements': {'reading_streak': 30},
            'rarity': 'epic'
        },
        {
            'name': 'Productivity Streak',
            'description': 'Complete tasks for 7 consecutive days',
            'icon': '⚡',
            'category': 'streak',
            'requirements': {'productivity_streak': 7},
            'rarity': 'rare'
        },
        {
            'name': 'Productivity Marathon',
            'description': 'Complete tasks for 30 consecutive days',
            'icon': '⚡⚡',
            'category': 'streak',
            'requirements': {'productivity_streak': 30},
            'rarity': 'epic'
        },
        
        # Quote Badges
        {
            'name': 'Quote Collector',
            'description': 'Add 10 quotes',
            'icon': '💬',
            'category': 'quotes',
            'requirements': {'quotes_added': 10},
            'rarity': 'common'
        },
        {
            'name': 'Wisdom Keeper',
            'description': 'Add 50 quotes',
            'icon': '🔮',
            'category': 'quotes',
            'requirements': {'quotes_added': 50},
            'rarity': 'rare'
        },
        {
            'name': 'Quote Master',
            'description': 'Add 100 quotes',
            'icon': '📜',
            'category': 'quotes',
            'requirements': {'quotes_added': 100},
            'rarity': 'epic'
        },
        
        # Social Badges
        {
            'name': 'Social Butterfly',
            'description': 'Join your first club',
            'icon': '🦋',
            'category': 'social',
            'requirements': {'clubs_joined': 1},
            'rarity': 'common'
        },
        {
            'name': 'Club Leader',
            'description': 'Create your first club',
            'icon': '👥',
            'category': 'social',
            'requirements': {'clubs_created': 1},
            'rarity': 'rare'
        }
    ]
    
    # Clear existing badges
    mongo.db.badges.delete_many({})
    
    # Insert badges
    result = mongo.db.badges.insert_many(badges)
    print(f"✓ Created {len(result.inserted_ids)} badges")

def create_indexes(mongo):
    """Create database indexes for better performance"""
    print("\nCreating database indexes...")
    
    # Users indexes
    mongo.db.users.create_index('email', unique=True)
    mongo.db.users.create_index('username', unique=True)
    mongo.db.users.create_index('points')
    mongo.db.users.create_index('created_at')
    print("✓ Users indexes created")
    
    # Books indexes
    mongo.db.books.create_index([('user_id', 1), ('status', 1)])
    mongo.db.books.create_index([('user_id', 1), ('added_at', -1)])
    mongo.db.books.create_index('genre')
    print("✓ Books indexes created")
    
    # Tasks indexes
    mongo.db.completed_tasks.create_index([('user_id', 1), ('completed_at', -1)])
    mongo.db.completed_tasks.create_index([('user_id', 1), ('category', 1)])
    print("✓ Tasks indexes created")
    
    # Active timers indexes
    mongo.db.active_timers.create_index('user_id', unique=True)
    print("✓ Active timers indexes created")
    
    # Reading sessions indexes
    mongo.db.reading_sessions.create_index([('user_id', 1), ('date', -1)])
    mongo.db.reading_sessions.create_index([('user_id', 1), ('book_id', 1)])
    print("✓ Reading sessions indexes created")
    
    # Rewards indexes
    mongo.db.rewards.create_index([('user_id', 1), ('earned_at', -1)])
    mongo.db.rewards.create_index([('user_id', 1), ('source', 1)])
    print("✓ Rewards indexes created")
    
    # User badges indexes
    mongo.db.user_badges.create_index([('user_id', 1), ('badge_id', 1)], unique=True)
    print("✓ User badges indexes created")
    
    # Clubs indexes
    mongo.db.clubs.create_index('members')
    mongo.db.clubs.create_index('is_private')
    mongo.db.clubs.create_index('created_at')
    print("✓ Clubs indexes created")
    
    # Quote submissions indexes
    mongo.db.quote_submissions.create_index([('user_id', 1), ('status', 1)])
    mongo.db.quote_submissions.create_index('status')
    mongo.db.quote_submissions.create_index('submitted_at')
    print("✓ Quote submissions indexes created")
    
    # Flashcards indexes
    mongo.db.flashcards.create_index([('user_id', 1), ('created_at', -1)])
    print("✓ Flashcards indexes created")

def create_sample_admin(mongo):
    """Create a sample admin user for testing"""
    print("\nCreating sample admin user...")
    
    from werkzeug.security import generate_password_hash
    
    # Check if admin already exists
    existing_admin = mongo.db.users.find_one({'email': 'admin@nhooks.com'})
    
    if existing_admin:
        print("⚠ Admin user already exists")
        return
    
    admin_data = {
        'username': 'admin',
        'email': 'admin@nhooks.com',
        'password_hash': generate_password_hash('admin123'),  # Change this in production!
        'is_admin': True,
        'is_active': True,
        'points': 0,
        'level': 1,
        'profile': {
            'theme': 'dark',
            'avatar_style': 'initials',
            'display_name': 'Admin',
            'bio': 'System Administrator',
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
    
    result = mongo.db.users.insert_one(admin_data)
    print(f"✓ Admin user created with ID: {result.inserted_id}")
    print("  Email: admin@nhooks.com")
    print("  Password: admin123")
    print("  ⚠ IMPORTANT: Change the admin password in production!")

def create_sample_data(mongo):
    """Create sample data for testing (optional)"""
    print("\nCreating sample data...")
    
    from werkzeug.security import generate_password_hash
    
    # Create a test user
    test_user_data = {
        'username': 'testuser',
        'email': 'test@nhooks.com',
        'password_hash': generate_password_hash('test123'),
        'is_admin': False,
        'is_active': True,
        'points': 150,
        'level': 2,
        'profile': {
            'theme': 'light',
            'avatar_style': 'initials',
            'display_name': 'Test User',
            'bio': 'Sample test user',
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
    
    # Check if test user exists
    existing_test_user = mongo.db.users.find_one({'email': 'test@nhooks.com'})
    
    if not existing_test_user:
        result = mongo.db.users.insert_one(test_user_data)
        test_user_id = result.inserted_id
        print(f"✓ Test user created with ID: {test_user_id}")
        print("  Email: test@nhooks.com")
        print("  Password: test123")
        
        # Add sample books for test user
        sample_books = [
            {
                'user_id': test_user_id,
                'title': 'Atomic Habits',
                'authors': ['James Clear'],
                'description': 'An Easy & Proven Way to Build Good Habits & Break Bad Ones',
                'page_count': 320,
                'current_page': 150,
                'status': 'reading',
                'rating': 0,
                'cover_image': '',
                'genre': 'Self-Help',
                'isbn': '9780735211292',
                'added_at': datetime.utcnow(),
                'quotes': [],
                'takeaways': []
            },
            {
                'user_id': test_user_id,
                'title': 'Deep Work',
                'authors': ['Cal Newport'],
                'description': 'Rules for Focused Success in a Distracted World',
                'page_count': 296,
                'current_page': 0,
                'status': 'to_read',
                'rating': 0,
                'cover_image': '',
                'genre': 'Productivity',
                'isbn': '9781455586691',
                'added_at': datetime.utcnow(),
                'quotes': [],
                'takeaways': []
            }
        ]
        
        mongo.db.books.insert_many(sample_books)
        print(f"✓ Added {len(sample_books)} sample books")
    else:
        print("⚠ Test user already exists")

def main():
    """Main initialization function"""
    print("=" * 60)
    print("Nhooks Backend - Database Initialization")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        mongo = app.mongo
        
        try:
            # Test MongoDB connection
            mongo.db.command('ping')
            print("✓ MongoDB connection successful\n")
            
            # Initialize badges
            init_badges(mongo)
            
            # Create indexes
            create_indexes(mongo)
            
            # Create admin user
            create_sample_admin(mongo)
            
            # Ask if user wants sample data
            print("\n" + "=" * 60)
            response = input("Do you want to create sample test data? (y/n): ").lower()
            
            if response == 'y':
                create_sample_data(mongo)
            
            print("\n" + "=" * 60)
            print("✓ Database initialization completed successfully!")
            print("=" * 60)
            print("\nYou can now start the server with: python run.py")
            
        except Exception as e:
            print(f"\n✗ Error during initialization: {str(e)}")
            print("\nPlease check your MongoDB connection and try again.")
            return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
