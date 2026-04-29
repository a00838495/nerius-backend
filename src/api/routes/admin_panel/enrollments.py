"""Enrollments management — view all enrollments, change status, cancel."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload

from src.core.audit import AuditAction, log_action
from src.core.permissions import require_admin
from src.db.models.learning_platform import (
    Course,
    Enrollment,
    EnrollmentStatus,
    User,
)
from src.db.session import get_db
from src.schemas.admin_panel import (
    EnrollmentAdminList,
    EnrollmentAdminRead,
    EnrollmentStatusUpdate,
)


router = APIRouter(prefix="/enrollments-management")


def _to_read(e: Enrollment, user: User, course: Course) -> EnrollmentAdminRead:
    return EnrollmentAdminRead(
        id=e.id,
        user_id=user.id,
        user_full_name=f"{user.first_name} {user.last_name}",
        user_email=user.email,
        course_id=course.id,
        course_title=course.title,
        status=e.status.value,
        progress_percent=float(e.progress_percent or 0),
        score=float(e.score) if e.score is not None else None,
        started_at=e.started_at,
        completed_at=e.completed_at,
        last_activity_at=e.last_activity_at,
        created_at=e.created_at,
    )


@router.get("", response_model=EnrollmentAdminList)
def list_enrollments(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    course_id: str | None = Query(None),
    user_id: str | None = Query(None),
    status: str | None = Query(None, description="active | completed | dropped"),
    search: str | None = Query(None, description="Match user name/email"),
):
    """Paginated enrollments listing for the admin panel."""
    q = (
        db.query(Enrollment, User, Course)
        .join(User, User.id == Enrollment.user_id)
        .join(Course, Course.id == Enrollment.course_id)
    )
    if course_id:
        q = q.filter(Enrollment.course_id == course_id)
    if user_id:
        q = q.filter(Enrollment.user_id == user_id)
    if status:
        try:
            q = q.filter(Enrollment.status == EnrollmentStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {status}")
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(
            User.first_name.ilike(like),
            User.last_name.ilike(like),
            User.email.ilike(like),
        ))

    total = q.count()
    rows = (
        q.order_by(desc(Enrollment.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_to_read(e, u, c) for e, u, c in rows]
    return EnrollmentAdminList(total=total, page=page, page_size=page_size, items=items)


@router.get("/{enrollment_id}", response_model=EnrollmentAdminRead)
def get_enrollment(
    enrollment_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = (
        db.query(Enrollment, User, Course)
        .join(User, User.id == Enrollment.user_id)
        .join(Course, Course.id == Enrollment.course_id)
        .filter(Enrollment.id == enrollment_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    e, u, c = row
    return _to_read(e, u, c)


@router.put("/{enrollment_id}/status", response_model=EnrollmentAdminRead)
def update_enrollment_status(
    enrollment_id: str,
    body: EnrollmentStatusUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Change an enrollment's status manually."""
    try:
        new_status = EnrollmentStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Status inválido: {body.status}")

    e = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")

    previous = e.status
    e.status = new_status
    if new_status == EnrollmentStatus.completed and not e.completed_at:
        e.completed_at = datetime.utcnow()
    db.commit()

    log_action(
        db,
        AuditAction.ENROLLMENT_UPDATED,
        user_id=current_user.id,
        resource_type="enrollment",
        resource_id=e.id,
        description=f"Inscripción cambió status: {previous.value} → {new_status.value}",
        extra_data={
            "target_user_id": e.user_id,
            "course_id": e.course_id,
            "previous_status": previous.value,
            "new_status": new_status.value,
        },
        request=request,
    )

    return get_enrollment(enrollment_id=enrollment_id, _=current_user, db=db)


@router.delete("/{enrollment_id}", status_code=204)
def cancel_enrollment(
    enrollment_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cancel an enrollment (sets status=dropped, does not hard-delete)."""
    e = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")

    target_user_id = e.user_id
    course_id = e.course_id
    e.status = EnrollmentStatus.dropped
    db.commit()

    log_action(
        db,
        AuditAction.ENROLLMENT_CANCELLED,
        user_id=current_user.id,
        resource_type="enrollment",
        resource_id=enrollment_id,
        description=f"Inscripción cancelada del usuario {target_user_id}",
        extra_data={"target_user_id": target_user_id, "course_id": course_id},
        request=request,
    )
    return None
