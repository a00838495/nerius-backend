"""Forum routes."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from src.core.auth import validate_session
from src.db.session import get_db
from src.db.models.learning_platform import (
    User,
    ForumPost,
    ForumComment,
    PublicationStatus,
)
from src.schemas.forum import (
    ForumPostSummaryRead,
    ForumPostDetailRead,
    ForumCommentRead,
    ForumCommentCreate,
    ForumCommentUpdate,
    ForumPostCreate,
    UserBasicRead,
)

router = APIRouter(tags=["forum"], prefix="/forum")


def get_current_user_required(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user (required for creating/deleting)."""
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    session = validate_session(session_id, db)
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


def get_current_user(
    db: Session = Depends(get_db),
) -> User | None:
    """Get current authenticated user (optional for forum reading)."""
    # For now, forum is public, but we keep the structure for future auth
    return None


@router.post("", response_model=ForumPostSummaryRead, status_code=201)
def create_forum_post(
    post_data: ForumPostCreate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """Create a new forum post. Published immediately. Requires authentication."""
    new_post = ForumPost(
        id=str(uuid.uuid4()),
        author_user_id=current_user.id,
        title=post_data.title.strip(),
        content=post_data.content.strip(),
        category=post_data.category,
        status=PublicationStatus.PUBLISHED,
        published_at=datetime.utcnow(),
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    db.refresh(new_post, ["author"])

    return ForumPostSummaryRead(
        id=new_post.id,
        title=new_post.title,
        content=new_post.content,
        category=new_post.category,
        multimedia_url=new_post.multimedia_url,
        author=UserBasicRead(
            id=new_post.author.id,
            first_name=new_post.author.first_name,
            last_name=new_post.author.last_name,
            email=new_post.author.email,
        ),
        status=new_post.status.value,
        created_at=new_post.created_at,
        published_at=new_post.published_at,
        comments_count=0,
    )


@router.get("", response_model=list[ForumPostSummaryRead])
def get_forum_posts(
    db: Session = Depends(get_db),
    limit: int = 10,
    skip: int = 0,
    category: str | None = Query(default=None, description="Filter by category"),
    sort: str = Query(default="recent", description="Sort order: recent | popular"),
):
    """Get forum posts (published only). Supports category filter and sort."""
    if limit > 50:
        limit = 50
    if limit < 1:
        limit = 10

    query = (
        db.query(ForumPost)
        .options(joinedload(ForumPost.author))
        .filter(ForumPost.status == PublicationStatus.PUBLISHED)
    )

    if category:
        query = query.filter(ForumPost.category == category)

    posts = query.order_by(ForumPost.published_at.desc()).offset(skip).limit(limit).all()

    result = []
    for post in posts:
        comments_count = (
            db.query(func.count(ForumComment.id))
            .filter(ForumComment.post_id == post.id)
            .scalar()
        )
        result.append(
            ForumPostSummaryRead(
                id=post.id,
                title=post.title,
                content=post.content,
                category=post.category,
                multimedia_url=post.multimedia_url,
                author=UserBasicRead(
                    id=post.author.id,
                    first_name=post.author.first_name,
                    last_name=post.author.last_name,
                    email=post.author.email,
                ),
                status=post.status.value,
                created_at=post.created_at,
                published_at=post.published_at,
                comments_count=comments_count,
            )
        )

    if sort == "popular":
        result.sort(key=lambda p: p.comments_count, reverse=True)

    return result


@router.get("/search", response_model=list[ForumPostSummaryRead])
def search_forum_posts(
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(default=10, le=50, description="Maximum number of results"),
    skip: int = Query(default=0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """
    Search forum posts by title or content.
    
    - **q**: Search query (minimum 2 characters, maximum 100)
    - **limit**: Maximum number of posts to return (default: 10, max: 50)
    - **skip**: Number of posts to skip for pagination (default: 0)
    
    Returns posts that match the search query in title or content,
    ordered by published_at (most recent first).
    """
    # Search term with wildcards for ILIKE
    search_term = f"%{q}%"
    
    # Query posts matching search criteria
    posts = (
        db.query(ForumPost)
        .options(joinedload(ForumPost.author))
        .filter(
            ForumPost.status == PublicationStatus.PUBLISHED,
            or_(
                ForumPost.title.ilike(search_term),
                ForumPost.content.ilike(search_term),
            )
        )
        .order_by(ForumPost.published_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Build response with comment counts
    result = []
    for post in posts:
        # Count comments for this post
        comments_count = (
            db.query(func.count(ForumComment.id))
            .filter(ForumComment.post_id == post.id)
            .scalar()
        )
        
        result.append(
            ForumPostSummaryRead(
                id=post.id,
                title=post.title,
                content=post.content,
                category=post.category,
                multimedia_url=post.multimedia_url,
                author=UserBasicRead(
                    id=post.author.id,
                    first_name=post.author.first_name,
                    last_name=post.author.last_name,
                    email=post.author.email,
                ),
                status=post.status.value,
                created_at=post.created_at,
                published_at=post.published_at,
                comments_count=comments_count,
            )
        )

    return result


@router.get("/{post_id}", response_model=ForumPostDetailRead)
def get_forum_post_detail(
    post_id: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed information for a specific forum post.
    
    - **post_id**: UUID of the forum post
    """
    post = (
        db.query(ForumPost)
        .options(joinedload(ForumPost.author))
        .filter(
            ForumPost.id == post_id,
            ForumPost.status == PublicationStatus.PUBLISHED,
        )
        .first()
    )
    
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Forum post not found or not published",
        )
    
    # Count comments
    comments_count = (
        db.query(func.count(ForumComment.id))
        .filter(ForumComment.post_id == post.id)
        .scalar()
    )
    
    return ForumPostDetailRead(
        id=post.id,
        title=post.title,
        content=post.content,
        multimedia_url=post.multimedia_url,
        author=UserBasicRead(
            id=post.author.id,
            first_name=post.author.first_name,
            last_name=post.author.last_name,
            email=post.author.email,
        ),
        status=post.status.value,
        created_at=post.created_at,
        updated_at=post.updated_at,
        published_at=post.published_at,
        comments_count=comments_count,
    )


@router.get("/{post_id}/comments", response_model=list[ForumCommentRead])
def get_forum_post_comments(
    post_id: str,
    db: Session = Depends(get_db),
):
    """
    Get all comments for a specific forum post.
    Returns top-level comments only (parent_comment_id is NULL).
    Each comment includes a replies_count field.
    
    - **post_id**: UUID of the forum post
    
    To get nested replies, you can make additional requests for specific comments.
    """
    # Verify post exists and is published
    post = (
        db.query(ForumPost)
        .filter(
            ForumPost.id == post_id,
            ForumPost.status == PublicationStatus.PUBLISHED,
        )
        .first()
    )
    
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Forum post not found or not published",
        )
    
    # Get top-level comments (no parent)
    comments = (
        db.query(ForumComment)
        .options(joinedload(ForumComment.author))
        .filter(
            ForumComment.post_id == post_id,
            ForumComment.parent_comment_id.is_(None),
        )
        .order_by(ForumComment.created_at.asc())
        .all()
    )
    
    # Build response with replies count
    result = []
    for comment in comments:
        # Count replies for this comment
        replies_count = (
            db.query(func.count(ForumComment.id))
            .filter(ForumComment.parent_comment_id == comment.id)
            .scalar()
        )
        
        result.append(
            ForumCommentRead(
                id=comment.id,
                post_id=comment.post_id,
                author=UserBasicRead(
                    id=comment.author.id,
                    first_name=comment.author.first_name,
                    last_name=comment.author.last_name,
                    email=comment.author.email,
                ),
                parent_comment_id=comment.parent_comment_id,
                content=comment.content,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                replies_count=replies_count,
            )
        )
    
    return result


@router.post("/{post_id}/comments", response_model=ForumCommentRead, status_code=201)
def create_forum_comment(
    post_id: str,
    comment_data: ForumCommentCreate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """
    Create a new comment on a forum post.
    
    - **post_id**: UUID of the forum post
    - **content**: Comment content (required, 1-5000 characters)
    - **parent_comment_id**: Optional ID of parent comment for nested replies
    
    Requires authentication.
    """
    # Verify post exists and is published
    post = (
        db.query(ForumPost)
        .filter(
            ForumPost.id == post_id,
            ForumPost.status == PublicationStatus.PUBLISHED,
        )
        .first()
    )
    
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Forum post not found or not published",
        )
    
    # If parent_comment_id is provided, verify it exists and belongs to this post
    if comment_data.parent_comment_id:
        parent_comment = (
            db.query(ForumComment)
            .filter(
                ForumComment.id == comment_data.parent_comment_id,
                ForumComment.post_id == post_id,
            )
            .first()
        )
        
        if not parent_comment:
            raise HTTPException(
                status_code=404,
                detail="Parent comment not found or does not belong to this post",
            )
    
    # Create new comment
    new_comment = ForumComment(
        id=str(uuid.uuid4()),
        post_id=post_id,
        author_user_id=current_user.id,
        parent_comment_id=comment_data.parent_comment_id,
        content=comment_data.content,
        created_at=datetime.utcnow(),
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    # Load author relationship
    db.refresh(new_comment, ["author"])
    
    # Count replies (will be 0 for new comment)
    replies_count = 0
    
    return ForumCommentRead(
        id=new_comment.id,
        post_id=new_comment.post_id,
        author=UserBasicRead(
            id=new_comment.author.id,
            first_name=new_comment.author.first_name,
            last_name=new_comment.author.last_name,
            email=new_comment.author.email,
        ),
        parent_comment_id=new_comment.parent_comment_id,
        content=new_comment.content,
        created_at=new_comment.created_at,
        updated_at=new_comment.updated_at,
        replies_count=replies_count,
    )


@router.delete("/{post_id}/comments/{comment_id}", status_code=204)
def delete_forum_comment(
    post_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """
    Delete a forum comment.
    
    - **post_id**: UUID of the forum post
    - **comment_id**: UUID of the comment to delete
    
    Users can only delete their own comments.
    Requires authentication.
    """
    # Find the comment
    comment = (
        db.query(ForumComment)
        .filter(
            ForumComment.id == comment_id,
            ForumComment.post_id == post_id,
        )
        .first()
    )
    
    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found",
        )
    
    # Check if user is the author of the comment
    if comment.author_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own comments",
        )
    
    # Delete the comment (cascade will handle replies)
    db.delete(comment)
    db.commit()
    
    return None
