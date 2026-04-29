"""Areas / Departments management."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.core.audit import AuditAction, log_action
from src.core.permissions import require_admin
from src.db.models.learning_platform import Area, Course, ForumPost, User
from src.db.session import get_db
from src.schemas.admin_panel import AreaAdminRead, AreaCreate, AreaUpdate


router = APIRouter(prefix="/areas-management")


def _to_read(area: Area, users: int, courses: int, posts: int) -> AreaAdminRead:
    return AreaAdminRead(
        id=area.id,
        name=area.name,
        created_at=area.created_at,
        users_count=users,
        courses_count=courses,
        forum_posts_count=posts,
    )


@router.get("", response_model=list[AreaAdminRead])
def list_areas(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all areas with counts."""
    areas = db.query(Area).order_by(Area.name).all()
    if not areas:
        return []

    ids = [a.id for a in areas]
    user_counts = dict(
        db.query(User.area_id, func.count(User.id))
        .filter(User.area_id.in_(ids))
        .group_by(User.area_id)
        .all()
    )
    course_counts = dict(
        db.query(Course.area_id, func.count(Course.id))
        .filter(Course.area_id.in_(ids))
        .group_by(Course.area_id)
        .all()
    )
    post_counts = dict(
        db.query(ForumPost.area_id, func.count(ForumPost.id))
        .filter(ForumPost.area_id.in_(ids))
        .group_by(ForumPost.area_id)
        .all()
    )

    return [
        _to_read(
            a,
            int(user_counts.get(a.id, 0)),
            int(course_counts.get(a.id, 0)),
            int(post_counts.get(a.id, 0)),
        )
        for a in areas
    ]


@router.get("/{area_id}", response_model=AreaAdminRead)
def get_area(
    area_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    users = db.query(func.count(User.id)).filter(User.area_id == area_id).scalar() or 0
    courses = db.query(func.count(Course.id)).filter(Course.area_id == area_id).scalar() or 0
    posts = db.query(func.count(ForumPost.id)).filter(ForumPost.area_id == area_id).scalar() or 0
    return _to_read(area, int(users), int(courses), int(posts))


@router.post("", response_model=AreaAdminRead, status_code=201)
def create_area(
    body: AreaCreate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(Area).filter(Area.name == body.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un área con ese nombre")

    area = Area(id=str(uuid.uuid4()), name=body.name)
    db.add(area)
    db.commit()
    db.refresh(area)

    log_action(
        db,
        AuditAction.AREA_CREATED,
        user_id=current_user.id,
        resource_type="area",
        resource_id=area.id,
        description=f"Área creada: {area.name}",
        request=request,
    )

    return _to_read(area, 0, 0, 0)


@router.put("/{area_id}", response_model=AreaAdminRead)
def update_area(
    area_id: str,
    body: AreaUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")

    if body.name != area.name:
        existing = db.query(Area).filter(Area.name == body.name).first()
        if existing:
            raise HTTPException(status_code=409, detail="Ya existe un área con ese nombre")

    previous_name = area.name
    area.name = body.name
    db.commit()
    db.refresh(area)

    log_action(
        db,
        AuditAction.AREA_UPDATED,
        user_id=current_user.id,
        resource_type="area",
        resource_id=area.id,
        description=f"Área renombrada: {previous_name} → {area.name}",
        extra_data={"previous_name": previous_name, "new_name": area.name},
        request=request,
    )

    return get_area(area_id=area_id, _=current_user, db=db)


@router.delete("/{area_id}", status_code=204)
def delete_area(
    area_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete an area. Users/courses/posts pointing to it get area_id=NULL via FK."""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")

    name = area.name
    db.delete(area)
    db.commit()

    log_action(
        db,
        AuditAction.AREA_DELETED,
        user_id=current_user.id,
        resource_type="area",
        resource_id=area_id,
        description=f"Área eliminada: {name}",
        request=request,
    )
    return None
