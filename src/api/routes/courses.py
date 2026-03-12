"""Courses routes."""

from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session

from src.core.auth import validate_session
from src.db.session import get_db
from src.db.models.learning_platform import User, Course, Enrollment, EnrollmentStatus
from src.schemas.user import CourseRead, EnrollmentRead

router = APIRouter(tags=["courses"], prefix="/courses")


def get_current_user(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user."""
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

    user = db.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


@router.get("", response_model=list[CourseRead])
def get_available_courses(db: Session = Depends(get_db)):
    """Get all published courses in the platform."""
    courses = (
        db.query(Course)
        .filter(Course.status == "published")
        .all()
    )
    return [
        CourseRead(
            id=course.id,
            title=course.title,
            description=course.description,
            status=course.status.value,
            estimated_minutes=course.estimated_minutes,
            cover_url=course.cover_url,
        )
        for course in courses
    ]


@router.get("/user/pending", response_model=list[EnrollmentRead])
def get_user_pending_courses(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Get pending courses (active enrollments) for the current user."""
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

    user = db.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Get active enrollments for the user
    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == user.id,
            Enrollment.status == EnrollmentStatus.active,
        )
        .all()
    )

    return [
        EnrollmentRead(
            id=enrollment.id,
            course_id=enrollment.course_id,
            status=enrollment.status.value,
            progress_percent=float(enrollment.progress_percent),
            course=CourseRead(
                id=enrollment.course.id,
                title=enrollment.course.title,
                description=enrollment.course.description,
                status=enrollment.course.status.value,
                estimated_minutes=enrollment.course.estimated_minutes,
                cover_url=enrollment.course.cover_url,
            ) if enrollment.course else None,
        )
        for enrollment in enrollments
    ]
