# Nhooks API Testing Guide

Complete guide for testing all API endpoints with example requests and responses.

## Base URL
```
http://localhost:5000/api
```

## Authentication Flow

### 1. Register a New User

**Endpoint**: `POST /auth/register`

**Request**:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

**Response** (201 Created):
```json
{
  "message": "Registration successful",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "testuser",
    "email": "test@example.com",
    "points": 10,
    "level": 1,
    "is_admin": false,
    "profile": {
      "theme": "light",
      "avatar_style": "initials",
      "display_name": "testuser"
    }
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Login

**Endpoint**: `POST /auth/login`

**Request**:
```json
{
  "identifier": "test@example.com",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "message": "Login successful",
  "user": { ... },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 3. Refresh Token

**Endpoint**: `POST /auth/refresh`

**Headers**:
```
Authorization: Bearer <refresh_token>
```

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": { ... }
}
```

## Profile Management

### Get Profile

**Endpoint**: `GET /auth/profile`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "testuser",
    "email": "test@example.com",
    "points": 10,
    "level": 1
  },
  "stats": {
    "total_books": 5,
    "finished_books": 2,
    "total_tasks": 15,
    "total_badges": 3
  }
}
```

### Update Profile

**Endpoint**: `PUT /auth/profile`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "display_name": "John Doe",
  "bio": "Avid reader and productivity enthusiast",
  "theme": "dark"
}
```

### Update Preferences

**Endpoint**: `PUT /auth/preferences`

**Request**:
```json
{
  "notifications": true,
  "timer_sound": true,
  "default_timer_duration": 25,
  "animations": true
}
```

## Nook (Reading) Endpoints

### Get Books

**Endpoint**: `GET /nook/books`

**Query Parameters**:
- `status` - Filter by status (to_read, reading, finished)
- `genre` - Filter by genre
- `sort_by` - Sort field (added_at, title, progress)
- `order` - Sort order (asc, desc)
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20)

**Example**: `GET /nook/books?status=reading&page=1&limit=10`

**Response** (200 OK):
```json
{
  "books": [
    {
      "id": "507f1f77bcf86cd799439011",
      "title": "Atomic Habits",
      "authors": ["James Clear"],
      "description": "An Easy & Proven Way to Build Good Habits & Break Bad Ones",
      "page_count": 320,
      "current_page": 150,
      "status": "reading",
      "rating": 0,
      "cover_image": "https://...",
      "genre": "Self-Help",
      "progress_percentage": 46.875
    }
  ],
  "stats": {
    "total_books": 10,
    "to_read": 5,
    "reading": 3,
    "finished": 2
  },
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 10,
    "pages": 1
  }
}
```

### Add Book

**Endpoint**: `POST /nook/books`

**Request**:
```json
{
  "title": "Atomic Habits",
  "authors": ["James Clear"],
  "description": "An Easy & Proven Way to Build Good Habits & Break Bad Ones",
  "page_count": 320,
  "current_page": 0,
  "status": "to_read",
  "cover_image": "https://...",
  "genre": "Self-Help",
  "isbn": "9780735211292"
}
```

**Response** (201 Created):
```json
{
  "message": "Book added successfully",
  "book": { ... }
}
```

### Update Book

**Endpoint**: `PUT /nook/books/<book_id>`

**Request**:
```json
{
  "status": "reading",
  "rating": 5
}
```

### Update Reading Progress

**Endpoint**: `POST /nook/books/<book_id>/progress`

**Request**:
```json
{
  "current_page": 150,
  "duration_minutes": 30,
  "session_notes": "Great chapter on habit stacking"
}
```

**Response** (200 OK):
```json
{
  "message": "Progress updated successfully",
  "book": { ... },
  "points_earned": 20
}
```

### Add Quote

**Endpoint**: `POST /nook/books/<book_id>/quotes`

**Request**:
```json
{
  "text": "You do not rise to the level of your goals. You fall to the level of your systems.",
  "page": "27",
  "context": "Chapter on systems vs goals"
}
```

### Search Books (Google Books)

**Endpoint**: `GET /nook/search?q=atomic+habits`

**Response** (200 OK):
```json
{
  "books": [
    {
      "google_id": "XfFvDwAAQBAJ",
      "title": "Atomic Habits",
      "authors": ["James Clear"],
      "description": "...",
      "page_count": 320,
      "cover_image": "https://...",
      "genre": "Self-Help",
      "isbn": "9780735211292"
    }
  ],
  "total": 1
}
```

### Get Reading Analytics

**Endpoint**: `GET /nook/analytics?days=30`

**Response** (200 OK):
```json
{
  "total_books": 10,
  "finished_books": 2,
  "total_pages_read": 1500,
  "total_reading_time": 900,
  "reading_streak": 7,
  "average_pages_per_session": 25,
  "books_by_genre": [
    {"_id": "Self-Help", "count": 5},
    {"_id": "Fiction", "count": 3}
  ]
}
```

## Hook (Productivity) Endpoints

### Get Active Timer

**Endpoint**: `GET /hook/timers/active`

**Response** (200 OK):
```json
{
  "timer": {
    "id": "507f1f77bcf86cd799439011",
    "task_name": "Write blog post",
    "duration": 25,
    "category": "work",
    "timer_type": "work",
    "status": "active",
    "started_at": "2024-01-15T10:00:00Z"
  }
}
```

### Start Timer

**Endpoint**: `POST /hook/timers/start`

**Request**:
```json
{
  "task_name": "Write blog post",
  "duration": 25,
  "category": "work",
  "timer_type": "work"
}
```

**Response** (201 Created):
```json
{
  "message": "Timer started successfully",
  "timer": { ... }
}
```

### Pause/Resume Timer

**Endpoint**: `POST /hook/timers/pause`

**Response** (200 OK):
```json
{
  "message": "Timer paused",
  "timer": { ... }
}
```

### Complete Timer

**Endpoint**: `POST /hook/timers/complete`

**Request**:
```json
{
  "mood_rating": 5,
  "notes": "Very productive session"
}
```

**Response** (200 OK):
```json
{
  "message": "Timer completed successfully",
  "points_earned": 7,
  "actual_duration": 25
}
```

### Get Completed Tasks

**Endpoint**: `GET /hook/tasks?category=work&days=30&page=1&limit=20`

**Response** (200 OK):
```json
{
  "tasks": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "task_name": "Write blog post",
      "planned_duration": 25,
      "actual_duration": 25,
      "category": "work",
      "mood_rating": 5,
      "completed_at": "2024-01-15T10:25:00Z"
    }
  ],
  "pagination": { ... }
}
```

### Get Productivity Analytics

**Endpoint**: `GET /hook/analytics?days=30`

**Response** (200 OK):
```json
{
  "total_tasks": 50,
  "total_time": 1250,
  "avg_session_length": 25,
  "productivity_streak": 7,
  "category_stats": {
    "work": {"count": 30, "time": 750},
    "study": {"count": 20, "time": 500}
  },
  "daily_productivity": [
    {
      "date": "2024-01-15",
      "tasks": 3,
      "time": 75
    }
  ]
}
```

### Get Timer Presets

**Endpoint**: `GET /hook/presets`

**Response** (200 OK):
```json
{
  "default_presets": [
    {
      "name": "Pomodoro",
      "duration": 25,
      "type": "work",
      "category": "general",
      "color": "red"
    }
  ],
  "custom_presets": []
}
```

### Save Custom Preset

**Endpoint**: `POST /hook/presets`

**Request**:
```json
{
  "name": "Deep Work",
  "duration": 90,
  "type": "work",
  "category": "work",
  "color": "blue"
}
```

## Clubs Endpoints

### Get Clubs

**Endpoint**: `GET /clubs/`

**Response** (200 OK):
```json
{
  "user_clubs": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "Book Lovers",
      "description": "A club for avid readers",
      "topic": "General Reading",
      "member_count": 15,
      "is_private": false
    }
  ],
  "public_clubs": [ ... ]
}
```

### Create Club

**Endpoint**: `POST /clubs/`

**Request**:
```json
{
  "name": "Sci-Fi Enthusiasts",
  "description": "For lovers of science fiction",
  "topic": "Science Fiction",
  "is_private": false
}
```

### Join Club

**Endpoint**: `POST /clubs/<club_id>/join`

**Response** (200 OK):
```json
{
  "message": "Successfully joined the club"
}
```

## Rewards & Gamification

### Get Reward History

**Endpoint**: `GET /rewards/history?source=nook&days=30&page=1&limit=20`

**Response** (200 OK):
```json
{
  "rewards": [
    {
      "id": "507f1f77bcf86cd799439011",
      "points": 50,
      "source": "nook",
      "description": "Finished reading: Atomic Habits",
      "earned_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total_points": 150,
  "pagination": { ... }
}
```

### Get Badges

**Endpoint**: `GET /rewards/badges`

**Response** (200 OK):
```json
{
  "earned_badges": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "First Book",
      "description": "Add your first book",
      "icon": "📖",
      "category": "reading",
      "rarity": "common",
      "earned_at": "2024-01-10T10:00:00Z"
    }
  ],
  "available_badges": [ ... ],
  "total_earned": 5,
  "total_available": 15
}
```

### Get Leaderboard

**Endpoint**: `GET /rewards/leaderboard?category=points&limit=10`

**Categories**: `points`, `reading`, `productivity`

**Response** (200 OK):
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "username": "topuser",
      "display_name": "Top User",
      "points": 5000,
      "level": 10
    }
  ],
  "category": "points"
}
```

