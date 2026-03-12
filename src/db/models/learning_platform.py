from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BIGINT, CHAR, DECIMAL, JSON, TIMESTAMP, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class RoleName(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    CONTENT_ADMIN = "content_admin"
    LEARNER = "learner"


class PublicationStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ResourceType(str, enum.Enum):
    VIDEO = "video"
    PDF = "pdf"
    PODCAST = "podcast"
    SLIDE = "slide"


class EnrollmentStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    dropped = "dropped"


class LessonProgressStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class UUIDPrimaryKeyMixin:
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class Area(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "areas"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    users: Mapped[list[User]] = relationship(back_populates="area")
    courses: Mapped[list[Course]] = relationship(back_populates="area")
    forum_posts: Mapped[list[ForumPost]] = relationship(back_populates="area")
    analytics_events: Mapped[list[AnalyticsEvent]] = relationship(back_populates="area")


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    area_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("areas.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status_enum", native_enum=False),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    area: Mapped[Area | None] = relationship(back_populates="users")
    user_role_links: Mapped[list[UserRole]] = relationship(
        back_populates="user",
        foreign_keys="UserRole.user_id",
        cascade="all, delete-orphan",
    )
    assigned_role_links: Mapped[list[UserRole]] = relationship(
        back_populates="assigned_by_user",
        foreign_keys="UserRole.assigned_by_user_id",
    )
    created_courses: Mapped[list[Course]] = relationship(
        back_populates="created_by_user",
        foreign_keys="Course.created_by_user_id",
    )
    enrollments: Mapped[list[Enrollment]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    badge_awards: Mapped[list[UserBadge]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    forum_posts: Mapped[list[ForumPost]] = relationship(
        back_populates="author",
        foreign_keys="ForumPost.author_user_id",
        cascade="all, delete-orphan",
    )
    forum_comments: Mapped[list[ForumComment]] = relationship(
        back_populates="author",
        foreign_keys="ForumComment.author_user_id",
        cascade="all, delete-orphan",
    )
    analytics_events: Mapped[list[AnalyticsEvent]] = relationship(back_populates="user")


class Role(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "roles"

    name: Mapped[RoleName] = mapped_column(
        Enum(RoleName, name="role_name_enum", native_enum=False),
        nullable=False,
        unique=True,
    )

    user_role_links: Mapped[list[UserRole]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )


class UserRole(CreatedAtMixin, Base):
    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("roles.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    assigned_by_user_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="user_role_links",
        foreign_keys=[user_id],
    )
    role: Mapped[Role] = relationship(back_populates="user_role_links")
    assigned_by_user: Mapped[User | None] = relationship(
        back_populates="assigned_role_links",
        foreign_keys=[assigned_by_user_id],
    )


class Course(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "courses"

    area_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("areas.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="course_status_enum", native_enum=False),
        nullable=False,
        server_default=text("'draft'"),
    )
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    area: Mapped[Area | None] = relationship(back_populates="courses")
    created_by_user: Mapped[User] = relationship(
        back_populates="created_courses",
        foreign_keys=[created_by_user_id],
    )
    modules: Mapped[list[CourseModule]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseModule.sort_order",
    )
    enrollments: Mapped[list[Enrollment]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )
    analytics_events: Mapped[list[AnalyticsEvent]] = relationship(back_populates="course")


class CourseModule(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "course_modules"
    __table_args__ = (
        UniqueConstraint("course_id", "sort_order", name="uq_course_modules_course_sort"),
    )

    course_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("courses.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    course: Mapped[Course] = relationship(back_populates="modules")
    lessons: Mapped[list[Lesson]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Lesson.sort_order",
    )


class Lesson(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("module_id", "sort_order", name="uq_lessons_module_sort"),
    )

    module_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("course_modules.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    module: Mapped[CourseModule] = relationship(back_populates="lessons")
    resources: Mapped[list[LessonResource]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    lesson_progress_entries: Mapped[list[LessonProgress]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    analytics_events: Mapped[list[AnalyticsEvent]] = relationship(back_populates="lesson")


class LessonResource(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "lesson_resources"

    lesson_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType, name="lesson_resource_type_enum", native_enum=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    external_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resource_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    lesson: Mapped[Lesson] = relationship(back_populates="resources")


class Enrollment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_enrollments_user_course"),
    )

    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("courses.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, name="enrollment_status_enum", native_enum=False),
        nullable=False,
        server_default=text("'active'"),
    )
    progress_percent: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        server_default=text("0"),
    )
    score: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    user: Mapped[User] = relationship(back_populates="enrollments")
    course: Mapped[Course] = relationship(back_populates="enrollments")
    lesson_progress_entries: Mapped[list[LessonProgress]] = relationship(
        back_populates="enrollment",
        cascade="all, delete-orphan",
    )


class LessonProgress(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint(
            "enrollment_id",
            "lesson_id",
            name="uq_lesson_progress_enrollment_lesson",
        ),
    )

    enrollment_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("enrollments.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    lesson_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    status: Mapped[LessonProgressStatus] = mapped_column(
        Enum(LessonProgressStatus, name="lesson_progress_status_enum", native_enum=False),
        nullable=False,
        server_default=text("'not_started'"),
    )
    progress_percent: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        server_default=text("0"),
    )
    time_spent_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    enrollment: Mapped[Enrollment] = relationship(back_populates="lesson_progress_entries")
    lesson: Mapped[Lesson] = relationship(back_populates="lesson_progress_entries")


class Badge(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "badges"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_badges: Mapped[list[UserBadge]] = relationship(
        back_populates="badge",
        cascade="all, delete-orphan",
    )


class UserBadge(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_badges"
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badges_user_badge"),
    )

    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    badge_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("badges.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    awarded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped[User] = relationship(back_populates="badge_awards")
    badge: Mapped[Badge] = relationship(back_populates="user_badges")


class ForumPost(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "forum_posts"
    __table_args__ = (
        Index("idx_forum_posts_area_status", "area_id", "status"),
        Index("idx_forum_posts_author", "author_user_id"),
    )

    area_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("areas.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    author_user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="forum_post_status_enum", native_enum=False),
        nullable=False,
        server_default=text("'draft'"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    area: Mapped[Area | None] = relationship(back_populates="forum_posts")
    author: Mapped[User] = relationship(
        back_populates="forum_posts",
        foreign_keys=[author_user_id],
    )
    comments: Mapped[list[ForumComment]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )


class ForumComment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "forum_comments"

    post_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("forum_posts.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    author_user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    parent_comment_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("forum_comments.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
        server_default=text("NULL"),
    )

    post: Mapped[ForumPost] = relationship(back_populates="comments")
    author: Mapped[User] = relationship(
        back_populates="forum_comments",
        foreign_keys=[author_user_id],
    )
    parent_comment: Mapped[ForumComment | None] = relationship(
        back_populates="replies",
        remote_side="ForumComment.id",
    )
    replies: Mapped[list[ForumComment]] = relationship(back_populates="parent_comment")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (
        Index("idx_analytics_events_user", "user_id"),
        Index("idx_analytics_events_area", "area_id"),
        Index("idx_analytics_events_course", "course_id"),
        Index("idx_analytics_events_lesson", "lesson_id"),
        Index("idx_analytics_events_name_time", "event_name", "event_time"),
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    area_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("areas.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    course_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("courses.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    lesson_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    event_time: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    user: Mapped[User | None] = relationship(back_populates="analytics_events")
    area: Mapped[Area | None] = relationship(back_populates="analytics_events")
    course: Mapped[Course | None] = relationship(back_populates="analytics_events")
    lesson: Mapped[Lesson | None] = relationship(back_populates="analytics_events")