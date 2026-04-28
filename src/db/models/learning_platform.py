from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BIGINT, CHAR, DECIMAL, JSON, TIMESTAMP, Boolean, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class RoleName(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    CONTENT_ADMIN = "content_admin"      # Rol 1: admin completo (crear/publicar/editar)
    CONTENT_EDITOR = "content_editor"    # Rol 2: solo editar cursos existentes (no crear ni publicar)
    CONTENT_VIEWER = "content_viewer"    # Rol 3: sin acceso a cursos (solo dashboard)
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


class GemVisibility(str, enum.Enum):
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ORDERING = "ordering"
    MATCHING = "matching"


class QuizAttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"


class CertificationRequestStatus(str, enum.Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    ISSUED = "issued"
    REJECTED = "rejected"


class CourseAccessType(str, enum.Enum):
    free = "free"
    restricted = "restricted"


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
    gems: Mapped[list[Gem]] = relationship(back_populates="area")
    gem_area_links: Mapped[list[GemAreaLink]] = relationship(back_populates="area")


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
    course_assignments_received: Mapped[list[CourseAssignment]] = relationship(
        back_populates="assigned_to_user",
        foreign_keys="CourseAssignment.assigned_to_user_id",
        cascade="all, delete-orphan",
    )
    course_assignments_sent: Mapped[list[CourseAssignment]] = relationship(
        back_populates="assigned_by_user",
        foreign_keys="CourseAssignment.assigned_by_user_id",
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
    sessions: Mapped[list[Session]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    created_gems: Mapped[list[Gem]] = relationship(
        back_populates="created_by_user",
        foreign_keys="Gem.created_by_user_id",
    )
    gem_collection: Mapped[list[UserGemCollection]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    quiz_attempts: Mapped[list[QuizAttempt]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    course_grants: Mapped[list[UserCourseGrant]] = relationship(
        back_populates="user",
        foreign_keys="UserCourseGrant.user_id",
        cascade="all, delete-orphan",
    )
    user_certifications: Mapped[list[UserCertification]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Session(Base):
    """User session for authentication."""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # session_id token
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_expires_at", "expires_at"),
    )


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
        server_default=func.now(),
        onupdate=func.now(),
    )
    access_type: Mapped[CourseAccessType] = mapped_column(
        Enum(CourseAccessType, name="course_access_type_enum", native_enum=False),
        nullable=False,
        server_default=text("'free'"),
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
    assignments: Mapped[list[CourseAssignment]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )
    badge_links: Mapped[list[CourseBadge]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )
    analytics_events: Mapped[list[AnalyticsEvent]] = relationship(back_populates="course")
    gem_links: Mapped[list[CourseGem]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )
    certification: Mapped[CourseCertification | None] = relationship(
        back_populates="course",
        uselist=False,
    )
    course_grants: Mapped[list[UserCourseGrant]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )


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
    gem_links: Mapped[list[LessonGem]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    quiz: Mapped[Quiz | None] = relationship(
        back_populates="lesson",
        uselist=False,
    )


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


class CourseAssignment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "course_assignments"
    __table_args__ = (
        UniqueConstraint(
            "assigned_to_user_id",
            "course_id",
            name="uq_course_assignments_user_course",
        ),
        Index("idx_course_assignments_due_date", "due_date"),
        Index("idx_course_assignments_assigned_by", "assigned_by_user_id"),
    )

    course_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("courses.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    assigned_by_user_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    assigned_to_user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    due_date: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)

    course: Mapped[Course] = relationship(back_populates="assignments")
    assigned_by_user: Mapped[User | None] = relationship(
        back_populates="course_assignments_sent",
        foreign_keys=[assigned_by_user_id],
    )
    assigned_to_user: Mapped[User] = relationship(
        back_populates="course_assignments_received",
        foreign_keys=[assigned_to_user_id],
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
    main_color: Mapped[str] = mapped_column(String(20), nullable=False, server_default="#3b82f6")
    secondary_color: Mapped[str] = mapped_column(String(20), nullable=False, server_default="#1e40af")

    user_badges: Mapped[list[UserBadge]] = relationship(
        back_populates="badge",
        cascade="all, delete-orphan",
    )
    course_badge_links: Mapped[list[CourseBadge]] = relationship(
        back_populates="badge",
        cascade="all, delete-orphan",
    )


class CourseBadge(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "course_badges"
    __table_args__ = (
        UniqueConstraint("course_id", "badge_id", name="uq_course_badges_course_badge"),
    )

    course_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("courses.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    badge_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("badges.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    progress_percentage: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        server_default=text("100.00"),
    )

    course: Mapped[Course] = relationship(back_populates="badge_links")
    badge: Mapped[Badge] = relationship(back_populates="course_badge_links")


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
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    multimedia_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="forum_post_status_enum", native_enum=False),
        nullable=False,
        server_default=text("'draft'"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
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


# ============================================================
# Gem Bank Models
# ============================================================


class GemCategory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "gem_categories"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    gems: Mapped[list[Gem]] = relationship(back_populates="category")


class Gem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "gems"
    __table_args__ = (
        Index("idx_gems_area_status", "area_id", "status"),
        Index("idx_gems_category", "category_id"),
        Index("idx_gems_created_by", "created_by_user_id"),
        Index("idx_gems_featured", "is_featured", "status"),
    )

    category_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("gem_categories.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    area_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("areas.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    created_by_user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    icon_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    gemini_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    conversation_starters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    visibility: Mapped[GemVisibility] = mapped_column(
        Enum(GemVisibility, name="gem_visibility_enum", native_enum=False),
        nullable=False,
        server_default=text("'public'"),
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("0"),
    )
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="gem_status_enum", native_enum=False),
        nullable=False,
        server_default=text("'draft'"),
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    category: Mapped[GemCategory | None] = relationship(back_populates="gems")
    area: Mapped[Area | None] = relationship(back_populates="gems")
    created_by_user: Mapped[User] = relationship(
        back_populates="created_gems",
        foreign_keys=[created_by_user_id],
    )
    tag_links: Mapped[list[GemTagLink]] = relationship(
        back_populates="gem",
        cascade="all, delete-orphan",
    )
    area_links: Mapped[list[GemAreaLink]] = relationship(
        back_populates="gem",
        cascade="all, delete-orphan",
    )
    user_collections: Mapped[list[UserGemCollection]] = relationship(
        back_populates="gem",
        cascade="all, delete-orphan",
    )
    course_links: Mapped[list[CourseGem]] = relationship(
        back_populates="gem",
        cascade="all, delete-orphan",
    )
    lesson_links: Mapped[list[LessonGem]] = relationship(
        back_populates="gem",
        cascade="all, delete-orphan",
    )


class GemTag(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "gem_tags"

    name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)

    gem_links: Mapped[list[GemTagLink]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
    )


class GemTagLink(Base):
    __tablename__ = "gem_tag_links"

    gem_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("gems.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("gem_tags.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    gem: Mapped[Gem] = relationship(back_populates="tag_links")
    tag: Mapped[GemTag] = relationship(back_populates="gem_links")


class UserGemCollection(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_gem_collection"
    __table_args__ = (
        UniqueConstraint("user_id", "gem_id", name="uq_user_gem_collection_user_gem"),
    )

    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    gem_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("gems.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    saved_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="gem_collection")
    gem: Mapped[Gem] = relationship(back_populates="user_collections")


class GemAreaLink(Base):
    __tablename__ = "gem_area_links"

    gem_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("gems.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    area_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("areas.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    gem: Mapped[Gem] = relationship(back_populates="area_links")
    area: Mapped[Area] = relationship(back_populates="gem_area_links")


class CourseGem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "course_gems"
    __table_args__ = (
        UniqueConstraint("course_id", "gem_id", name="uq_course_gems_course_gem"),
    )

    course_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("courses.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    gem_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("gems.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    course: Mapped[Course] = relationship(back_populates="gem_links")
    gem: Mapped[Gem] = relationship(back_populates="course_links")


class LessonGem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "lesson_gems"
    __table_args__ = (
        UniqueConstraint("lesson_id", "gem_id", name="uq_lesson_gems_lesson_gem"),
    )

    lesson_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    gem_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("gems.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    lesson: Mapped[Lesson] = relationship(back_populates="gem_links")
    gem: Mapped[Gem] = relationship(back_populates="lesson_links")


# ============================================================
# Quiz Models
# ============================================================


class Quiz(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "quizzes"

    lesson_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    passing_score: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        server_default=text("70.00"),
    )
    max_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("1"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    lesson: Mapped[Lesson] = relationship(back_populates="quiz")
    questions: Mapped[list[QuizQuestion]] = relationship(
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="QuizQuestion.sort_order",
    )
    attempts: Mapped[list[QuizAttempt]] = relationship(
        back_populates="quiz",
        cascade="all, delete-orphan",
    )


class QuizQuestion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "quiz_questions"
    __table_args__ = (
        UniqueConstraint("quiz_id", "sort_order", name="uq_quiz_questions_quiz_sort"),
    )

    quiz_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("quizzes.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type_enum", native_enum=False),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    points: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        server_default=text("1.00"),
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    quiz: Mapped[Quiz] = relationship(back_populates="questions")
    options: Mapped[list[QuizQuestionOption]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuizQuestionOption.sort_order",
    )


class QuizQuestionOption(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "quiz_question_options"
    __table_args__ = (
        UniqueConstraint("question_id", "sort_order", name="uq_quiz_question_options_question_sort"),
    )

    question_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("quiz_questions.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("0"),
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    match_target: Mapped[str | None] = mapped_column(Text, nullable=True)

    question: Mapped[QuizQuestion] = relationship(back_populates="options")


class QuizAttempt(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        UniqueConstraint("quiz_id", "user_id", "attempt_number", name="uq_quiz_attempts_quiz_user_attempt"),
        Index("idx_quiz_attempts_user_quiz", "user_id", "quiz_id"),
        Index("idx_quiz_attempts_enrollment", "enrollment_id"),
    )

    quiz_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("quizzes.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    enrollment_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("enrollments.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[QuizAttemptStatus] = mapped_column(
        Enum(QuizAttemptStatus, name="quiz_attempt_status_enum", native_enum=False),
        nullable=False,
        server_default=text("'in_progress'"),
    )
    score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    quiz: Mapped[Quiz] = relationship(back_populates="attempts")
    user: Mapped[User] = relationship(back_populates="quiz_attempts")
    enrollment: Mapped[Enrollment] = relationship()
    responses: Mapped[list[QuizAttemptResponse]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
    )


class QuizAttemptResponse(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "quiz_attempt_responses"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_quiz_attempt_responses_attempt_question"),
    )

    attempt_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("quiz_attempts.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("quiz_questions.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    selected_option_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("quiz_question_options.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    text_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordering_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    matching_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    points_earned: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)

    attempt: Mapped[QuizAttempt] = relationship(back_populates="responses")
    question: Mapped[QuizQuestion] = relationship()
    selected_option: Mapped[QuizQuestionOption | None] = relationship()


# ============================================================
# Certification Models
# ============================================================


class CourseCertification(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "course_certifications"

    course_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("courses.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    validity_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    course: Mapped[Course] = relationship(back_populates="certification")
    user_certifications: Mapped[list[UserCertification]] = relationship(
        back_populates="course_certification",
        cascade="all, delete-orphan",
    )


class UserCertification(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "user_certifications"
    __table_args__ = (
        UniqueConstraint("user_id", "course_certification_id", name="uq_user_certifications_user_cert"),
        Index("idx_user_certifications_status", "status"),
        Index("idx_user_certifications_user", "user_id"),
    )

    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    course_certification_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("course_certifications.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    enrollment_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("enrollments.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    status: Mapped[CertificationRequestStatus] = mapped_column(
        Enum(CertificationRequestStatus, name="certification_request_status_enum", native_enum=False),
        nullable=False,
        server_default=text("'requested'"),
    )
    requested_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    approved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    expiration_date: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    certificate_code: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    certificate_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="user_certifications")
    course_certification: Mapped[CourseCertification] = relationship(back_populates="user_certifications")
    enrollment: Mapped[Enrollment] = relationship()


# ============================================================
# Course Access Control
# ============================================================


class UserCourseGrant(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "user_course_grants"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course_grants_user_course"),
        Index("idx_user_course_grants_user", "user_id"),
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
    granted_by_user_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="course_grants",
        foreign_keys=[user_id],
    )
    course: Mapped[Course] = relationship(back_populates="course_grants")
    granted_by_user: Mapped[User | None] = relationship(foreign_keys=[granted_by_user_id])