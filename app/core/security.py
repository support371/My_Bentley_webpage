import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt.exceptions import PyJWTError as JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def _prepare_password(password: str) -> str:
    """Pre-hash password with SHA-256 so bcrypt always receives <=72 bytes."""
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    return pwd_context.hash(_prepare_password(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_prepare_password(plain), hashed)


def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM],
                          options={"require": ["exp", "sub"]})
    except (JWTError, KeyError):
        return None


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    if settings.SKIP_SIGNATURE_VERIFY:
        return True
    if not signature or not settings.WEBHOOK_SECRET:
        return False
    expected = hmac.new(settings.WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.lower().replace("sha256=", ""))


def get_current_user_from_cookie(request: Request) -> Optional[dict]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    return decode_token(token)


def require_auth(request: Request) -> dict:
    user = get_current_user_from_cookie(request)
    if not user:
        from fastapi.responses import RedirectResponse
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    return user


def require_admin(request: Request) -> dict:
    user = require_auth(request)
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def get_optional_user(request: Request) -> Optional[dict]:
    return get_current_user_from_cookie(request)
