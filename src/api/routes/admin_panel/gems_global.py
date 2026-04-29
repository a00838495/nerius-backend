"""Global gems management — CRUD across the whole platform plus categories/tags."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from src.core.audit import AuditAction, log_action
from src.core.permissions import require_admin
from src.db.models.learning_platform import (
    Area,
    Gem,
    GemCategory,
    GemTag,
    GemTagLink,
    GemVisibility,
    PublicationStatus,
    User,
    UserGemCollection,
)
from src.db.session import get_db
from src.schemas.admin_panel import (
    GemAdminCreate,
    GemAdminList,
    GemAdminListItem,
    GemAdminUpdate,
    GemCategoryCreate,
    GemCategoryRead,
    GemCategoryUpdate,
    GemTagCreate,
    GemTagRead,
)


router = APIRouter(prefix="/gems-global")


def _to_list_item(
    gem: Gem,
    saved_count: int,
    tag_names: list[str],
) -> GemAdminListItem:
    return GemAdminListItem(
        id=gem.id,
        title=gem.title,
        description=gem.description,
        icon_url=gem.icon_url,
        visibility=gem.visibility.value,
        status=gem.status.value,
        is_featured=gem.is_featured,
        usage_count=gem.usage_count,
        saved_count=saved_count,
        category_id=gem.category_id,
        category_name=gem.category.name if gem.category else None,
        area_id=gem.area_id,
        area_name=gem.area.name if gem.area else None,
        created_by_user_id=gem.created_by_user_id,
        created_by_user_name=(
            f"{gem.created_by_user.first_name} {gem.created_by_user.last_name}"
            if gem.created_by_user else ""
        ),
        created_at=gem.created_at,
        updated_at=gem.updated_at,
        tags=tag_names,
    )


# ============================================================================
# GEMS
# ============================================================================


@router.get("/gems", response_model=GemAdminList)
def list_gems(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    status: str | None = Query(None),
    category_id: str | None = Query(None),
    area_id: str | None = Query(None),
    is_featured: bool | None = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|usage_count|saved_count|title)$"),
):
    """List gems with filters and sorting."""
    q = (
        db.query(Gem)
        .options(
            joinedload(Gem.category),
            joinedload(Gem.area),
            joinedload(Gem.created_by_user),
        )
    )

    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(Gem.title.ilike(like), Gem.description.ilike(like)))
    if status:
        try:
            q = q.filter(Gem.status == PublicationStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {status}")
    if category_id:
        q = q.filter(Gem.category_id == category_id)
    if area_id:
        q = q.filter(Gem.area_id == area_id)
    if is_featured is not None:
        q = q.filter(Gem.is_featured == is_featured)

    total = q.count()

    if sort_by == "saved_count":
        # Special path: order by collection count
        sub = (
            db.query(
                UserGemCollection.gem_id.label("gid"),
                func.count(UserGemCollection.id).label("cnt"),
            )
            .group_by(UserGemCollection.gem_id)
            .subquery()
        )
        q = q.outerjoin(sub, sub.c.gid == Gem.id).order_by(desc(func.coalesce(sub.c.cnt, 0)))
    elif sort_by == "title":
        q = q.order_by(Gem.title)
    else:
        q = q.order_by(desc(getattr(Gem, sort_by)))

    rows = q.offset((page - 1) * page_size).limit(page_size).all()

    gem_ids = [g.id for g in rows]

    saved_counts: dict[str, int] = {}
    if gem_ids:
        saved_rows = (
            db.query(UserGemCollection.gem_id, func.count(UserGemCollection.id))
            .filter(UserGemCollection.gem_id.in_(gem_ids))
            .group_by(UserGemCollection.gem_id)
            .all()
        )
        saved_counts = {gid: int(c) for gid, c in saved_rows}

    tags_by_gem: dict[str, list[str]] = {}
    if gem_ids:
        tag_rows = (
            db.query(GemTagLink.gem_id, GemTag.name)
            .join(GemTag, GemTag.id == GemTagLink.tag_id)
            .filter(GemTagLink.gem_id.in_(gem_ids))
            .all()
        )
        for gid, tname in tag_rows:
            tags_by_gem.setdefault(gid, []).append(tname)

    items = [
        _to_list_item(g, saved_counts.get(g.id, 0), tags_by_gem.get(g.id, []))
        for g in rows
    ]
    return GemAdminList(total=total, page=page, page_size=page_size, items=items)


@router.get("/gems/{gem_id}", response_model=GemAdminListItem)
def get_gem(
    gem_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    g = (
        db.query(Gem)
        .options(joinedload(Gem.category), joinedload(Gem.area), joinedload(Gem.created_by_user))
        .filter(Gem.id == gem_id)
        .first()
    )
    if not g:
        raise HTTPException(status_code=404, detail="Gema no encontrada")

    saved = (
        db.query(func.count(UserGemCollection.id))
        .filter(UserGemCollection.gem_id == gem_id)
        .scalar() or 0
    )
    tags = (
        db.query(GemTag.name)
        .join(GemTagLink, GemTagLink.tag_id == GemTag.id)
        .filter(GemTagLink.gem_id == gem_id)
        .all()
    )
    return _to_list_item(g, int(saved), [t[0] for t in tags])


@router.post("/gems", response_model=GemAdminListItem, status_code=201)
def create_gem(
    body: GemAdminCreate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        visibility = GemVisibility(body.visibility)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Visibility inválida: {body.visibility}")
    try:
        status = PublicationStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Status inválido: {body.status}")

    if body.category_id and not db.query(GemCategory).filter(GemCategory.id == body.category_id).first():
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if body.area_id and not db.query(Area).filter(Area.id == body.area_id).first():
        raise HTTPException(status_code=404, detail="Área no encontrada")

    gem = Gem(
        id=str(uuid.uuid4()),
        title=body.title,
        description=body.description,
        instructions=body.instructions,
        icon_url=body.icon_url,
        gemini_url=body.gemini_url,
        conversation_starters=body.conversation_starters,
        visibility=visibility,
        is_featured=body.is_featured,
        status=status,
        category_id=body.category_id,
        area_id=body.area_id,
        created_by_user_id=current_user.id,
    )
    db.add(gem)
    db.flush()

    # Tags
    if body.tag_ids:
        for tid in body.tag_ids:
            db.add(GemTagLink(gem_id=gem.id, tag_id=tid))

    db.commit()
    db.refresh(gem)

    log_action(
        db,
        AuditAction.GEM_CREATED,
        user_id=current_user.id,
        resource_type="gem",
        resource_id=gem.id,
        description=f"Gema creada: {gem.title}",
        request=request,
    )

    return get_gem(gem_id=gem.id, _=current_user, db=db)


@router.put("/gems/{gem_id}", response_model=GemAdminListItem)
def update_gem(
    gem_id: str,
    body: GemAdminUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    gem = db.query(Gem).filter(Gem.id == gem_id).first()
    if not gem:
        raise HTTPException(status_code=404, detail="Gema no encontrada")

    if body.visibility is not None:
        try:
            gem.visibility = GemVisibility(body.visibility)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Visibility inválida: {body.visibility}")
    if body.status is not None:
        try:
            gem.status = PublicationStatus(body.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {body.status}")

    if body.category_id is not None:
        if body.category_id and not db.query(GemCategory).filter(GemCategory.id == body.category_id).first():
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        gem.category_id = body.category_id or None
    if body.area_id is not None:
        if body.area_id and not db.query(Area).filter(Area.id == body.area_id).first():
            raise HTTPException(status_code=404, detail="Área no encontrada")
        gem.area_id = body.area_id or None

    for field in ("title", "description", "instructions", "icon_url", "gemini_url", "conversation_starters", "is_featured"):
        val = getattr(body, field)
        if val is not None:
            setattr(gem, field, val)

    if body.tag_ids is not None:
        # Replace tags
        db.query(GemTagLink).filter(GemTagLink.gem_id == gem_id).delete()
        for tid in body.tag_ids:
            db.add(GemTagLink(gem_id=gem_id, tag_id=tid))

    db.commit()

    log_action(
        db,
        AuditAction.GEM_UPDATED,
        user_id=current_user.id,
        resource_type="gem",
        resource_id=gem_id,
        description=f"Gema actualizada: {gem.title}",
        request=request,
    )

    return get_gem(gem_id=gem_id, _=current_user, db=db)


@router.delete("/gems/{gem_id}", status_code=204)
def delete_gem(
    gem_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    gem = db.query(Gem).filter(Gem.id == gem_id).first()
    if not gem:
        raise HTTPException(status_code=404, detail="Gema no encontrada")
    title = gem.title
    db.delete(gem)
    db.commit()

    log_action(
        db,
        AuditAction.GEM_DELETED,
        user_id=current_user.id,
        resource_type="gem",
        resource_id=gem_id,
        description=f"Gema eliminada: {title}",
        request=request,
    )
    return None


# ============================================================================
# CATEGORIES
# ============================================================================


@router.get("/categories", response_model=list[GemCategoryRead])
def list_categories(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cats = db.query(GemCategory).order_by(GemCategory.sort_order, GemCategory.name).all()
    if not cats:
        return []

    counts = dict(
        db.query(Gem.category_id, func.count(Gem.id))
        .filter(Gem.category_id.in_([c.id for c in cats]))
        .group_by(Gem.category_id)
        .all()
    )
    return [
        GemCategoryRead(
            id=c.id,
            name=c.name,
            description=c.description,
            icon=c.icon,
            sort_order=c.sort_order,
            gems_count=int(counts.get(c.id, 0)),
        )
        for c in cats
    ]


@router.post("/categories", response_model=GemCategoryRead, status_code=201)
def create_category(
    body: GemCategoryCreate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(GemCategory).filter(GemCategory.name == body.name).first():
        raise HTTPException(status_code=409, detail="Ya existe una categoría con ese nombre")

    cat = GemCategory(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        icon=body.icon,
        sort_order=body.sort_order,
    )
    db.add(cat)
    db.commit()

    log_action(
        db,
        AuditAction.GEM_CATEGORY_CREATED,
        user_id=current_user.id,
        resource_type="gem_category",
        resource_id=cat.id,
        description=f"Categoría de gemas creada: {cat.name}",
        request=request,
    )
    return GemCategoryRead(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        icon=cat.icon,
        sort_order=cat.sort_order,
        gems_count=0,
    )


@router.put("/categories/{category_id}", response_model=GemCategoryRead)
def update_category(
    category_id: str,
    body: GemCategoryUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cat = db.query(GemCategory).filter(GemCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    if body.name is not None and body.name != cat.name:
        if db.query(GemCategory).filter(GemCategory.name == body.name).first():
            raise HTTPException(status_code=409, detail="Ya existe una categoría con ese nombre")
        cat.name = body.name

    for field in ("description", "icon", "sort_order"):
        val = getattr(body, field)
        if val is not None:
            setattr(cat, field, val)

    db.commit()

    log_action(
        db,
        AuditAction.GEM_CATEGORY_UPDATED,
        user_id=current_user.id,
        resource_type="gem_category",
        resource_id=cat.id,
        description=f"Categoría actualizada: {cat.name}",
        request=request,
    )

    gems_count = db.query(func.count(Gem.id)).filter(Gem.category_id == category_id).scalar() or 0
    return GemCategoryRead(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        icon=cat.icon,
        sort_order=cat.sort_order,
        gems_count=int(gems_count),
    )


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(
    category_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cat = db.query(GemCategory).filter(GemCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    name = cat.name
    db.delete(cat)
    db.commit()

    log_action(
        db,
        AuditAction.GEM_CATEGORY_DELETED,
        user_id=current_user.id,
        resource_type="gem_category",
        resource_id=category_id,
        description=f"Categoría eliminada: {name}",
        request=request,
    )
    return None


# ============================================================================
# TAGS
# ============================================================================


@router.get("/tags", response_model=list[GemTagRead])
def list_tags(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    tags = db.query(GemTag).order_by(GemTag.name).all()
    counts = dict(
        db.query(GemTagLink.tag_id, func.count(GemTagLink.gem_id))
        .group_by(GemTagLink.tag_id)
        .all()
    )
    return [
        GemTagRead(id=t.id, name=t.name, gems_count=int(counts.get(t.id, 0)))
        for t in tags
    ]


@router.post("/tags", response_model=GemTagRead, status_code=201)
def create_tag(
    body: GemTagCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(GemTag).filter(GemTag.name == body.name).first():
        raise HTTPException(status_code=409, detail="Ya existe un tag con ese nombre")

    tag = GemTag(id=str(uuid.uuid4()), name=body.name)
    db.add(tag)
    db.commit()
    return GemTagRead(id=tag.id, name=tag.name, gems_count=0)


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(
    tag_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    tag = db.query(GemTag).filter(GemTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag no encontrado")
    db.delete(tag)
    db.commit()
    return None
