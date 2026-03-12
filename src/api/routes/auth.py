"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.orm import Session

from src.core.auth import authenticate_user, create_session, validate_session, invalidate_session
from src.db.session import get_db
from src.schemas.user import LoginRequest, LoginResponse, UserRead

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Login with email and password. Sets a session cookie."""
    user = authenticate_user(request.email, request.password, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # Create session and set cookie
    session_id = create_session(user.id, user.email)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return LoginResponse(
        message="Login successful",
        user=UserRead(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            status=user.status.value,
        ),
    )


@router.post("/logout")
def logout(response: Response, session_id: str | None = Cookie(None)):
    """Logout and invalidate session."""
    if session_id:
        invalidate_session(session_id)
    
    response.delete_cookie("session_id")
    
    return {"message": "Logout successful"}


@router.get("/me", response_model=UserRead)
def get_current_user(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Get current logged-in user information."""
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    session = validate_session(session_id)
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
        )

    # Get user from database
    from src.db.models.learning_platform import User
    user = db.query(User).filter(User.id == session["user_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return UserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        status=user.status.value,
    )
