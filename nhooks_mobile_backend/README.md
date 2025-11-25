# Nhooks Mobile Backend API

A comprehensive Flask-based REST API for the Nhooks mobile application, featuring reading tracking (Nook), productivity timers (Hook), social clubs, gamification, and more.

## Features

### Core Modules
- **Authentication** - User registration, login, JWT tokens, profile management
- **Nook (Reading)** - Book library, progress tracking, quotes, takeaways, Google Books search
- **Hook (Productivity)** - Pomodoro timers, task tracking, focus sessions, analytics
- **Clubs** - Social reading clubs, book discussions, community features
- **Rewards** - Points system, badges, achievements, leaderboards
- **Mini Modules** - Flashcards, daily quizzes, learning tools
- **Dashboard** - Comprehensive analytics and statistics
- **Themes** - Customizable UI themes
- **Quotes** - Quote submission and verification system with rewards
- **Admin** - User management, quote verification, system statistics

## Tech Stack

- **Framework**: Flask 2.3.3
- **Database**: MongoDB (PyMongo 4.5.0)
- **Authentication**: Flask-JWT-Extended 4.5.3
- **Security**: Werkzeug 2.3.7 (password hashing)
- **CORS**: Flask-CORS 4.0.0

## Installation

### Prerequisites
- Python 3.8+
- MongoDB (local or MongoDB Atlas)
- pip (Python package manager)

### Setup Steps

1. **Clone the repository** (if not already done)
   ```bash
   cd nhooks_mobile_backend
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example environment file
   copy .env.example .env  # Windows
   # or
   cp .env.example .env    # macOS/Linux
   
   # Edit .env and add your configuration
   ```

5. **Set up MongoDB**
   
   **Option A: Local MongoDB**
   - Install MongoDB Community Edition
   - Start MongoDB service
   - Use connection string: `mongodb://localhost:27017/hooks_mobile`
   
   **Option B: MongoDB Atlas (Cloud)**
   - Create a free cluster at https://www.mongodb.com/cloud/atlas
   - Get your connection string
   - Update MONGO_URI in .env file

6. **Run the development server**
   ```bash
   python run.py
   ```
   
   Or using Flask directly:
   ```bash
   python app.py
   ```

7. **Verify the server is running**
   ```bash
   curl http://localhost:5000/api/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "message": "Hooks Mobile API is running"
   }
   ```

## API Endpoints

### Authentication (`/api/auth`)
- `POST /register` - Register new user
- `POST /login` - User login
- `POST /refresh` - Refresh access token
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile
- `PUT /preferences` - Update user preferences
- `POST /change-password` - Change password

### Nook - Reading (`/api/nook`)
- `GET /books` - Get user's books (with filters)
- `GET /books/<id>` - Get book details
- `POST /books` - Add new book
- `PUT /books/<id>` - Update book
- `POST /books/<id>/progress` - Update reading progress
- `POST /books/<id>/quotes` - Add quote to book
- `POST /books/<id>/takeaways` - Add takeaway to book
- `GET /search` - Search Google Books
- `GET /analytics` - Get reading analytics

### Hook - Productivity (`/api/hook`)
- `GET /timers/active` - Get active timer
- `POST /timers/start` - Start new timer
- `POST /timers/pause` - Pause/resume timer
- `POST /timers/complete` - Complete timer
- `POST /timers/cancel` - Cancel timer
- `GET /tasks` - Get completed tasks
- `GET /analytics` - Get productivity analytics
- `GET /presets` - Get timer presets
- `POST /presets` - Save custom preset

### Clubs (`/api/clubs`)
- `GET /` - Get user's clubs and public clubs
- `POST /` - Create new club
- `POST /<id>/join` - Join a club

### Mini Modules (`/api/mini-modules`)
- `GET /flashcards` - Get user's flashcards
- `POST /flashcards` - Create flashcard
- `GET /quiz/daily` - Get daily quiz

### Rewards (`/api/rewards`)
- `GET /history` - Get reward history
- `GET /badges` - Get user badges
- `GET /leaderboard` - Get leaderboard
- `GET /achievements` - Get achievements

### Dashboard (`/api/dashboard`)
- `GET /summary` - Get dashboard summary
- `GET /analytics` - Get detailed analytics

### Themes (`/api/themes`)
- `GET /` - Get available themes
- `POST /apply` - Apply theme

### Quotes (`/api/quotes`)
- `POST /submit` - Submit quote for verification
- `GET /my-submissions` - Get user's quote submissions

### Admin (`/api/admin`)
- `GET /dashboard` - Get admin dashboard
- `GET /users` - Get all users
- `GET /quotes/pending` - Get pending quotes
- `POST /quotes/<id>/verify` - Verify/reject quote

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. After login/registration, you'll receive:
- `access_token` - Short-lived token for API requests (24 hours)
- `refresh_token` - Long-lived token for getting new access tokens (30 days)

### Using the tokens

Include the access token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

### Example with curl
```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier": "user@example.com", "password": "password123"}'

# Use the token
curl -X GET http://localhost:5000/api/nook/books \
  -H "Authorization: Bearer <your_access_token>"
```

