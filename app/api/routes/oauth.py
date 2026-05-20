"""
OAuth callback routes for Google and GitHub authentication.

These endpoints handle the OAuth callback flow and return tokens
to the frontend for use with subsequent API requests.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import secrets
import logging

from app.core.oauth import GoogleOAuth, GitHubOAuth
from app.core.security import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["oauth"])

# Store state temporarily for CSRF protection (in production, use Redis)
_oauth_states = {}


@router.get("/oauth/google/start")
async def start_google_oauth():
    """
    Initiate Google OAuth flow.
    
    Returns:
        Authorization URL for the user to visit
    """
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.utcnow() + timedelta(minutes=10)
    
    auth_url = await GoogleOAuth.get_authorization_url(state)
    
    return {
        "authorization_url": auth_url,
        "state": state,
    }


@router.get("/oauth/google/callback")
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    """
    Handle Google OAuth callback.
    
    Query Parameters:
        code: Authorization code from Google
        state: State parameter for CSRF protection
    
    Returns:
        Access token for authenticated requests
    """
    # Verify state
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    if _oauth_states[state] < datetime.utcnow():
        del _oauth_states[state]
        raise HTTPException(status_code=400, detail="State parameter expired")
    
    del _oauth_states[state]
    
    # Exchange code for token
    token_data = await GoogleOAuth.exchange_code(code)
    if not token_data or "access_token" not in token_data:
        raise HTTPException(status_code=400, detail="Failed to exchange code")
    
    # Get user info
    user_info = await GoogleOAuth.get_user_info(token_data["access_token"])
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info")
    
    # Create application access token
    email = user_info.get("email")
    name = user_info.get("name")
    
    access_token = create_access_token(
        data={"sub": email, "name": name, "provider": "google"},
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": email,
            "name": name,
            "provider": "google",
        },
    }


@router.get("/oauth/github/start")
async def start_github_oauth():
    """
    Initiate GitHub OAuth flow.
    
    Returns:
        Authorization URL for the user to visit
    """
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.utcnow() + timedelta(minutes=10)
    
    auth_url = await GitHubOAuth.get_authorization_url(state)
    
    return {
        "authorization_url": auth_url,
        "state": state,
    }


@router.get("/oauth/github/callback")
async def github_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    """
    Handle GitHub OAuth callback.
    
    Query Parameters:
        code: Authorization code from GitHub
        state: State parameter for CSRF protection
    
    Returns:
        Access token for authenticated requests
    """
    # Verify state
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    if _oauth_states[state] < datetime.utcnow():
        del _oauth_states[state]
        raise HTTPException(status_code=400, detail="State parameter expired")
    
    del _oauth_states[state]
    
    # Exchange code for token
    token_data = await GitHubOAuth.exchange_code(code)
    if not token_data or "access_token" not in token_data:
        raise HTTPException(status_code=400, detail="Failed to exchange code")
    
    # Get user info
    user_info = await GitHubOAuth.get_user_info(token_data["access_token"])
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info")
    
    # Create application access token
    email = user_info.get("email", user_info.get("login") + "@github.com")
    name = user_info.get("name") or user_info.get("login")
    
    access_token = create_access_token(
        data={"sub": email, "name": name, "provider": "github"},
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": email,
            "name": name,
            "provider": "github",
        },
    }
