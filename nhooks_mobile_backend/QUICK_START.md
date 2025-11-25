# Nhooks Backend - Quick Start Guide

Get your Nhooks backend up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- MongoDB (local or cloud)
- pip (Python package manager)

## Quick Setup (5 Steps)

### Step 1: Install Dependencies

```bash
cd nhooks_mobile_backend
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit `.env` and set your MongoDB connection:

```env
MONGO_URI=mongodb://localhost:27017/hooks_mobile
# Or for MongoDB Atlas:
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/hooks_mobile
```

### Step 3: Initialize Database

```bash
python init_database.py
```

This will:
- Create all necessary indexes
- Set up badges and achievements
- Create an admin user (admin@nhooks.com / admin123)
- Optionally create sample test data

### Step 4: Start the Server

```bash
python run.py
```

You should see:
```
╔═══════════════════════════════════════════════════════════╗
║         Nhooks Mobile Backend API Server                 ║
╠═══════════════════════════════════════════════════════════╣
║  Server running on: http://0.0.0.0:5000                  ║
║  Health check: http://0.0.0.0:5000/api/health           ║
║  Debug mode: True                                         ║
╚═══════════════════════════════════════════════════════════╝
```

### Step 5: Test the API

Open a new terminal and test:

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

## Quick Test Flow

### 1. Register a User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"myuser\",\"email\":\"user@example.com\",\"password\":\"password123\"}"
```

### 2. Save Your Token

Copy the `access_token` from the response.

### 3. Get Your Profile

```bash
curl -X GET http://localhost:5000/api/auth/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

### 4. Add a Book

```bash
curl -X POST http://localhost:5000/api/nook/books \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Atomic Habits\",\"authors\":[\"James Clear\"],\"page_count\":320,\"status\":\"to_read\"}"
```

### 5. Start a Timer

```bash
curl -X POST http://localhost:5000/api/hook/timers/start \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d "{\"task_name\":\"Reading\",\"duration\":25,\"category\":\"reading\"}"
```

## MongoDB Setup Options

### Option A: Local MongoDB

1. **Install MongoDB Community Edition**
   - Windows: https://www.mongodb.com/try/download/community
   - macOS: `brew install mongodb-community`
   - Linux: Follow official docs

2. **Start MongoDB**
   ```bash
   # Windows (as service)
   net start MongoDB
   
   # macOS
   brew services start mongodb-community
   
   # Linux
   sudo systemctl start mongod
   ```

3. **Use in .env**
   ```env
   MONGO_URI=mongodb://localhost:27017/hooks_mobile
   ```

### Option B: MongoDB Atlas (Cloud - Free)

1. **Create Account**
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for free

2. **Create Cluster**
   - Choose "Shared" (Free tier)
   - Select a region close to you
   - Click "Create Cluster"

3. **Get Connection String**
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database password

4. **Whitelist IP**
   - Go to "Network Access"
   - Add IP Address
   - Choose "Allow Access from Anywhere" (for development)

5. **Use in .env**
   ```env
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/hooks_mobile?retryWrites=true&w=majority
   ```

## Default Credentials

After running `init_database.py`:

**Admin User:**
- Email: `admin@nhooks.com`
- Password: `admin123`
- ⚠️ Change this in production!

**Test User (if created):**
- Email: `test@nhooks.com`
- Password: `test123`

## Common Issues

### Issue: "ModuleNotFoundError"
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "MongoDB connection failed"
**Solution:**
- Check if MongoDB is running
- Verify MONGO_URI in .env
- For Atlas: Check IP whitelist

### Issue: "Port 5000 already in use"
**Solution:**
```bash
# Change port in .env
PORT=5001

# Or kill the process using port 5000
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:5000 | xargs kill -9
```

### Issue: "JWT token expired"
**Solution:**
Use the refresh token endpoint:
```bash
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

## Next Steps

1. **Read the full documentation**: `README.md`
2. **Explore API endpoints**: `API_TESTING_GUIDE.md`
3. **Connect your Flutter app**: Update API base URL in Flutter app
4. **Deploy to production**: See deployment section in README

## API Documentation

All endpoints are documented in `API_TESTING_GUIDE.md`

Quick reference:
- Authentication: `/api/auth/*`
- Reading (Nook): `/api/nook/*`
- Productivity (Hook): `/api/hook/*`
- Clubs: `/api/clubs/*`
- Rewards: `/api/rewards/*`
- Dashboard: `/api/dashboard/*`
- Admin: `/api/admin/*`

## Development Tips

### Enable Debug Mode
Already enabled by default in `.env`:
```env
FLASK_DEBUG=True
```

### View Logs
The server outputs logs to console. Watch for:
- Request logs
- Error messages
- Database queries

### Test with Postman
Import the endpoints from `API_TESTING_GUIDE.md` into Postman for easier testing.

### Database GUI Tools
- **MongoDB Compass** (Official): https://www.mongodb.com/products/compass
- **Robo 3T**: https://robomongo.org/
- **Studio 3T**: https://studio3t.com/

## Production Deployment

For production deployment, see the full deployment guide in `README.md`.

Quick checklist:
- [ ] Set strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Use production MongoDB (Atlas recommended)
- [ ] Set FLASK_ENV=production
- [ ] Set FLASK_DEBUG=False
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Use Gunicorn instead of Flask dev server
- [ ] Set up monitoring and logging
- [ ] Change default admin password

## Support

Need help?
- Check `README.md` for detailed documentation
- Review `API_TESTING_GUIDE.md` for endpoint examples
- Check MongoDB connection
- Verify environment variables

## Success Checklist

- [ ] MongoDB is running
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured
- [ ] Database initialized (`python init_database.py`)
- [ ] Server started (`python run.py`)
- [ ] Health check passes (`curl http://localhost:5000/api/health`)
- [ ] Can register a user
- [ ] Can login and get token
- [ ] Can access protected endpoints with token

If all checks pass, you're ready to go! 🚀

---

**Happy coding!**
