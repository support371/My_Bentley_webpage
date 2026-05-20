# Backend Integration Guide

This guide explains how to integrate the Next.js frontend with the FastAPI backend, including CORS configuration, WebSocket setup, and OAuth integration.

## Overview

The frontend communicates with the FastAPI backend through:
- **REST API**: Axios client with JWT authentication
- **WebSockets**: Real-time event streaming
- **OAuth**: Google/Microsoft authentication (optional)

## CORS Configuration

### FastAPI Backend Setup

Add CORS middleware to your FastAPI application:

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Local development
        "http://localhost:3001",      # Alternative dev port
        "https://your-domain.com",    # Production
        "https://*.vercel.app",       # Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    expose_headers=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### Environment-based CORS

```python
# app/core/config.py
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    
    if os.getenv("ENVIRONMENT") == "production":
        CORS_ORIGINS.extend([
            "https://your-domain.com",
            "https://*.vercel.app",
        ])
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## JWT Authentication

### Token Management

The frontend automatically handles JWT token management:

```typescript
// lib/api.ts - Automatic token injection
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

### Backend JWT Configuration

```python
# app/core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        return user_id
    except JWTError:
        return None
```

### Login Endpoint

```python
# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token"""
    user = await db.execute(
        select(User).where(User.email == email)
    )
    user = user.scalars().first()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    }

@router.get("/me")
async def get_current_user(current_user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role
    }
```

## WebSocket Integration

### FastAPI WebSocket Endpoint

```python
# app/api/routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Process incoming message
            await manager.broadcast({
                "type": "message",
                "data": data
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Endpoint to trigger broadcasts from REST API
@router.post("/broadcast-event")
async def broadcast_event(event: dict):
    """Send event to all connected WebSocket clients"""
    await manager.broadcast({
        "type": "event",
        "data": event
    })
    return {"status": "sent"}
```

### Frontend WebSocket Integration

```typescript
// lib/websocket.ts - Already implemented
import { getWebSocketClient, initializeWebSocket } from '@/lib/websocket'
import { notify } from '@/lib/notifications'

// In your component or hook:
export function useWebSocket() {
  useEffect(() => {
    const connect = async () => {
      await initializeWebSocket()
      const client = getWebSocketClient()
      
      // Subscribe to events
      client.subscribe('project_updated', (data) => {
        notify.success('Project Updated', `${data.name} was updated`)
      })
      
      client.subscribe('imodel_synced', (data) => {
        notify.success('iModel Synced', `${data.name} sync complete`)
      })
      
      client.subscribe('error', (data) => {
        notify.error('Error', data.message)
      })
    }
    
    connect()
  }, [])
}
```

## OAuth Integration

### Google OAuth Setup

```python
# app/core/oauth.py
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

async def verify_google_token(token: str):
    try:
        idinfo = verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        return {
            "email": idinfo['email'],
            "name": idinfo['name'],
            "picture": idinfo.get('picture'),
            "sub": idinfo['sub']
        }
    except ValueError:
        return None

# app/api/routes/oauth.py
@router.post("/oauth/google")
async def google_oauth(token: str, db: AsyncSession = Depends(get_db)):
    """Authenticate with Google OAuth"""
    user_info = await verify_google_token(token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    
    # Find or create user
    user = await db.execute(
        select(User).where(User.email == user_info['email'])
    )
    user = user.scalars().first()
    
    if not user:
        user = User(
            email=user_info['email'],
            name=user_info['name'],
            picture=user_info.get('picture'),
            google_sub=user_info['sub'],
            hashed_password=""  # OAuth user, no password
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture
        }
    }
```

### Frontend Google OAuth

```typescript
// lib/api.ts - Add OAuth function
export async function loginWithGoogle(token: string) {
  try {
    const response = await api.post('/auth/oauth/google', { token })
    const { access_token, user } = response.data
    
    // Store token
    localStorage.setItem('access_token', access_token)
    
    // Update auth store
    useAuthStore.getState().setToken(access_token)
    useAuthStore.getState().setUser(user)
    
    return user
  } catch (error) {
    throw new Error('Google authentication failed')
  }
}
```

## API Endpoints

