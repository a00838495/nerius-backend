"""Authentication utilities for password hashing and session management."""

import logging
import secrets
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy.orm import Session as DBSession

from src.db.models.learning_platform import User, Session
from src.core.config import settings

logger = logging.getLogger(__name__)


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# Session management using database
def create_session(
    user_id: str,
    db: DBSession,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> str:
    """Create a new session for a user and store it in the database."""
    session_id = secrets.token_urlsafe(32)
    # Use datetime.utcnow() for naive UTC time (MySQL TIMESTAMP doesn't store timezone)
    now_utc = datetime.utcnow()
    expires_at = now_utc + timedelta(days=settings.session_expire_days)
    
    session = Session(
        id=session_id,
        user_id=user_id,
        expires_at=expires_at,
        last_activity_at=now_utc,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    db.add(session)
    db.commit()
    
    return session_id


def validate_session(session_id: str, db: DBSession) -> dict | None:
    """Validate a session and return user data if valid."""
    session = db.query(Session).filter(Session.id == session_id).first()
    
    if not session:
        return None
    
    # Check if session has expired (using naive UTC time)
    now_utc = datetime.utcnow()
    if now_utc > session.expires_at:
        db.delete(session)
        db.commit()
        return None
    
    # Update last activity
    session.last_activity_at = now_utc
    db.commit()
    
    return {
        "user_id": session.user_id,
        "created_at": session.created_at,
        "expires_at": session.expires_at,
    }


def invalidate_session(session_id: str, db: DBSession) -> None:
    """Invalidate a session by deleting it from the database."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()


def cleanup_expired_sessions(db: DBSession) -> int:
    """Remove all expired sessions from the database. Returns count of deleted sessions."""
    now_utc = datetime.utcnow()
    expired_sessions = db.query(Session).filter(Session.expires_at < now_utc).all()
    count = len(expired_sessions)
    
    for session in expired_sessions:
        db.delete(session)
    
    db.commit()
    return count


def authenticate_user(email: str, password: str, db: DBSession) -> tuple[User | None, str]:
    """Authenticate a user with email and password.

    Returns (user, reason). On success: (user, "ok"). On failure user is None
    and reason is one of: "user_not_found", "empty_password_hash",
    "invalid_password", "verify_error:<exc>", "db_error:<exc>".
    """
    try:
        user = db.query(User).filter(User.email == email).first()
    except Exception as e:
        logger.exception("DB error while looking up user %s", email)
        return None, f"db_error:{type(e).__name__}:{e}"

    if not user:
        logger.info("authenticate_user: user not found for email=%s", email)
        return None, "user_not_found"

    if not user.password:
        logger.warning("authenticate_user: user %s has empty password hash", email)
        return None, "empty_password_hash"

    try:
        if not verify_password(password, user.password):
            logger.info("authenticate_user: invalid password for email=%s", email)
            return None, "invalid_password"
    except Exception as e:
        logger.exception("authenticate_user: verify_password raised for email=%s", email)
        return None, f"verify_error:{type(e).__name__}:{e}"

    return user, "ok"
