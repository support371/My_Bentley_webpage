# Quick Start Guide - iTwin Ops Platform

Get the complete iTwin Ops platform running in minutes.

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Git

## Start in 3 Minutes

### 1. Clone and Install

```bash
# Frontend dependencies
npm install

# Backend dependencies  
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env.local

# Minimal configuration (update these values):
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_WS_URL=ws://localhost:5000
SECRET_KEY=your-random-key-here-min-32-chars
DATABASE_URL=sqlite:///./itwin_ops.db
```

### 3. Run Both Servers

**Terminal 1 - Frontend:**
```bash
npm run dev
# Open http://localhost:3000
```

**Terminal 2 - Backend:**
```bash
uvicorn app.main:app --reload --port 5000
# API at http://localhost:5000
```

## Access the Application

- **Login Page**: http://localhost:3000/auth/login
- **Dashboard**: http://localhost:3000/dashboard
- **Projects**: http://localhost:3000/projects
- **Events**: http://localhost:3000/events
- **Admin**: http://localhost:3000/admin
- **API Docs**: http://localhost:5000/docs

## Default Credentials

For testing (update before production):
- Email: `admin@example.com`
- Password: `admin123`

## Next Steps

### 1. Configure OAuth (Optional)

Add Google/GitHub OAuth for authentication:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your_id
GOOGLE_CLIENT_SECRET=your_secret

# GitHub OAuth  
GITHUB_CLIENT_ID=your_id
GITHUB_CLIENT_SECRET=your_secret
```

### 2. Configure Bentley API

Add Bentley iTwin credentials:

```env
BENTLEY_CLIENT_ID=your_id
BENTLEY_CLIENT_SECRET=your_secret
BENTLEY_API_BASE_URL=https://api.bentley.com/v1
```

### 3. Deploy to Production

See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- Vercel frontend deployment
- Azure/AWS backend deployment
- PostgreSQL database setup
- SSL/TLS configuration

## Project Structure Quick Reference

```
Frontend Code:     app/                 (Next.js 16 routes)
Components:        components/          (React components)
Styles:            app/globals.css      (Tailwind CSS)
State Management:  lib/store.ts         (Zustand)
API Integration:   lib/api.ts           (Axios client)

Backend Code:      app/                 (FastAPI)
Routes:            app/api/routes/      (REST endpoints)
Database:          app/db/              (SQLModel)
Auth:              app/core/security.py (JWT + OAuth)
WebSocket:         app/websocket/       (Real-time)
```

## Available Commands

**Frontend:**
```bash
npm run dev          # Development server
npm run build        # Production build
npm run start        # Production server
npm run lint         # Code quality check
```

**Backend:**
```bash
# Development
uvicorn app.main:app --reload

# With specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 5000

# Production
gunicorn app.main:app
```

## Troubleshooting

### Frontend won't start
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend API not responding
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill existing process
pkill -f "uvicorn"

# Start fresh
uvicorn app.main:app --reload
```

### CORS errors in browser
- Check `CORS_ORIGINS` in backend .env
- Ensure frontend URL is in the list
- Restart backend after changing .env

### WebSocket connection failed
- Verify `NEXT_PUBLIC_WS_URL` is correct
- Check backend WebSocket route at `/ws/events`
- Ensure backend is running

## Features Included

- **Dashboard**: Real-time KPIs and charts
- **Projects**: Full CRUD with detail views
- **iModels**: Digital twin management
- **Events**: Real-time event streaming
- **Admin**: User and system management
- **Auth**: Email + OAuth (Google, GitHub)
- **Real-time**: WebSocket integration
- **Responsive**: Mobile-friendly design

## Documentation

- [README.md](./README.md) - Complete overview
- [FRONTEND_SETUP.md](./FRONTEND_SETUP.md) - Frontend guide
- [BACKEND_INTEGRATION.md](./BACKEND_INTEGRATION.md) - Backend API docs
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production deployment
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Detailed summary

## Getting Help

1. Check the appropriate documentation file above
2. Review error messages in the browser console
3. Check backend logs in terminal
4. Review GitHub issues in the repository

## Next: Deploy to Production

When ready, follow [DEPLOYMENT.md](./DEPLOYMENT.md) to:
1. Deploy frontend to Vercel
2. Deploy backend to Azure/AWS
3. Configure production database
4. Set up SSL/TLS certificates

That's it! You now have a fully functional iTwin Ops platform running locally. Happy building!