### Authentication
```
POST   /api/auth/login              # Email/password login
POST   /api/auth/signup             # User registration
POST   /api/auth/logout             # Clear session
POST   /api/auth/oauth/google       # Google OAuth
POST   /api/auth/oauth/microsoft    # Microsoft OAuth
GET    /api/auth/me                 # Get current user
POST   /api/auth/refresh            # Refresh token
```

### Projects
```
GET    /api/projects                # List all projects
POST   /api/projects                # Create project
GET    /api/projects/:id            # Get project details
PUT    /api/projects/:id            # Update project
DELETE /api/projects/:id            # Delete project
GET    /api/projects/:id/imodels    # List project iModels
```

### iModels
```
GET    /api/imodels                 # List all iModels
POST   /api/imodels                 # Create iModel
GET    /api/imodels/:id             # Get iModel details
PUT    /api/imodels/:id             # Update iModel
DELETE /api/imodels/:id             # Delete iModel
POST   /api/imodels/:id/sync        # Trigger sync
GET    /api/imodels/:id/sync-status # Get sync status
```

### Events
```
GET    /api/events                  # List events with filters
GET    /api/events/:id              # Get event details
POST   /api/events                  # Create event (webhook)
DELETE /api/events/:id              # Delete event
```

### Admin
```
GET    /api/admin/users             # List all users
POST   /api/admin/users             # Create user
PUT    /api/admin/users/:id         # Update user
DELETE /api/admin/users/:id         # Delete user
GET    /api/admin/audit-log         # Get audit log
GET    /api/admin/settings          # Get settings
PUT    /api/admin/settings          # Update settings
```

## Error Handling

### Frontend Error Handling

```typescript
// lib/api.ts
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      useAuthStore.getState().logout()
      router.push('/auth/login')
    } else if (error.response?.status === 403) {
      notify.error('Access Denied', 'You do not have permission')
    } else {
      notify.error('Error', error.response?.data?.detail || 'An error occurred')
    }
    return Promise.reject(error)
  }
)
```

### Backend Error Responses

```python
# Standardized error format
{
  "detail": "Error message",
  "error_code": "INVALID_CREDENTIALS",
  "status": 401
}
```

## Development vs Production

### Development Environment

```env
# .env
NEXT_PUBLIC_API_URL=http://localhost:5000/api
NEXT_PUBLIC_WS_URL=ws://localhost:5000/ws
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Production Environment

```env
# .env.production
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com/ws
CORS_ORIGINS=https://your-domain.com,https://*.vercel.app
```

## Testing the Integration

### Manual Testing Checklist

- [ ] Frontend loads without CORS errors
- [ ] Login works with valid credentials
- [ ] JWT token is stored in localStorage
- [ ] Protected routes redirect to login
- [ ] Dashboard loads project data from API
- [ ] Real-time WebSocket connects
- [ ] Notifications appear on WebSocket messages
- [ ] Admin endpoints require proper roles
- [ ] API errors display user-friendly messages

### Automated Testing

```bash
# Backend tests
cd /path/to/backend
pytest tests/

# Frontend tests
npm test

# Integration tests
npm run test:e2e
```

## Troubleshooting

### CORS Issues

```
Error: Access to XMLHttpRequest blocked by CORS
```

**Solution**: Verify CORS_ORIGINS in FastAPI includes your frontend URL.

### WebSocket Connection Failed

```
WebSocket connection failed
```

**Solution**: Ensure WebSocket endpoint is accessible and CORS allows WebSocket upgrades.

### JWT Token Issues

```
Error: Invalid token
```

**Solution**: Clear localStorage, log in again, and verify SECRET_KEY matches between frontend and backend.

### API Response 401 Unauthorized

**Solution**: Check that token is being sent in Authorization header with `Bearer` prefix.

## Security Checklist

- [ ] All sensitive data in environment variables
- [ ] HTTPS/WSS in production
- [ ] JWT tokens not exposed in URLs
- [ ] CORS restricted to trusted origins
- [ ] Rate limiting on auth endpoints
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (use parameterized queries)
- [ ] CSRF protection enabled
- [ ] Audit logging of sensitive actions

## Next Steps

1. **Configure CORS** in FastAPI app
2. **Setup OAuth** with Google/Microsoft
3. **Enable WebSockets** for real-time updates
4. **Implement Rate Limiting** on auth endpoints
5. **Add Monitoring** and alerting
6. **Deploy** to production (Vercel + CloudRun/AKS)

---

**Version**: 1.0.0  
**Last Updated**: January 2024
