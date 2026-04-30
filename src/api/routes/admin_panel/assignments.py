"""Course assignments — including bulk assignment to users / areas."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import case, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from src.core.audit import AuditAction, log_action
from src.core.permissions import require_admin
from src.db.models.learning_platform import (
    Area,
    Course,
    CourseAssignment,
    Enrollment,
    EnrollmentStatus,
    User,
)
from src.db.session import get_db
from src.schemas.admin_panel import (
    AssignmentProgressSummary,
    BulkAssignmentRequest,
    BulkAssignmentResult,
    CourseAssignmentList,
    CourseAssignmentRow,
)


router = APIRouter(prefix="/assignments")


def _to_row(
    assignment: CourseAssignment,
    user: User,
    course: Course,
    enrollment: Enrollment | None,
    assigned_by: User | None,
) -> CourseAssignmentRow:
    return CourseAssignmentRow(
        id=assignment.id,
        course_id=course.id,
        course_title=course.title,
        user_id=user.id,
        user_full_name=f"{user.first_name} {user.last_name}",
        user_email=user.email,
        area_name=user.area.name if user.area else None,
        due_date=assignment.due_date,
        assigned_by_user_id=assignment.assigned_by_user_id,
        assigned_by_user_name=(
            f"{assigned_by.first_name} {assigned_by.last_name}" if assigned_by else None
        ),
        created_at=assignment.created_at,
        progress_percent=float(enrollment.progress_percent) if enrollment else 0.0,
        enrollment_status=enrollment.status.value if enrollment else None,
        is_overdue=(
            assignment.due_date < datetime.utcnow()
            and (not enrollment or enrollment.status != EnrollmentStatus.completed)
        ),
    )


@router.get("", response_model=CourseAssignmentList)
def list_assignments(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    course_id: str | None = Query(None),
    user_id: str | None = Query(None),
    area_id: str | None = Query(None, description="Filter by user's area"),
    overdue_only: bool = Query(False),
    search: str | None = Query(None, description="Search by user name or email"),
):
    """Paginated assignments listing with filters."""
    q = (
        db.query(CourseAssignment, User, Course)
        .join(User, User.id == CourseAssignment.assigned_to_user_id)
        .join(Course, Course.id == CourseAssignment.course_id)
        .options(joinedload(CourseAssignment.assigned_to_user).joinedload(User.area))
    )

    if course_id:
        q = q.filter(CourseAssignment.course_id == course_id)
    if user_id:
        q = q.filter(CourseAssignment.assigned_to_user_id == user_id)
    if area_id:
        q = q.filter(User.area_id == area_id)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            or_(
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.email.ilike(like),
            )
        )
    if overdue_only:
        q = q.filter(CourseAssignment.due_date < datetime.utcnow())

    total = q.count()
    rows = (
        q.order_by(desc(CourseAssignment.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Resolve enrollments + assigned_by users in batch
    pairs = [(a.assigned_to_user_id, a.course_id) for a, _, _ in rows]
    enrollments_by_pair: dict[tuple[str, str], Enrollment] = {}
    if pairs:
        user_ids = list({p[0] for p in pairs})
        course_ids = list({p[1] for p in pairs})
        enrolls = (
            db.query(Enrollment)
            .filter(Enrollment.user_id.in_(user_ids), Enrollment.course_id.in_(course_ids))
            .all()
        )
        enrollments_by_pair = {(e.user_id, e.course_id): e for e in enrolls}

    actor_ids = {a.assigned_by_user_id for a, _, _ in rows if a.assigned_by_user_id}
    actors_by_id = {}
    if actor_ids:
        actors_by_id = {
            u.id: u
            for u in db.query(User).filter(User.id.in_(list(actor_ids))).all()
        }

    items = [
        _to_row(
            a,
            u,
            c,
            enrollments_by_pair.get((a.assigned_to_user_id, a.course_id)),
            actors_by_id.get(a.assigned_by_user_id) if a.assigned_by_user_id else None,
        )
        for a, u, c in rows
    ]
    return CourseAssignmentList(total=total, page=page, page_size=page_size, items=items)


@router.post("/bulk", response_model=BulkAssignmentResult, status_code=201)
def bulk_assign(
    body: BulkAssignmentRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Assign a course to many users at once. Pass either user_ids, area_ids, or both."""
    if not body.user_ids and not body.area_ids:
        raise HTTPException(
            status_code=400,
            detail="Debes proveer al menos `user_ids` o `area_ids`",
        )

    course = db.query(Course).filter(Course.id == body.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    if body.due_date <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="La fecha límite debe ser futura",
        )

    # Resolve target user_ids
    target_user_ids: set[str] = set(body.user_ids or [])

    if body.area_ids:
        users_in_areas = (
            db.query(User.id).filter(User.area_id.in_(body.area_ids)).all()
        )
        target_user_ids.update(uid for (uid,) in users_in_areas)

    if not target_user_ids:
        raise HTTPException(
            status_code=400,
            detail="No se encontraron usuarios para asignar",
        )

    # Validate which users actually exist
    found_users = (
        db.query(User.id).filter(User.id.in_(list(target_user_ids))).all()
    )
    valid_user_ids = {uid for (uid,) in found_users}
    skipped_not_found = len(target_user_ids) - len(valid_user_ids)

    # Skip users already assigned
    already_assigned = (
        db.query(CourseAssignment.assigned_to_user_id)
        .filter(
            CourseAssignment.course_id == body.course_id,
            CourseAssignment.assigned_to_user_id.in_(list(valid_user_ids)),
        )
        .all()
    )
    already_assigned_ids = {uid for (uid,) in already_assigned}
    to_create = valid_user_ids - already_assigned_ids

    created_count = 0
    affected: list[str] = []
    for uid in to_create:
        db.add(CourseAssignment(
            id=str(uuid.uuid4()),
            course_id=body.course_id,
            assigned_to_user_id=uid,
            assigned_by_user_id=current_user.id,
            due_date=body.due_date,
        ))
        affected.append(uid)
        created_count += 1

    db.commit()

    log_action(
        db,
        AuditAction.ASSIGNMENT_BULK_CREATED,
        user_id=current_user.id,
        resource_type="course",
        resource_id=body.course_id,
        description=(
            f"Asignación masiva del curso '{course.title}': "
            f"{created_count} usuarios asignados"
        ),
        extra_data={
            "course_id": body.course_id,
            "course_title": course.title,
            "due_date": body.due_date.isoformat(),
            "created": created_count,
            "skipped_already_assigned": len(already_assigned_ids),
            "skipped_not_found": skipped_not_found,
            "user_ids_input": body.user_ids,
            "area_ids_input": body.area_ids,
        },
        request=request,
    )

    return BulkAssignmentResult(
        created=created_count,
        skipped_already_assigned=len(already_assigned_ids),
        skipped_not_found=skipped_not_found,
        course_id=body.course_id,
        due_date=body.due_date,
        affected_user_ids=affected,
    )


