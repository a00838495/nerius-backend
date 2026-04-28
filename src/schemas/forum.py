"""Forum schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserBasicRead(BaseModel):
    """Basic user information for forum posts/comments."""
    id: str
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ForumCommentRead(BaseModel):
    """Forum comment response schema."""
    id: str
    post_id: str
    author: UserBasicRead
    parent_comment_id: str | None
    content: str
    created_at: datetime
    updated_at: datetime | None
    replies_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ForumPostSummaryRead(BaseModel):
    """Forum post summary for list view."""
    id: str
    title: str
    content: str
    category: str | None = None
    multimedia_url: str | None
    author: UserBasicRead
    status: str
    created_at: datetime
    published_at: datetime | None
    comments_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ForumPostDetailRead(BaseModel):
    """Forum post detail with full information."""
    id: str
    title: str
    content: str
    category: str | None = None
    multimedia_url: str | None
    author: UserBasicRead
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    comments_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Input schemas for creating/updating forum content
# ============================================================

class ForumPostCreate(BaseModel):
    """Schema for creating a new forum post."""
    title: str = Field(..., min_length=5, max_length=180)
    content: str = Field(..., min_length=10, max_length=10000)
    category: str | None = Field(default="General", max_length=80)

    model_config = ConfigDict(from_attributes=True)


class ForumCommentCreate(BaseModel):
    """Schema for creating a new comment."""
    content: str = Field(..., min_length=1, max_length=5000)
    parent_comment_id: str | None = Field(default=None, description="ID of parent comment for nested replies")

    model_config = ConfigDict(from_attributes=True)


class ForumCommentUpdate(BaseModel):
    """Schema for updating an existing comment."""
    content: str = Field(..., min_length=1, max_length=5000)

    model_config = ConfigDict(from_attributes=True)
