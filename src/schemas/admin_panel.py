"""Pydantic schemas for the admin panel modules.

Single file to keep imports tidy across the admin_panel/ subpackage.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# =============================================================================
# 1. DASHBOARD
# =============================================================================


class DashboardCounters(BaseModel):
    total_users: int
    active_users: int
    total_courses: int
    published_courses: int
    total_enrollments: int
    completed_enrollments: int
    total_areas: int
    total_certifications_issued: int
    total_forum_posts: int
    total_gems: int
    total_badges_earned: int
    new_users_last_7d: int
    new_enrollments_last_7d: int


class DashboardCoursePopularity(BaseModel):
    course_id: str
    title: str
    enrollments: int
    completed: int
    completion_rate: float


class DashboardCompletionByArea(BaseModel):
    area_id: str | None
    area_name: str
    enrollments: int
    completed: int
    completion_rate: float


class DashboardActivityBucket(BaseModel):
    date: str
    enrollments: int
    completions: int
    new_users: int


class DashboardOverview(BaseModel):
    counters: DashboardCounters
    popular_courses: list[DashboardCoursePopularity]
    completion_by_area: list[DashboardCompletionByArea]
    activity_last_30d: list[DashboardActivityBucket]


# =============================================================================
# 2. USERS MANAGEMENT (learners y otros)
# =============================================================================


class UserAdminRead(BaseModel):
    """Full user detail for the admin panel."""
    id: str
    first_name: str
    last_name: str
    email: str
    status: str
    gender: str | None = None
    area_id: str | None = None
    area_name: str | None = None
    roles: list[str] = []
    is_admin: bool = False
    last_login_at: datetime | None = None
    created_at: datetime
    enrollments_count: int = 0
    completed_courses_count: int = 0
    badges_count: int = 0
    certifications_count: int = 0


class UserAdminListItem(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    status: str
    area_name: str | None = None
    roles: list[str] = []
    last_login_at: datetime | None = None
    created_at: datetime
    enrollments_count: int = 0


class UserAdminList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserAdminListItem]


class UserAdminCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    gender: str | None = Field(None, max_length=30)
    area_id: str | None = None


class UserAdminUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    gender: str | None = Field(None, max_length=30)
    area_id: str | None = None


class UserStatusUpdate(BaseModel):
    status: str = Field(..., description="active | inactive | suspended")


class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=100)


class PasswordResetResponse(BaseModel):
    user_id: str
    message: str


# =============================================================================
# 3. AREAS MANAGEMENT
# =============================================================================


class AreaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class AreaUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class AreaAdminRead(BaseModel):
    id: str
    name: str
    created_at: datetime
    users_count: int = 0
    courses_count: int = 0
    forum_posts_count: int = 0


# =============================================================================
# 4. ASSIGNMENTS (Asignaciones masivas de cursos)
# =============================================================================


class BulkAssignmentRequest(BaseModel):
    course_id: str
    due_date: datetime
    user_ids: list[str] | None = None
    area_ids: list[str] | None = None
    notify: bool = False  # Reservado: enviar notificación (no implementado por ahora)


class BulkAssignmentResult(BaseModel):
    created: int
    skipped_already_assigned: int
    skipped_not_found: int
    course_id: str
    due_date: datetime
    affected_user_ids: list[str]


class CourseAssignmentRow(BaseModel):
    id: str
    course_id: str
    course_title: str
    user_id: str
    user_full_name: str
    user_email: str
    area_name: str | None = None
    due_date: datetime
    assigned_by_user_id: str | None
    assigned_by_user_name: str | None = None
    created_at: datetime
    progress_percent: float = 0.0
    enrollment_status: str | None = None
    is_overdue: bool = False


class CourseAssignmentList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[CourseAssignmentRow]


class AssignmentProgressSummary(BaseModel):
    course_id: str
    course_title: str
    total_assigned: int
    not_started: int
    in_progress: int
    completed: int
    overdue: int
    avg_progress: float


# =============================================================================
# 5. FORUM MODERATION
# =============================================================================


class ForumPostAdminRead(BaseModel):
    id: str
    title: str
    content: str
    multimedia_url: str | None
    status: str
    author_id: str
    author_email: str
    author_full_name: str
    area_id: str | None
    area_name: str | None
    comments_count: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class ForumPostAdminList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ForumPostAdminRead]


class ForumPostStatusUpdate(BaseModel):
    status: str = Field(..., description="draft | published | archived")


class ForumPostUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=180)
    content: str | None = Field(None, min_length=1)
    multimedia_url: str | None = None


class ForumCommentAdminRead(BaseModel):
    id: str
    post_id: str
    post_title: str
    parent_comment_id: str | None
    content: str
    author_id: str
    author_email: str
    author_full_name: str
    created_at: datetime
    updated_at: datetime | None


class ForumCommentAdminList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ForumCommentAdminRead]


class ForumStats(BaseModel):
    total_posts: int
    published_posts: int
    draft_posts: int
    archived_posts: int
    total_comments: int
    posts_last_7d: int
    posts_without_comments: int
    top_authors: list[dict[str, Any]]


# =============================================================================
# 6. GEMS GLOBAL
# =============================================================================


class GemAdminListItem(BaseModel):
    id: str
    title: str
    description: str | None
    icon_url: str | None
    visibility: str
    status: str
    is_featured: bool
    usage_count: int
    saved_count: int = 0
    category_id: str | None
    category_name: str | None
    area_id: str | None
    area_name: str | None
    created_by_user_id: str
    created_by_user_name: str
    created_at: datetime
    updated_at: datetime
    tags: list[str] = []


class GemAdminList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[GemAdminListItem]


class GemAdminCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=180)
    description: str | None = None
    instructions: str = Field(..., min_length=1)
    icon_url: str | None = None
    gemini_url: str | None = None
    conversation_starters: list[str] | None = None
    visibility: str = "public"
    is_featured: bool = False
    status: str = "draft"
    category_id: str | None = None
    area_id: str | None = None
    tag_ids: list[str] = Field(default_factory=list)


class GemAdminUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=180)
    description: str | None = None
    instructions: str | None = Field(None, min_length=1)
    icon_url: str | None = None
    gemini_url: str | None = None
    conversation_starters: list[str] | None = None
    visibility: str | None = None
    is_featured: bool | None = None
    status: str | None = None
    category_id: str | None = None
    area_id: str | None = None
    tag_ids: list[str] | None = None


class GemCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = None
    icon: str | None = Field(None, max_length=50)
    sort_order: int = 0


class GemCategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = None
    icon: str | None = Field(None, max_length=50)
    sort_order: int | None = None


class GemCategoryRead(BaseModel):
    id: str
    name: str
    description: str | None
    icon: str | None
    sort_order: int
    gems_count: int = 0


class GemTagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=60)


class GemTagRead(BaseModel):
    id: str
    name: str
    gems_count: int = 0


# =============================================================================
# 7. BADGES GLOBAL
# =============================================================================


class BadgeAdminCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = None
    icon_url: str | None = None
    main_color: str = Field("#3b82f6", max_length=20)
    secondary_color: str = Field("#1e40af", max_length=20)


class BadgeAdminUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = None
    icon_url: str | None = None
    main_color: str | None = Field(None, max_length=20)
    secondary_color: str | None = Field(None, max_length=20)


class BadgeAdminRead(BaseModel):
    id: str
    name: str
    description: str | None
    icon_url: str | None
    main_color: str
    secondary_color: str
    awarded_count: int = 0
    courses_linked: int = 0
    created_at: datetime


class BadgeAwardItem(BaseModel):
    id: str
    user_id: str
    user_full_name: str
    user_email: str
    awarded_at: datetime


# =============================================================================
# 8. CERTIFICATIONS ADMIN
# =============================================================================


class UserCertificationAdminRead(BaseModel):
    id: str
    user_id: str
    user_full_name: str
    user_email: str
    course_certification_id: str
    certification_title: str
    course_id: str
    course_title: str
    status: str
    requested_at: datetime
    approved_at: datetime | None
    issued_at: datetime | None
    rejected_at: datetime | None
    rejection_reason: str | None
    expiration_date: datetime | None
    certificate_code: str | None
    certificate_url: str | None


class UserCertificationAdminList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserCertificationAdminRead]


class CertificationApproveRequest(BaseModel):
    issue_now: bool = True
    expiration_date: datetime | None = None
    certificate_url: str | None = None


class CertificationRejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class CertificationStats(BaseModel):
    total_requested: int
    total_approved: int
    total_issued: int
    total_rejected: int
    avg_approval_time_hours: float | None = None


# =============================================================================
# 9. REPORTS
# =============================================================================


class CourseProgressReportRow(BaseModel):
    course_id: str
    course_title: str
    area_name: str | None
    total_enrolled: int
    completed: int
    in_progress: int
    not_started: int
    completion_rate: float
    avg_progress: float
    avg_score: float | None


class UserProgressReportRow(BaseModel):
    user_id: str
    full_name: str
    email: str
    area_name: str | None
    total_enrollments: int
    completed: int
    in_progress: int
    avg_progress: float
    badges_count: int
    certifications_count: int
    last_activity_at: datetime | None


class QuizReportRow(BaseModel):
    quiz_id: str
    lesson_title: str
    course_title: str
    total_attempts: int
    passed: int
    failed: int
    pass_rate: float
    avg_score: float | None
    hardest_question_id: str | None
    hardest_question_text: str | None
    hardest_question_fail_rate: float | None


# =============================================================================
# 10. ENROLLMENTS
# =============================================================================


class EnrollmentAdminRead(BaseModel):
    id: str
    user_id: str
    user_full_name: str
    user_email: str
    course_id: str
    course_title: str
    status: str
    progress_percent: float
    score: float | None
    started_at: datetime | None
    completed_at: datetime | None
    last_activity_at: datetime | None
    created_at: datetime


class EnrollmentAdminList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[EnrollmentAdminRead]


class EnrollmentStatusUpdate(BaseModel):
    status: str = Field(..., description="active | completed | dropped")