### Get Achievements

**Endpoint**: `GET /rewards/achievements`

**Response** (200 OK):
```json
{
  "achievements": {
    "points": [
      {
        "name": "Getting Started",
        "description": "Earn your first 100 points",
        "threshold": 100,
        "current": 150,
        "completed": true,
        "progress": 100,
        "icon": "🎯"
      }
    ],
    "reading": [ ... ],
    "productivity": [ ... ]
  },
  "stats": {
    "points": 150,
    "books_added": 10,
    "books_finished": 2,
    "tasks_completed": 50
  },
  "completed_count": 5,
  "total_count": 20
}
```

## Dashboard

### Get Dashboard Summary

**Endpoint**: `GET /dashboard/summary`

**Response** (200 OK):
```json
{
  "user": {
    "username": "testuser",
    "points": 150,
    "level": 2,
    "theme": "dark"
  },
  "reading_stats": {
    "total_books": 10,
    "finished_books": 2,
    "currently_reading": 3,
    "to_read": 5,
    "pages_read_today": 25,
    "reading_time_today": 30
  },
  "productivity_stats": {
    "total_tasks": 50,
    "tasks_today": 3,
    "tasks_this_week": 15,
    "tasks_this_month": 50,
    "focus_time_today": 75
  },
  "rewards_stats": {
    "total_points": 150,
    "level": 2,
    "total_badges": 5
  },
  "streaks": {
    "reading_streak": 7,
    "productivity_streak": 5
  },
  "recent_rewards": [ ... ],
  "active_timer": { ... },
  "recent_books": [ ... ]
}
```

