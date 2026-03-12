"""Forum schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


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
    author: UserBasicRead
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    comments_count: int = 0

    model_config = ConfigDict(from_attributes=True)
