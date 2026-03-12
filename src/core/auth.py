"""Authentication utilities for password hashing and session management."""

import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.db.models.learning_platform import User
from src.core.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# Session management
SESSION_STORAGE: dict[str, dict] = {}  # In-memory session storage (use Redis in production)


def create_session(user_id: str, user_email: str) -> str:
    """Create a new session for a user."""
    session_id = secrets.token_urlsafe(32)
    SESSION_STORAGE[session_id] = {
        "user_id": user_id,
        "email": user_email,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return session_id


def validate_session(session_id: str) -> dict | None:
    """Validate a session and return user data if valid."""
    if session_id not in SESSION_STORAGE:
        return None

    session = SESSION_STORAGE[session_id]
    
    # Check if session has expired
    if datetime.now(timezone.utc) > session["expires_at"]:
        del SESSION_STORAGE[session_id]
        return None
    
    return session


def invalidate_session(session_id: str) -> None:
    """Invalidate a session."""
    if session_id in SESSION_STORAGE:
        del SESSION_STORAGE[session_id]


def authenticate_user(email: str, password: str, db: Session) -> User | None:
    """Authenticate a user with email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user