## Database Collections

The API uses the following MongoDB collections:

- `users` - User accounts and profiles
- `books` - User's book library
- `reading_sessions` - Reading activity tracking
- `active_timers` - Currently running timers
- `completed_tasks` - Completed focus sessions
- `clubs` - Reading clubs
- `rewards` - Points and rewards history
- `badges` - Available badges
- `user_badges` - User's earned badges
- `flashcards` - User's flashcards
- `quote_submissions` - Quote submissions for verification

## Gamification System

### Points
Users earn points for various activities:
- Registration: 10 points
- Adding a book: 5 points
- Reading pages: 1 point per page (max 20 per session)
- Adding quotes: 3 points
- Adding takeaways: 2 points
- Completing book: 50 points
- Completing focus session: 1 point per 5 minutes
- Good mood rating: +2 bonus points

### Achievements
The system tracks various achievements:
- Point milestones (100, 500, 1000, 5000)
- Reading milestones (1, 10, 25, 50 books)
- Completion milestones (1, 5, 25 books finished)
- Productivity milestones (1, 50, 100 tasks)
- Quote collection (10, 50 quotes)
- Streaks (7-day reading/productivity streaks)

### Leaderboards
Three leaderboard categories:
- Points - Total points earned
- Reading - Books finished
- Productivity - Tasks completed

## Development

### Project Structure
```
nhooks_mobile_backend/
├── app.py                 # Main Flask application
├── models.py              # Data models
├── run.py                 # Development server runner
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── blueprints/           # API route modules
│   ├── __init__.py
│   ├── auth.py           # Authentication routes
│   ├── nook.py           # Reading/books routes
│   ├── hook.py           # Timer/productivity routes
│   ├── clubs.py          # Social clubs routes
│   ├── mini_modules.py   # Flashcards/quiz routes
│   ├── rewards.py        # Gamification routes
│   ├── dashboard.py      # Analytics routes
│   ├── admin.py          # Admin routes
│   ├── themes.py         # Theme routes
│   └── quotes.py         # Quote submission routes
└── README.md             # This file
```

### Adding New Endpoints

1. Create or modify a blueprint in `blueprints/`
2. Register the blueprint in `app.py`
3. Add appropriate models in `models.py` if needed
4. Test the endpoint

### Running Tests
```bash
# TODO: Add test suite
pytest
```

## Deployment

### Production Checklist

1. **Environment Variables**
   - Set strong SECRET_KEY and JWT_SECRET_KEY
   - Use production MongoDB URI
   - Set FLASK_ENV=production
   - Set FLASK_DEBUG=False

2. **Security**
   - Enable HTTPS
   - Configure CORS properly
   - Set up rate limiting
   - Enable MongoDB authentication
   - Use environment-specific secrets

3. **Database**
   - Set up MongoDB indexes for performance
   - Configure backups
   - Monitor database size

4. **Server**
   - Use production WSGI server (Gunicorn)
   - Set up reverse proxy (Nginx)
   - Configure logging
   - Set up monitoring

### Deploy with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Deploy to Heroku
```bash
# Already configured with Procfile
heroku create your-app-name
heroku addons:create mongolab:sandbox
git push heroku main
```

### Deploy to Railway/Render
- Connect your GitHub repository
- Set environment variables
- Deploy automatically

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| SECRET_KEY | Flask secret key | dev-secret-key | Yes |
| JWT_SECRET_KEY | JWT signing key | jwt-secret-key | Yes |
| MONGO_URI | MongoDB connection string | mongodb://localhost:27017/hooks_mobile | Yes |
| GOOGLE_BOOKS_API_KEY | Google Books API key | None | No |
| FLASK_ENV | Environment (development/production) | development | No |
| FLASK_DEBUG | Debug mode | True | No |
| HOST | Server host | 0.0.0.0 | No |
| PORT | Server port | 5000 | No |

## Troubleshooting

### MongoDB Connection Issues
```
Error: ServerSelectionTimeoutError
```
**Solution**: 
- Check if MongoDB is running
- Verify MONGO_URI in .env
- Check firewall settings
- For Atlas: Whitelist your IP address

### Import Errors
```
ModuleNotFoundError: No module named 'flask'
```
**Solution**:
```bash
pip install -r requirements.txt
```

### JWT Token Errors
```
Error: Token has expired
```
**Solution**: Use the refresh token endpoint to get a new access token

### CORS Errors
```
Access-Control-Allow-Origin error
```
**Solution**: Add your frontend URL to CORS_ORIGINS in .env

## API Response Format

### Success Response
```json
{
  "message": "Operation successful",
  "data": { ... }
}
```

### Error Response
```json
{
  "error": "Error message",
  "details": "Detailed error information"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is proprietary software for the Nhooks mobile application.

## Support

For issues or questions:
- Create an issue in the repository
- Contact the development team

## Changelog

### Version 1.0.0 (Current)
- Initial release
- Complete API implementation
- All core features functional
- MongoDB integration
- JWT authentication
- Gamification system
- Admin panel
- Quote verification system

---

**Built with ❤️ for the Nhooks community**
