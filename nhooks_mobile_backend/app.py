from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import blueprints
from blueprints.auth import auth_bp
from blueprints.nook import nook_bp
from blueprints.hook import hook_bp
from blueprints.clubs import clubs_bp
from blueprints.mini_modules import mini_modules_bp
from blueprints.rewards import rewards_bp
from blueprints.dashboard import dashboard_bp
from blueprints.admin import admin_bp
from blueprints.themes import themes_bp
from blueprints.quotes import quotes_bp

# Import models
from models import User


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['MONGO_URI'] = os.environ.get(
        'MONGO_URI', 'mongodb://localhost:27017/hooks_mobile')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    # Initialize extensions
    mongo = PyMongo(app)
    CORS(app)
    jwt = JWTManager(app)

    # Login manager setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        user_data = mongo.db.users.find_one({'_id': user_id})
        if user_data:
            return User(user_data)
        return None

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(nook_bp, url_prefix='/api/nook')
    app.register_blueprint(hook_bp, url_prefix='/api/hook')
    app.register_blueprint(clubs_bp, url_prefix='/api/clubs')
    app.register_blueprint(mini_modules_bp, url_prefix='/api/mini-modules')
    app.register_blueprint(rewards_bp, url_prefix='/api/rewards')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(themes_bp, url_prefix='/api/themes')
    app.register_blueprint(quotes_bp, url_prefix='/api/quotes')

    # Store mongo instance in app
    app.mongo = mongo

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Hooks Mobile API is running'})

    return app


# Create the application instance at module level
app = create_app()


# Keep this block only for local development (optional)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
