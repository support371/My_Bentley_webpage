"""
CORS (Cross-Origin Resource Sharing) configuration for frontend integration.

This module provides CORS middleware setup to allow the Next.js frontend
to communicate with the FastAPI backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def configure_cors(app: FastAPI, allowed_origins: list[str] | None = None) -> None:
    """
    Configure CORS middleware for the FastAPI application.
    
    Args:
        app: The FastAPI application instance
        allowed_origins: List of allowed origins. Defaults to localhost for development.
    """
    if allowed_origins is None:
        # Development defaults
        allowed_origins = [
            "http://localhost:3000",      # Next.js dev server
            "http://localhost:3001",      # Alternative port
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
        ],
        expose_headers=["Content-Length", "X-Total-Count"],
        max_age=3600,
    )


def get_cors_origins_from_env(dev_mode: bool = False) -> list[str]:
    """
    Get CORS origins from environment variables.
    
    Environment variables:
        CORS_ORIGINS: Comma-separated list of allowed origins
        FRONTEND_URL: Primary frontend URL
    
    Returns:
        List of allowed origins
    """
    import os
    
    origins = []
    
    # Add development defaults if in dev mode
    if dev_mode:
        origins.extend([
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ])
    
    # Add from environment
    if cors_env := os.getenv("CORS_ORIGINS"):
        origins.extend([o.strip() for o in cors_env.split(",")])
    
    if frontend_url := os.getenv("FRONTEND_URL"):
        origins.append(frontend_url)
    
    return list(set(origins))  # Remove duplicates
