"""Users management — CRUD, status changes, password reset, admin views.

This module is for the *content_admin* (and super_admin) — admin tier.
NOTE: Role assignment is super-admin-only and lives in `admin.py` (legacy).
This module focuses on regular user CRUD and status management.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from src.core.audit import AuditAction, log_action
from src.core.auth import hash_password
from src.core.permissions import require_admin
from src.db.models.learning_platform import (
    Area,
    Enrollment,
    EnrollmentStatus,
    Role,
    RoleName,
    User,
    UserBadge,
    UserCertification,
    UserRole,
    UserStatus,
)
from src.db.session import get_db
from src.schemas.admin_panel import (
    PasswordResetRequest,
    PasswordResetResponse,
    UserAdminCreate,
    UserAdminList,
    UserAdminListItem,
    UserAdminRead,
    UserAdminUpdate,
    UserStatusUpdate,
)


router = APIRouter(prefix="/users-management")


# Admin tier roles
_ADMIN_ROLE_VALUES = {
    RoleName.SUPER_ADMIN.value,
    RoleName.CONTENT_ADMIN.value,
    RoleName.CONTENT_EDITOR.value,
    RoleName.CONTENT_VIEWER.value,
}


def _user_roles(db: Session, user_id: str) -> list[str]:
    rows = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    return [r[0].value for r in rows]


def _to_list_item(user: User, roles: list[str], enrollments_count: int) -> UserAdminListItem:
    return UserAdminListItem(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        status=user.status.value,
        area_name=user.area.name if user.area else None,
        roles=roles,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        enrollments_count=enrollments_count,
    )


@router.get("", response_model=UserAdminList)
def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, description="Match on first_name, last_name or email"),
    status: str | None = Query(None, description="active | inactive | suspended"),
    area_id: str | None = Query(None),
    role: str | None = Query(None, description="Filter by role: 'learners' | 'admins' | specific role"),
    has_admin_role: bool | None = Query(None),
):
    """Paginated user list for the admin panel with filters."""
    q = db.query(User).options(joinedload(User.area))

    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            or_(
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.email.ilike(like),
            )
        )
    if status:
        try:
            q = q.filter(User.status == UserStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {status}")
    if area_id:
        q = q.filter(User.area_id == area_id)

    # Role filtering — joins with user_roles
    if role or has_admin_role is not None:
        q = q.outerjoin(UserRole, UserRole.user_id == User.id).outerjoin(Role, Role.id == UserRole.role_id)
        if role == "learners":
            # Users that have ONLY the learner role and no admin tier role
            admin_user_ids = (
                db.query(UserRole.user_id)
                .join(Role, Role.id == UserRole.role_id)
                .filter(Role.name.in_([RoleName(v) for v in _ADMIN_ROLE_VALUES]))
            )
            q = q.filter(~User.id.in_(admin_user_ids))
        elif role == "admins":
            q = q.filter(Role.name.in_([RoleName(v) for v in _ADMIN_ROLE_VALUES]))
        elif role:
            try:
                q = q.filter(Role.name == RoleName(role))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Rol inválido: {role}")

        if has_admin_role is True:
            q = q.filter(Role.name.in_([RoleName(v) for v in _ADMIN_ROLE_VALUES]))
        elif has_admin_role is False:
            admin_user_ids = (
                db.query(UserRole.user_id)
                .join(Role, Role.id == UserRole.role_id)
                .filter(Role.name.in_([RoleName(v) for v in _ADMIN_ROLE_VALUES]))
            )
            q = q.filter(~User.id.in_(admin_user_ids))

        q = q.distinct()

    total = q.count()
    rows = (
        q.order_by(desc(User.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Resolve roles + counts in batch
    user_ids = [u.id for u in rows]
    roles_by_user: dict[str, list[str]] = {uid: [] for uid in user_ids}
    if user_ids:
        role_rows = (
            db.query(UserRole.user_id, Role.name)
            .join(Role, Role.id == UserRole.role_id)
            .filter(UserRole.user_id.in_(user_ids))
            .all()
        )
        for uid, rname in role_rows:
            roles_by_user.setdefault(uid, []).append(rname.value)

    enroll_counts: dict[str, int] = {}
    if user_ids:
        enroll_rows = (
            db.query(Enrollment.user_id, func.count(Enrollment.id))
            .filter(Enrollment.user_id.in_(user_ids))
            .group_by(Enrollment.user_id)
            .all()
        )
        enroll_counts = {uid: int(c) for uid, c in enroll_rows}

    items = [
        _to_list_item(u, roles_by_user.get(u.id, []), enroll_counts.get(u.id, 0))
        for u in rows
    ]
    return UserAdminList(total=total, page=page, page_size=page_size, items=items)


@router.get("/{user_id}", response_model=UserAdminRead)
def get_user_detail(
    user_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Full user detail with stats."""
    user = (
        db.query(User)
        .options(joinedload(User.area))
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    roles = _user_roles(db, user_id)
    enrollments_count = (
        db.query(func.count(Enrollment.id)).filter(Enrollment.user_id == user_id).scalar() or 0
    )
    completed_count = (
        db.query(func.count(Enrollment.id))
        .filter(Enrollment.user_id == user_id, Enrollment.status == EnrollmentStatus.completed)
        .scalar() or 0
    )
    badges_count = (
        db.query(func.count(UserBadge.id)).filter(UserBadge.user_id == user_id).scalar() or 0
    )
    certifications_count = (
        db.query(func.count(UserCertification.id))
        .filter(UserCertification.user_id == user_id)
        .scalar() or 0
    )

    is_admin = any(r in _ADMIN_ROLE_VALUES for r in roles)

    return UserAdminRead(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        status=user.status.value,
        gender=user.gender,
        area_id=user.area_id,
        area_name=user.area.name if user.area else None,
        roles=roles,
        is_admin=is_admin,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        enrollments_count=int(enrollments_count),
        completed_courses_count=int(completed_count),
        badges_count=int(badges_count),
        certifications_count=int(certifications_count),
    )


_ASSIGNABLE_ADMIN_ROLES_ON_CREATE = {
    RoleName.CONTENT_ADMIN.value,
    RoleName.CONTENT_EDITOR.value,
    RoleName.CONTENT_VIEWER.value,
}


@router.post("", response_model=UserAdminRead, status_code=201)
def create_user(
    body: UserAdminCreate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new user.

    Always assigns the 'learner' role. Optionally, an admin role can be
    granted in the same operation via `body.role` (one of `content_admin`,
    `content_editor`, `content_viewer`). `super_admin` cannot be assigned here.
    """
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")

    if body.area_id:
        area = db.query(Area).filter(Area.id == body.area_id).first()
        if not area:
            raise HTTPException(status_code=404, detail="Área no encontrada")

    admin_role_obj: Role | None = None
    if body.role:
        if body.role not in _ASSIGNABLE_ADMIN_ROLES_ON_CREATE:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Rol no válido. Use 'content_admin', 'content_editor' o "
                    "'content_viewer'."
                ),
            )
        admin_role_obj = db.query(Role).filter(Role.name == body.role).first()
        if not admin_role_obj:
            raise HTTPException(status_code=500, detail="Rol no inicializado en BD")

    user = User(
        id=str(uuid.uuid4()),
        first_name=body.first_name,
        last_name=body.last_name,
        email=str(body.email),
        password=hash_password(body.password),
        gender=body.gender,
        area_id=body.area_id,
        status=UserStatus.active,
    )
    db.add(user)
    db.flush()

    learner_role = db.query(Role).filter(Role.name == RoleName.LEARNER).first()
    if learner_role:
        db.add(UserRole(
            user_id=user.id,
            role_id=learner_role.id,
            assigned_by_user_id=current_user.id,
        ))

    if admin_role_obj:
        db.add(UserRole(
            user_id=user.id,
            role_id=admin_role_obj.id,
            assigned_by_user_id=current_user.id,
        ))

    db.commit()
    db.refresh(user)

    log_action(
        db,
        AuditAction.USER_CREATED,
        user_id=current_user.id,
        resource_type="user",
        resource_id=user.id,
        description=f"Usuario creado: {user.email}"
        + (f" con rol {body.role}" if body.role else ""),
        extra_data={
            "email": user.email,
            "area_id": user.area_id,
            "role": body.role,
        },
        request=request,
    )

    return get_user_detail(user_id=user.id, _=current_user, db=db)


@router.put("/{user_id}", response_model=UserAdminRead)
def update_user(
    user_id: str,
    body: UserAdminUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update user fields. Does NOT change roles or password."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if body.email and body.email != user.email:
        if db.query(User).filter(User.email == str(body.email)).first():
            raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")

    if body.area_id is not None:
        if body.area_id:
            area = db.query(Area).filter(Area.id == body.area_id).first()
            if not area:
                raise HTTPException(status_code=404, detail="Área no encontrada")
        user.area_id = body.area_id or None

    for field in ("first_name", "last_name", "gender"):
        val = getattr(body, field)
        if val is not None:
            setattr(user, field, val)
    if body.email is not None:
        user.email = str(body.email)

    db.commit()
    db.refresh(user)

    log_action(
        db,
        AuditAction.USER_UPDATED,
        user_id=current_user.id,
        resource_type="user",
        resource_id=user.id,
        description=f"Usuario actualizado: {user.email}",
        request=request,
    )

    return get_user_detail(user_id=user.id, _=current_user, db=db)


@router.put("/{user_id}/status", response_model=UserAdminRead)
def update_user_status(
    user_id: str,
    body: UserStatusUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate, deactivate, or suspend a user."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio status")

    try:
        new_status = UserStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Status inválido: {body.status}")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    previous = user.status
    user.status = new_status
    db.commit()

    # Map to a more specific audit action
    action_map = {
        UserStatus.suspended: AuditAction.USER_SUSPENDED,
        UserStatus.active: AuditAction.USER_ACTIVATED,
        UserStatus.inactive: AuditAction.USER_DEACTIVATED,
    }
    log_action(
        db,
        action_map.get(new_status, AuditAction.USER_UPDATED),
        user_id=current_user.id,
        resource_type="user",
        resource_id=user.id,
        description=f"Status cambiado para {user.email}: {previous.value} → {new_status.value}",
        extra_data={"previous_status": previous.value, "new_status": new_status.value},
        request=request,
    )

    return get_user_detail(user_id=user.id, _=current_user, db=db)


@router.post("/{user_id}/reset-password", response_model=PasswordResetResponse)
def reset_user_password(
    user_id: str,
    body: PasswordResetRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reset a user's password to the value provided. Use with care."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.password = hash_password(body.new_password)
    db.commit()

    log_action(
        db,
        AuditAction.USER_PASSWORD_RESET,
        user_id=current_user.id,
        resource_type="user",
        resource_id=user.id,
        description=f"Contraseña reseteada para {user.email}",
        request=request,
    )

    return PasswordResetResponse(
        user_id=user.id,
        message="Contraseña actualizada correctamente",
    )


@router.get("/{user_id}/enrollments", response_model=list[dict[str, Any]])
def get_user_enrollments(
    user_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List of all enrollments for a user (with course title and progress)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    rows = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.course))
        .filter(Enrollment.user_id == user_id)
        .order_by(desc(Enrollment.created_at))
        .all()
    )
    return [
        {
            "id": e.id,
            "course_id": e.course_id,
            "course_title": e.course.title if e.course else None,
            "status": e.status.value,
            "progress_percent": float(e.progress_percent or 0),
            "score": float(e.score) if e.score is not None else None,
            "started_at": e.started_at,
            "completed_at": e.completed_at,
            "created_at": e.created_at,
        }
        for e in rows
    ]
