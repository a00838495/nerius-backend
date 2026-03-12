"""Forum routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
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
    UserBasicRead,
)

router = APIRouter(tags=["forum"], prefix="/forum")


def get_current_user(
    db: Session = Depends(get_db),
) -> User | None:
    """Get current authenticated user (optional for forum reading)."""
    # For now, forum is public, but we keep the structure for future auth
    return None


@router.get("", response_model=list[ForumPostSummaryRead])
def get_forum_posts(
    db: Session = Depends(get_db),
    limit: int = 10,
    skip: int = 0,
):
    """
    Get the latest forum posts (published only).
    
    - **limit**: Maximum number of posts to return (default: 10, max: 50)
    - **skip**: Number of posts to skip for pagination (default: 0)
    
    Returns posts ordered by published_at (most recent first).
    """
    # Limit validation
    if limit > 50:
        limit = 50
    if limit < 1:
        limit = 10
    
    # Query published posts with author information
    posts = (
        db.query(ForumPost)
        .options(joinedload(ForumPost.author))
        .filter(ForumPost.status == PublicationStatus.PUBLISHED)
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