@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(
    assignment_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    a = db.query(CourseAssignment).filter(CourseAssignment.id == assignment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    target_user_id = a.assigned_to_user_id
    course_id = a.course_id
    db.delete(a)
    db.commit()

    log_action(
        db,
        AuditAction.ASSIGNMENT_DELETED,
        user_id=current_user.id,
        resource_type="assignment",
        resource_id=assignment_id,
        description=f"Asignación eliminada del usuario {target_user_id}",
        extra_data={"target_user_id": target_user_id, "course_id": course_id},
        request=request,
    )
    return None


@router.get(
    "/courses/{course_id}/progress-summary",
    response_model=AssignmentProgressSummary,
)
def assignment_progress_summary(
    course_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Aggregated progress for a course's assignments."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    assignments = (
        db.query(CourseAssignment)
        .filter(CourseAssignment.course_id == course_id)
        .all()
    )
    total = len(assignments)
    if total == 0:
        return AssignmentProgressSummary(
            course_id=course_id,
            course_title=course.title,
            total_assigned=0,
            not_started=0,
            in_progress=0,
            completed=0,
            overdue=0,
            avg_progress=0.0,
        )

    user_ids = [a.assigned_to_user_id for a in assignments]
    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id, Enrollment.user_id.in_(user_ids))
        .all()
    )
    enroll_by_user = {e.user_id: e for e in enrollments}

    not_started = 0
    in_progress = 0
    completed = 0
    overdue = 0
    sum_progress = Decimal("0")

    now = datetime.utcnow()
    for a in assignments:
        e = enroll_by_user.get(a.assigned_to_user_id)
        if not e:
            not_started += 1
            if a.due_date < now:
                overdue += 1
            continue
        sum_progress += e.progress_percent or Decimal("0")
        if e.status == EnrollmentStatus.completed:
            completed += 1
        elif (e.progress_percent or 0) > 0:
            in_progress += 1
            if a.due_date < now:
                overdue += 1
        else:
            not_started += 1
            if a.due_date < now:
                overdue += 1

    avg_progress = float(sum_progress / total) if total else 0.0
    return AssignmentProgressSummary(
        course_id=course_id,
        course_title=course.title,
        total_assigned=total,
        not_started=not_started,
        in_progress=in_progress,
        completed=completed,
        overdue=overdue,
        avg_progress=round(avg_progress, 2),
    )
