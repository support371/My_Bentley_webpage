"""
OAuth integration for Google and GitHub authentication.

This module provides OAuth2 client setup and utility functions for
integrating Google and GitHub login with the FastAPI backend.
"""

import os
from typing import Optional
from dataclasses import dataclass
import httpx


@dataclass
class OAuthConfig:
    """OAuth configuration for a provider."""
    
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    redirect_uri: str
    scopes: list[str]


class GoogleOAuth:
    """Google OAuth2 configuration."""
    
    @staticmethod
    def get_config() -> OAuthConfig:
        """Get Google OAuth configuration from environment."""
        return OAuthConfig(
            client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
            redirect_uri=os.getenv(
                "GOOGLE_REDIRECT_URI",
                "http://localhost:5000/api/auth/callback/google",
            ),
            scopes=["openid", "email", "profile"],
        )
    
    @staticmethod
    async def get_authorization_url(state: str) -> str:
        """Generate Google authorization URL."""
        config = GoogleOAuth.get_config()
        scopes = " ".join(config.scopes)
        
        return (
            f"{config.authorize_url}?"
            f"client_id={config.client_id}&"
            f"redirect_uri={config.redirect_uri}&"
            f"response_type=code&"
            f"scope={scopes}&"
            f"state={state}"
        )
    
    @staticmethod
    async def exchange_code(code: str) -> Optional[dict]:
        """Exchange authorization code for access token."""
        config = GoogleOAuth.get_config()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config.token_url,
                    data={
                        "code": code,
                        "client_id": config.client_id,
                        "client_secret": config.client_secret,
                        "redirect_uri": config.redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
        except Exception as e:
            print(f"Error exchanging code: {e}")
            return None
    
    @staticmethod
    async def get_user_info(access_token: str) -> Optional[dict]:
        """Get user info using access token."""
        config = GoogleOAuth.get_config()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    config.userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None


class GitHubOAuth:
    """GitHub OAuth2 configuration."""
    
    @staticmethod
    def get_config() -> OAuthConfig:
        """Get GitHub OAuth configuration from environment."""
        return OAuthConfig(
            client_id=os.getenv("GITHUB_CLIENT_ID", ""),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET", ""),
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user",
            redirect_uri=os.getenv(
                "GITHUB_REDIRECT_URI",
                "http://localhost:5000/api/auth/callback/github",
            ),
            scopes=["user:email", "read:user"],
        )
    
    @staticmethod
    async def get_authorization_url(state: str) -> str:
        """Generate GitHub authorization URL."""
        config = GitHubOAuth.get_config()
        scopes = ",".join(config.scopes)
        
        return (
            f"{config.authorize_url}?"
            f"client_id={config.client_id}&"
            f"redirect_uri={config.redirect_uri}&"
            f"scope={scopes}&"
            f"state={state}"
        )
    
    @staticmethod
    async def exchange_code(code: str) -> Optional[dict]:
        """Exchange authorization code for access token."""
        config = GitHubOAuth.get_config()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config.token_url,
                    headers={"Accept": "application/json"},
                    data={
                        "client_id": config.client_id,
                        "client_secret": config.client_secret,
                        "code": code,
                    },
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
        except Exception as e:
            print(f"Error exchanging code: {e}")
            return None
    
    @staticmethod
    async def get_user_info(access_token: str) -> Optional[dict]:
        """Get user info using access token."""
        config = GitHubOAuth.get_config()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    config.userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None
