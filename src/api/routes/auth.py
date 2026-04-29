"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request
from sqlalchemy.orm import Session

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from src.core.auth import authenticate_user, create_session, validate_session, invalidate_session
from src.core.audit import AuditAction, log_action
from src.db.session import get_db
from src.schemas.user import LoginRequest, LoginResponse, UserRead, UserProfileRead, UserStatsRead

router = APIRouter(tags=["auth"])

ALLOWED_EMAIL_DOMAIN = "whirpool.com"


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    http_request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Login with email and password. Sets a session cookie.

    Solo se permite el login a usuarios cuyo email pertenezca al dominio
    corporativo `@whirpool.com` (SSO empresarial).
    """
    email_normalized = request.email.strip().lower()
    if not email_normalized.endswith(f"@{ALLOWED_EMAIL_DOMAIN}"):
        log_action(
            db,
            AuditAction.AUTH_LOGIN_FAILED,
            description=f"Intento de login con dominio no autorizado: {request.email}",
            extra_data={"email": request.email, "reason": "invalid_domain"},
            request=http_request,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Only users with @{ALLOWED_EMAIL_DOMAIN} email addresses are allowed to log in",
        )

    user = authenticate_user(request.email, request.password, db)
    if not user:
        log_action(
            db,
            AuditAction.AUTH_LOGIN_FAILED,
            description=f"Intento de login fallido para {request.email}",
            extra_data={"email": request.email},
            request=http_request,
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # Get user agent and IP from request
    user_agent = http_request.headers.get("user-agent")
    ip_address = http_request.client.host if http_request.client else None

    # Create session and set cookie
    session_id = create_session(
        user_id=user.id,
        db=db,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    log_action(
        db,
        AuditAction.AUTH_LOGIN,
        user_id=user.id,
        description=f"Login exitoso de {user.email}",
        request=http_request,
    )

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=30 * 24 * 60 * 60,  # 30 days (matches settings.session_expire_days)
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
def logout(
    response: Response,
    http_request: Request,
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Logout and invalidate session."""
    user_id_for_log: str | None = None
    if session_id:
        sess = validate_session(session_id, db)
        if sess:
            user_id_for_log = sess.get("user_id")
        invalidate_session(session_id, db)

    response.delete_cookie("session_id")

    if user_id_for_log:
        log_action(
            db,
            AuditAction.AUTH_LOGOUT,
            user_id=user_id_for_log,
            description="Logout del usuario",
            request=http_request,
        )

    return {"message": "Logout successful"}


def _get_authenticated_user(session_id: str | None, db: Session):
    """Helper: validate session and return User ORM instance."""
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = validate_session(session_id, db)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    from src.db.models.learning_platform import User
    user = (
        db.query(User)
        .options(joinedload(User.area), joinedload(User.user_role_links))
        .filter(User.id == session["user_id"])
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me", response_model=UserProfileRead)
def get_current_user(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Get current logged-in user information with area and role."""
    user = _get_authenticated_user(session_id, db)

    # Get ALL role names for the user
    from src.db.models.learning_platform import Role
    role_rows = (
        db.query(Role.name)
        .join_from(Role, type(user).__table__.metadata.tables["user_roles"],
                   Role.id == type(user).__table__.metadata.tables["user_roles"].c.role_id)
        .filter(type(user).__table__.metadata.tables["user_roles"].c.user_id == user.id)
        .all()
    ) if False else None  # placeholder — actual query below

    from src.core.permissions import get_user_role_names
    role_names = get_user_role_names(db, user.id)

    # Pick a "primary" role for backward compat — prefer highest in hierarchy
    priority = ["super_admin", "content_admin", "content_editor", "content_viewer", "learner"]
    primary_role = next((r for r in priority if r in role_names), None)

    return UserProfileRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        status=user.status.value,
        area_name=user.area.name if user.area else None,
        role_name=primary_role,
        role_names=role_names,
        created_at=user.created_at,
    )


@router.get("/me/stats", response_model=UserStatsRead)
def get_current_user_stats(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Get real computed stats for the current user's profile."""
    user = _get_authenticated_user(session_id, db)

    from src.db.models.learning_platform import (
        Enrollment, EnrollmentStatus, LessonProgress, UserBadge, UserGemCollection,
    )

    # Completed courses
    completed_courses = (
        db.query(func.count(Enrollment.id))
        .filter(Enrollment.user_id == user.id, Enrollment.status == EnrollmentStatus.completed)
        .scalar() or 0
    )

    # Enrolled courses (active)
    enrolled_courses = (
        db.query(func.count(Enrollment.id))
        .filter(Enrollment.user_id == user.id, Enrollment.status == EnrollmentStatus.active)
        .scalar() or 0
    )

    # Total hours (from lesson_progress.time_spent_seconds via enrollments)
    total_seconds = (
        db.query(func.sum(LessonProgress.time_spent_seconds))
        .join(Enrollment, LessonProgress.enrollment_id == Enrollment.id)
        .filter(Enrollment.user_id == user.id)
        .scalar() or 0
    )
    total_hours = round(total_seconds / 3600, 1)

    # Badges count
    badges_count = (
        db.query(func.count(UserBadge.id))
        .filter(UserBadge.user_id == user.id)
        .scalar() or 0
    )

    # Saved gems count
    saved_gems_count = (
        db.query(func.count(UserGemCollection.id))
        .filter(UserGemCollection.user_id == user.id)
        .scalar() or 0
    )

    # Rank: count users with more completed courses than this user
    if completed_courses > 0:
        users_ahead = (
            db.query(func.count(func.distinct(Enrollment.user_id)))
            .filter(Enrollment.status == EnrollmentStatus.completed)
            .group_by(Enrollment.user_id)
            .having(func.count(Enrollment.id) > completed_courses)
            .count()
        )
        rank = users_ahead + 1
    else:
        rank = None

    return UserStatsRead(
        completed_courses=completed_courses,
        enrolled_courses=enrolled_courses,
        total_hours=total_hours,
        rank=rank,
        badges_count=badges_count,
        saved_gems_count=saved_gems_count,
    )


@router.get("/sessions")
def get_active_sessions(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Get all active sessions for the current user."""
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    session_data = validate_session(session_id, db)
    if not session_data:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
        )

    # Get all sessions for this user
    from src.db.models.learning_platform import Session as SessionModel
    from datetime import datetime
    
    sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.user_id == session_data["user_id"],
            SessionModel.expires_at > datetime.utcnow()
        )
        .order_by(SessionModel.last_activity_at.desc())
        .all()
    )

    return {
        "total": len(sessions),
        "sessions": [
            {
                "id": s.id,
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat(),
                "last_activity_at": s.last_activity_at.isoformat(),
                "user_agent": s.user_agent,
                "ip_address": s.ip_address,
                "is_current": s.id == session_id,
            }
            for s in sessions
        ],
    }


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: str,  # Path parameter: the session to revoke
    current_session_id: str | None = Cookie(None, alias="session_id"),  # Cookie: current user's session
    db: Session = Depends(get_db),
):
    """Revoke a specific session. Users can only revoke their own sessions."""
    if not current_session_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    current_session = validate_session(current_session_id, db)
    if not current_session:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
        )

    # Get the session to revoke
    from src.db.models.learning_platform import Session as SessionModel
    
    target_session = (
        db.query(SessionModel)
        .filter(SessionModel.id == session_id)
        .first()
    )

    if not target_session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    # Check if the session belongs to the current user
    if target_session.user_id != current_session["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Cannot revoke another user's session",
        )

    # Revoke the session
    invalidate_session(session_id, db)

    return {"message": "Session revoked successfully"}
