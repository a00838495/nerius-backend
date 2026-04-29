"""Forum moderation — admin-only views and actions over posts and comments."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from src.core.audit import AuditAction, log_action
from src.core.permissions import require_admin
from src.db.models.learning_platform import (
    Area,
    ForumComment,
    ForumPost,
    PublicationStatus,
    User,
)
from src.db.session import get_db
from src.schemas.admin_panel import (
    ForumCommentAdminList,
    ForumCommentAdminRead,
    ForumPostAdminList,
    ForumPostAdminRead,
    ForumPostStatusUpdate,
    ForumPostUpdate,
    ForumStats,
)


router = APIRouter(prefix="/forum-moderation")


def _post_to_read(post: ForumPost, comments_count: int) -> ForumPostAdminRead:
    return ForumPostAdminRead(
        id=post.id,
        title=post.title,
        content=post.content,
        multimedia_url=post.multimedia_url,
        status=post.status.value,
        author_id=post.author_user_id,
        author_email=post.author.email if post.author else "",
        author_full_name=(
            f"{post.author.first_name} {post.author.last_name}" if post.author else ""
        ),
        area_id=post.area_id,
        area_name=post.area.name if post.area else None,
        comments_count=comments_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
        published_at=post.published_at,
    )


@router.get("/posts", response_model=ForumPostAdminList)
def list_posts(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="draft | published | archived"),
    area_id: str | None = Query(None),
    author_id: str | None = Query(None),
    search: str | None = Query(None, description="Search in title/content"),
    no_comments: bool | None = Query(None, description="Only posts with 0 comments"),
):
    """Paginated forum posts for moderation."""
    q = (
        db.query(ForumPost)
        .options(joinedload(ForumPost.author), joinedload(ForumPost.area))
    )

    if status:
        try:
            q = q.filter(ForumPost.status == PublicationStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {status}")
    if area_id:
        q = q.filter(ForumPost.area_id == area_id)
    if author_id:
        q = q.filter(ForumPost.author_user_id == author_id)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(ForumPost.title.ilike(like), ForumPost.content.ilike(like)))

    total = q.count()
    rows = (
        q.order_by(desc(ForumPost.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Count comments per post
    post_ids = [p.id for p in rows]
    comment_counts: dict[str, int] = {}
    if post_ids:
        cc_rows = (
            db.query(ForumComment.post_id, func.count(ForumComment.id))
            .filter(ForumComment.post_id.in_(post_ids))
            .group_by(ForumComment.post_id)
            .all()
        )
        comment_counts = {pid: int(c) for pid, c in cc_rows}

    items = [_post_to_read(p, comment_counts.get(p.id, 0)) for p in rows]
    if no_comments:
        items = [it for it in items if it.comments_count == 0]
        total = len(items)
    return ForumPostAdminList(total=total, page=page, page_size=page_size, items=items)


@router.get("/posts/{post_id}", response_model=ForumPostAdminRead)
def get_post(
    post_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    post = (
        db.query(ForumPost)
        .options(joinedload(ForumPost.author), joinedload(ForumPost.area))
        .filter(ForumPost.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    cc = db.query(func.count(ForumComment.id)).filter(ForumComment.post_id == post_id).scalar() or 0
    return _post_to_read(post, int(cc))


@router.put("/posts/{post_id}", response_model=ForumPostAdminRead)
def update_post(
    post_id: str,
    body: ForumPostUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Edit a post's content or media (moderation)."""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    for field in ("title", "content", "multimedia_url"):
        val = getattr(body, field)
        if val is not None:
            setattr(post, field, val)

    db.commit()

    log_action(
        db,
        AuditAction.FORUM_POST_UPDATED,
        user_id=current_user.id,
        resource_type="forum_post",
        resource_id=post.id,
        description=f"Post actualizado: {post.title}",
        request=request,
    )
    return get_post(post_id=post_id, _=current_user, db=db)