### Get Detailed Analytics

**Endpoint**: `GET /dashboard/analytics?days=30`

**Response** (200 OK):
```json
{
  "daily_reading": [
    {
      "date": "2024-01-15",
      "pages_read": 25,
      "reading_time": 30,
      "sessions": 2
    }
  ],
  "daily_productivity": [
    {
      "date": "2024-01-15",
      "tasks_completed": 3,
      "focus_time": 75,
      "avg_mood": 4.5
    }
  ],
  "daily_points": [
    {
      "date": "2024-01-15",
      "points": 30,
      "sources": {
        "nook": 20,
        "hook": 10
      }
    }
  ],
  "task_categories": [ ... ],
  "book_genres": [ ... ]
}
```

## Mini Modules

### Get Flashcards

**Endpoint**: `GET /mini-modules/flashcards`

**Response** (200 OK):
```json
{
  "flashcards": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "front": "What is the Pomodoro Technique?",
      "back": "A time management method using 25-minute work intervals",
      "tags": ["productivity", "time-management"],
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Create Flashcard

**Endpoint**: `POST /mini-modules/flashcards`

**Request**:
```json
{
  "front": "What is the Pomodoro Technique?",
  "back": "A time management method using 25-minute work intervals",
  "tags": ["productivity", "time-management"]
}
```

### Get Daily Quiz

**Endpoint**: `GET /mini-modules/quiz/daily`

**Response** (200 OK):
```json
{
  "quiz": {
    "id": "daily_20240115",
    "title": "Daily Productivity Quiz",
    "questions": [
      {
        "id": 1,
        "question": "What is the main benefit of the Pomodoro Technique?",
        "options": [
          "Improved focus and productivity",
          "Better time management",
          "Reduced stress",
          "All of the above"
        ],
        "correct_answer": 3,
        "explanation": "The Pomodoro Technique helps with focus, time management, and stress reduction."
      }
    ],
    "time_limit": 300
  }
}
```

## Themes

### Get Themes

**Endpoint**: `GET /themes/`

**Response** (200 OK):
```json
{
  "themes": [
    {
      "id": "light",
      "name": "Light",
      "description": "Clean and bright theme for daytime use",
      "primary_color": "#007bff",
      "background_color": "#ffffff",
      "text_color": "#333333",
      "is_premium": false
    },
    {
      "id": "dark",
      "name": "Dark",
      "description": "Easy on the eyes for low-light environments",
      "primary_color": "#bb86fc",
      "background_color": "#121212",
      "text_color": "#ffffff",
      "is_premium": false
    }
  ]
}
```

### Apply Theme

**Endpoint**: `POST /themes/apply`

**Request**:
```json
{
  "theme_id": "dark"
}
```

## Quotes

### Submit Quote

**Endpoint**: `POST /quotes/submit`

**Request**:
```json
{
  "book_id": "507f1f77bcf86cd799439011",
  "text": "You do not rise to the level of your goals. You fall to the level of your systems.",
  "page": "27",
  "context": "Chapter on systems vs goals"
}
```

**Response** (201 Created):
```json
{
  "message": "Quote submitted for verification",
  "quote": {
    "id": "507f1f77bcf86cd799439011",
    "text": "You do not rise to the level of your goals...",
    "status": "pending",
    "reward_amount": 10,
    "submitted_at": "2024-01-15T10:00:00Z"
  }
}
```

### Get My Quote Submissions

**Endpoint**: `GET /quotes/my-submissions?status=pending&page=1&limit=20`

**Response** (200 OK):
```json
{
  "quotes": [
    {
      "id": "507f1f77bcf86cd799439011",
      "text": "You do not rise to the level of your goals...",
      "book_title": "Atomic Habits",
      "status": "pending",
      "reward_amount": 10,
      "submitted_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total_earnings": 50,
  "pagination": { ... }
}
```

## Admin Endpoints

### Get Admin Dashboard

**Endpoint**: `GET /admin/dashboard`

**Headers**:
```
Authorization: Bearer <admin_access_token>
```

**Response** (200 OK):
```json
{
  "stats": {
    "total_users": 1000,
    "active_users": 850,
    "total_books": 5000,
    "total_tasks": 10000,
    "pending_quotes": 25,
    "new_users_week": 50,
    "new_books_week": 200,
    "completed_tasks_week": 500
  },
  "top_users": [ ... ]
}
```

### Get All Users

**Endpoint**: `GET /admin/users?search=john&page=1&limit=20`

**Response** (200 OK):
```json
{
  "users": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "username": "john_doe",
      "email": "john@example.com",
      "points": 150,
      "level": 2,
      "is_active": true,
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

### Get Pending Quotes

**Endpoint**: `GET /admin/quotes/pending`

**Response** (200 OK):
```json
{
  "quotes": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "text": "You do not rise to the level of your goals...",
      "username": "john_doe",
      "book_title": "Atomic Habits",
      "book_authors": ["James Clear"],
      "status": "pending",
      "reward_amount": 10,
      "submitted_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Verify Quote

**Endpoint**: `POST /admin/quotes/<quote_id>/verify`

**Request**:
```json
{
  "action": "approve",
  "reason": "Quote verified in book"
}
```

**Response** (200 OK):
```json
{
  "message": "Quote approved successfully",
  "quote_id": "507f1f77bcf86cd799439011",
  "action": "approve"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
  "error": "Admin privileges required"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 409 Conflict
```json
{
  "error": "Email already registered"
}
```

### 500 Internal Server Error
```json
{
  "error": "Operation failed",
  "details": "Detailed error message"
}
```

## Testing with cURL

### Example: Complete User Flow

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# 2. Save the access_token from response
TOKEN="your_access_token_here"

# 3. Get profile
curl -X GET http://localhost:5000/api/auth/profile \
  -H "Authorization: Bearer $TOKEN"

# 4. Add a book
curl -X POST http://localhost:5000/api/nook/books \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Atomic Habits","authors":["James Clear"],"page_count":320,"status":"to_read"}'

# 5. Start a timer
curl -X POST http://localhost:5000/api/hook/timers/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_name":"Reading","duration":25,"category":"reading"}'

# 6. Get dashboard
curl -X GET http://localhost:5000/api/dashboard/summary \
  -H "Authorization: Bearer $TOKEN"
```

## Testing with Python

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Register
response = requests.post(f"{BASE_URL}/auth/register", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
})

data = response.json()
token = data["access_token"]

# Get books
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/nook/books", headers=headers)
books = response.json()

print(books)
```

---

**Happy Testing! 🚀**
