"""Admin Dashboard — counters, popular courses, completion by area, activity."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from src.core.permissions import require_admin
from src.db.models.learning_platform import (
    Area,
    Course,
    Enrollment,
    EnrollmentStatus,
    ForumPost,
    Gem,
    PublicationStatus,
    User,
    UserBadge,
    UserCertification,
    UserStatus,
    CertificationRequestStatus,
)
from src.db.session import get_db
from src.schemas.admin_panel import (
    DashboardActivityBucket,
    DashboardCompletionByArea,
    DashboardCounters,
    DashboardCoursePopularity,
    DashboardOverview,
)


router = APIRouter(prefix="/dashboard")


def _dialect_name(db: Session) -> str:
    return db.bind.dialect.name if db.bind else "unknown"


@router.get("/counters", response_model=DashboardCounters)
def dashboard_counters(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Top-level counters for the admin dashboard."""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    return DashboardCounters(
        total_users=db.query(func.count(User.id)).scalar() or 0,
        active_users=db.query(func.count(User.id)).filter(User.status == UserStatus.active).scalar() or 0,
        total_courses=db.query(func.count(Course.id)).scalar() or 0,
        published_courses=(
            db.query(func.count(Course.id))
            .filter(Course.status == PublicationStatus.PUBLISHED)
            .scalar() or 0
        ),
        total_enrollments=db.query(func.count(Enrollment.id)).scalar() or 0,
        completed_enrollments=(
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.status == EnrollmentStatus.completed)
            .scalar() or 0
        ),
        total_areas=db.query(func.count(Area.id)).scalar() or 0,
        total_certifications_issued=(
            db.query(func.count(UserCertification.id))
            .filter(UserCertification.status == CertificationRequestStatus.ISSUED)
            .scalar() or 0
        ),
        total_forum_posts=(
            db.query(func.count(ForumPost.id))
            .filter(ForumPost.status == PublicationStatus.PUBLISHED)
            .scalar() or 0
        ),
        total_gems=db.query(func.count(Gem.id)).scalar() or 0,
        total_badges_earned=db.query(func.count(UserBadge.id)).scalar() or 0,
        new_users_last_7d=(
            db.query(func.count(User.id))
            .filter(User.created_at >= week_ago)
            .scalar() or 0
        ),
        new_enrollments_last_7d=(
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.created_at >= week_ago)
            .scalar() or 0
        ),
    )


@router.get("/popular-courses", response_model=list[DashboardCoursePopularity])
def dashboard_popular_courses(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
):
    """Top courses by enrollment count."""
    completed_case = case(
        (Enrollment.status == EnrollmentStatus.completed, 1),
        else_=0,
    )

    rows = (
        db.query(
            Course.id.label("course_id"),
            Course.title.label("title"),
            func.count(Enrollment.id).label("enrollments"),
            func.sum(completed_case).label("completed"),
        )
        .join(Enrollment, Enrollment.course_id == Course.id, isouter=True)
        .group_by(Course.id, Course.title)
        .order_by(desc("enrollments"))
        .limit(limit)
        .all()
    )

    out: list[DashboardCoursePopularity] = []
    for r in rows:
        enrolled = int(r.enrollments or 0)
        completed = int(r.completed or 0)
        rate = (completed / enrolled * 100) if enrolled > 0 else 0.0
        out.append(DashboardCoursePopularity(
            course_id=r.course_id,
            title=r.title,
            enrollments=enrolled,
            completed=completed,
            completion_rate=round(rate, 2),
        ))
    return out


@router.get("/completion-by-area", response_model=list[DashboardCompletionByArea])
def dashboard_completion_by_area(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Course completion grouped by user's area."""
    completed_case = case(
        (Enrollment.status == EnrollmentStatus.completed, 1),
        else_=0,
    )

    rows = (
        db.query(
            Area.id.label("area_id"),
            Area.name.label("area_name"),
            func.count(Enrollment.id).label("enrollments"),
            func.sum(completed_case).label("completed"),
        )
        .select_from(Enrollment)
        .join(User, User.id == Enrollment.user_id)
        .join(Area, Area.id == User.area_id, isouter=True)
        .group_by(Area.id, Area.name)
        .all()
    )

    out: list[DashboardCompletionByArea] = []
    for r in rows:
        enrolled = int(r.enrollments or 0)
        completed = int(r.completed or 0)
        rate = (completed / enrolled * 100) if enrolled > 0 else 0.0
        out.append(DashboardCompletionByArea(
            area_id=r.area_id,
            area_name=r.area_name or "Sin área",
            enrollments=enrolled,
            completed=completed,
            completion_rate=round(rate, 2),
        ))
    out.sort(key=lambda x: x.enrollments, reverse=True)
    return out


@router.get("/activity", response_model=list[DashboardActivityBucket])
def dashboard_activity(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=180),
):
    """Daily activity for the last N days: new users, enrollments, completions."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    dialect = _dialect_name(db)

    if dialect == "mysql":
        date_fn = lambda col: func.date_format(col, "%Y-%m-%d")  # noqa: E731
    else:
        date_fn = lambda col: func.strftime("%Y-%m-%d", col)  # noqa: E731

    # New users
    user_rows = (
        db.query(date_fn(User.created_at).label("d"), func.count(User.id).label("c"))
        .filter(User.created_at >= cutoff)
        .group_by("d")
        .all()
    )
    users_by_day = {r.d: int(r.c) for r in user_rows}

    # New enrollments
    enr_rows = (
        db.query(date_fn(Enrollment.created_at).label("d"), func.count(Enrollment.id).label("c"))
        .filter(Enrollment.created_at >= cutoff)
        .group_by("d")
        .all()
    )
    enrollments_by_day = {r.d: int(r.c) for r in enr_rows}

    # Completions (when status changed to completed; we use completed_at)
    comp_rows = (
        db.query(date_fn(Enrollment.completed_at).label("d"), func.count(Enrollment.id).label("c"))
        .filter(
            Enrollment.completed_at.isnot(None),
            Enrollment.completed_at >= cutoff,
        )
        .group_by("d")
        .all()
    )
    completions_by_day = {r.d: int(r.c) for r in comp_rows}

    # Build a continuous list of days
    today = datetime.utcnow().date()
    out: list[DashboardActivityBucket] = []
    for i in range(days, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        out.append(DashboardActivityBucket(
            date=d,
            enrollments=enrollments_by_day.get(d, 0),
            completions=completions_by_day.get(d, 0),
            new_users=users_by_day.get(d, 0),
        ))
    return out


@router.get("/overview", response_model=DashboardOverview)
def dashboard_overview(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Single payload combining all dashboard data — convenient for the UI."""
    return DashboardOverview(
        counters=dashboard_counters(_=current_user, db=db),
        popular_courses=dashboard_popular_courses(_=current_user, db=db, limit=5),
        completion_by_area=dashboard_completion_by_area(_=current_user, db=db),
        activity_last_30d=dashboard_activity(_=current_user, db=db, days=30),
    )