@router.put("/posts/{post_id}/status", response_model=ForumPostAdminRead)
def update_post_status(
    post_id: str,
    body: ForumPostStatusUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Hide (archived/draft) or publish a post."""
    try:
        new_status = PublicationStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Status inválido: {body.status}")

    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    previous = post.status.value
    post.status = new_status
    if new_status == PublicationStatus.PUBLISHED and not post.published_at:
        post.published_at = datetime.utcnow()

    db.commit()

    if new_status == PublicationStatus.PUBLISHED:
        action = AuditAction.FORUM_POST_PUBLISHED
    else:
        action = AuditAction.FORUM_POST_HIDDEN

    log_action(
        db,
        action,
        user_id=current_user.id,
        resource_type="forum_post",
        resource_id=post.id,
        description=f"Post '{post.title}': {previous} → {new_status.value}",
        extra_data={"previous_status": previous, "new_status": new_status.value},
        request=request,
    )
    return get_post(post_id=post_id, _=current_user, db=db)


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Hard delete of a post and all its comments."""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    title = post.title
    db.delete(post)
    db.commit()

    log_action(
        db,
        AuditAction.FORUM_POST_DELETED,
        user_id=current_user.id,
        resource_type="forum_post",
        resource_id=post_id,
        description=f"Post eliminado: {title}",
        request=request,
    )
    return None


# ---- Comments ----


def _comment_to_read(c: ForumComment, post_title: str) -> ForumCommentAdminRead:
    return ForumCommentAdminRead(
        id=c.id,
        post_id=c.post_id,
        post_title=post_title,
        parent_comment_id=c.parent_comment_id,
        content=c.content,
        author_id=c.author_user_id,
        author_email=c.author.email if c.author else "",
        author_full_name=(
            f"{c.author.first_name} {c.author.last_name}" if c.author else ""
        ),
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("/comments", response_model=ForumCommentAdminList)
def list_comments(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    post_id: str | None = Query(None),
    author_id: str | None = Query(None),
    search: str | None = Query(None),
):
    q = (
        db.query(ForumComment, ForumPost)
        .join(ForumPost, ForumPost.id == ForumComment.post_id)
        .options(joinedload(ForumComment.author))
    )
    if post_id:
        q = q.filter(ForumComment.post_id == post_id)
    if author_id:
        q = q.filter(ForumComment.author_user_id == author_id)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(ForumComment.content.ilike(like))

    total = q.count()
    rows = (
        q.order_by(desc(ForumComment.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_comment_to_read(c, p.title) for c, p in rows]
    return ForumCommentAdminList(total=total, page=page, page_size=page_size, items=items)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    c = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")

    post_id = c.post_id
    db.delete(c)
    db.commit()

    log_action(
        db,
        AuditAction.FORUM_COMMENT_DELETED,
        user_id=current_user.id,
        resource_type="forum_comment",
        resource_id=comment_id,
        description=f"Comentario eliminado del post {post_id}",
        extra_data={"post_id": post_id},
        request=request,
    )
    return None


# ---- Stats ----


@router.get("/stats", response_model=ForumStats)
def forum_stats(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    week_ago = datetime.utcnow() - timedelta(days=7)

    total_posts = db.query(func.count(ForumPost.id)).scalar() or 0
    published = (
        db.query(func.count(ForumPost.id))
        .filter(ForumPost.status == PublicationStatus.PUBLISHED)
        .scalar() or 0
    )
    draft = (
        db.query(func.count(ForumPost.id))
        .filter(ForumPost.status == PublicationStatus.DRAFT)
        .scalar() or 0
    )
    archived = (
        db.query(func.count(ForumPost.id))
        .filter(ForumPost.status == PublicationStatus.ARCHIVED)
        .scalar() or 0
    )
    total_comments = db.query(func.count(ForumComment.id)).scalar() or 0
    posts_7d = (
        db.query(func.count(ForumPost.id))
        .filter(ForumPost.created_at >= week_ago)
        .scalar() or 0
    )

    posts_with_comments = (
        db.query(ForumComment.post_id)
        .distinct()
        .subquery()
    )
    posts_without_comments = (
        db.query(func.count(ForumPost.id))
        .filter(~ForumPost.id.in_(db.query(posts_with_comments)))
        .scalar() or 0
    )

    # Top authors
    author_rows = (
        db.query(
            User.id,
            User.first_name,
            User.last_name,
            User.email,
            func.count(ForumPost.id).label("posts"),
        )
        .join(ForumPost, ForumPost.author_user_id == User.id)
        .group_by(User.id, User.first_name, User.last_name, User.email)
        .order_by(desc("posts"))
        .limit(5)
        .all()
    )
    top_authors = [
        {
            "user_id": r.id,
            "full_name": f"{r.first_name} {r.last_name}",
            "email": r.email,
            "posts_count": int(r.posts),
        }
        for r in author_rows
    ]

    return ForumStats(
        total_posts=int(total_posts),
        published_posts=int(published),
        draft_posts=int(draft),
        archived_posts=int(archived),
        total_comments=int(total_comments),
        posts_last_7d=int(posts_7d),
        posts_without_comments=int(posts_without_comments),
        top_authors=top_authors,
    )
