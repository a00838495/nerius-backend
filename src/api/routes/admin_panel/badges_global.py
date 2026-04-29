"""Global badges management — CRUD plus visibility into who earned each badge."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from src.core.audit import AuditAction, log_action
from src.core.permissions import require_admin
from src.db.models.learning_platform import (
    Badge,
    CourseBadge,
    User,
    UserBadge,
)
from src.db.session import get_db
from src.schemas.admin_panel import (
    BadgeAdminCreate,
    BadgeAdminRead,
    BadgeAdminUpdate,
    BadgeAwardItem,
)


router = APIRouter(prefix="/badges-global")


def _to_read(b: Badge, awarded: int, courses_linked: int) -> BadgeAdminRead:
    return BadgeAdminRead(
        id=b.id,
        name=b.name,
        description=b.description,
        icon_url=b.icon_url,
        main_color=b.main_color,
        secondary_color=b.secondary_color,
        awarded_count=awarded,
        courses_linked=courses_linked,
        created_at=b.created_at,
    )


@router.get("", response_model=list[BadgeAdminRead])
def list_badges(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    search: str | None = Query(None),
):
    """List badges with award and course-linked counts."""
    q = db.query(Badge)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(Badge.name.ilike(like), Badge.description.ilike(like)))
    badges = q.order_by(Badge.name).all()

    if not badges:
        return []

    badge_ids = [b.id for b in badges]
    awarded = dict(
        db.query(UserBadge.badge_id, func.count(UserBadge.id))
        .filter(UserBadge.badge_id.in_(badge_ids))
        .group_by(UserBadge.badge_id)
        .all()
    )
    courses_linked = dict(
        db.query(CourseBadge.badge_id, func.count(CourseBadge.id))
        .filter(CourseBadge.badge_id.in_(badge_ids))
        .group_by(CourseBadge.badge_id)
        .all()
    )

    return [
        _to_read(b, int(awarded.get(b.id, 0)), int(courses_linked.get(b.id, 0)))
        for b in badges
    ]


@router.get("/{badge_id}", response_model=BadgeAdminRead)
def get_badge(
    badge_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    b = db.query(Badge).filter(Badge.id == badge_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Badge no encontrado")
    awarded = db.query(func.count(UserBadge.id)).filter(UserBadge.badge_id == badge_id).scalar() or 0
    courses_linked = (
        db.query(func.count(CourseBadge.id)).filter(CourseBadge.badge_id == badge_id).scalar() or 0
    )
    return _to_read(b, int(awarded), int(courses_linked))


@router.post("", response_model=BadgeAdminRead, status_code=201)
def create_badge(
    body: BadgeAdminCreate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    badge = Badge(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        icon_url=body.icon_url,
        main_color=body.main_color,
        secondary_color=body.secondary_color,
    )
    db.add(badge)
    db.commit()

    log_action(
        db,
        AuditAction.BADGE_CREATED,
        user_id=current_user.id,
        resource_type="badge",
        resource_id=badge.id,
        description=f"Badge creado: {badge.name}",
        request=request,
    )
    return _to_read(badge, 0, 0)


@router.put("/{badge_id}", response_model=BadgeAdminRead)
def update_badge(
    badge_id: str,
    body: BadgeAdminUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    badge = db.query(Badge).filter(Badge.id == badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge no encontrado")

    for field in ("name", "description", "icon_url", "main_color", "secondary_color"):
        val = getattr(body, field)
        if val is not None:
            setattr(badge, field, val)
    db.commit()

    log_action(
        db,
        AuditAction.BADGE_UPDATED,
        user_id=current_user.id,
        resource_type="badge",
        resource_id=badge.id,
        description=f"Badge actualizado: {badge.name}",
        request=request,
    )
    return get_badge(badge_id=badge_id, _=current_user, db=db)


@router.delete("/{badge_id}", status_code=204)
def delete_badge(
    badge_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    badge = db.query(Badge).filter(Badge.id == badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge no encontrado")
    name = badge.name
    db.delete(badge)
    db.commit()

    log_action(
        db,
        AuditAction.BADGE_DELETED,
        user_id=current_user.id,
        resource_type="badge",
        resource_id=badge_id,
        description=f"Badge eliminado: {name}",
        request=request,
    )
    return None


@router.get("/{badge_id}/awards", response_model=list[BadgeAwardItem])
def list_badge_awards(
    badge_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
):
    """Users who earned a specific badge."""
    badge = db.query(Badge).filter(Badge.id == badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge no encontrado")

    rows = (
        db.query(UserBadge, User)
        .join(User, User.id == UserBadge.user_id)
        .filter(UserBadge.badge_id == badge_id)
        .order_by(desc(UserBadge.awarded_at))
        .limit(limit)
        .all()
    )
    return [
        BadgeAwardItem(
            id=ub.id,
            user_id=u.id,
            user_full_name=f"{u.first_name} {u.last_name}",
            user_email=u.email,
            awarded_at=ub.awarded_at,
        )
        for ub, u in rows
    ]
