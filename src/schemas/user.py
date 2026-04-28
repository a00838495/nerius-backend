from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class UserProfileRead(UserBase):
    """Enriched user profile with area, roles, and created_at."""
    id: str
    status: str
    area_name: str | None = None
    role_name: str | None = None  # Kept for backward compatibility (primary role)
    role_names: list[str] = []    # All roles assigned to the user
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserStatsRead(BaseModel):
    """Real computed stats for the user profile."""
    completed_courses: int = 0
    total_hours: float = 0
    rank: int | None = None
    badges_count: int = 0
    saved_gems_count: int = 0
    enrolled_courses: int = 0


class UserUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    message: str
    user: UserRead


class CourseRead(BaseModel):
    id: str
    title: str
    description: str | None
    status: str
    estimated_minutes: int | None
    cover_url: str | None

    model_config = ConfigDict(from_attributes=True)


class EnrollmentRead(BaseModel):
    id: str
    course_id: str
    status: str
    progress_percent: float
    completed_at: datetime | None = None
    course: CourseRead | None = None

    model_config = ConfigDict(from_attributes=True)


class CourseAssignmentCreate(BaseModel):
    course_id: str
    assigned_to_user_id: str
    due_date: datetime


class CourseAssignmentRead(BaseModel):
    id: str
    course_id: str
    assigned_by_user_id: str | None
    assigned_to_user_id: str
    due_date: str
    created_at: str
    assigned_by_name: str | None = None
    course: CourseRead | None = None

    model_config = ConfigDict(from_attributes=True)


# Schemas for detailed course view
class LessonResourceRead(BaseModel):
    id: str
    resource_type: str
    title: str
    external_url: str
    thumbnail_url: str | None
    duration_seconds: int | None

    model_config = ConfigDict(from_attributes=True)


class LessonProgressRead(BaseModel):
    lesson_id: str
    status: str
    progress_percent: float
    time_spent_seconds: int
    completed_at: str | None = None
    last_activity_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class LessonBasicRead(BaseModel):
    id: str
    title: str
    sort_order: int
    estimated_minutes: int | None

    model_config = ConfigDict(from_attributes=True)


class LessonWithProgressRead(LessonBasicRead):
    """Lesson with progress information but without resources."""
    status: str  # not_started, in_progress, completed
    progress_percent: float
    has_quiz: bool = False

    model_config = ConfigDict(from_attributes=True)


class LessonDetailedRead(LessonBasicRead):
    """Full lesson details with resources and progress."""
    description: str | None
    resources: list[LessonResourceRead] = []
    progress: LessonProgressRead | None = None

    model_config = ConfigDict(from_attributes=True)


class ModuleBasicRead(BaseModel):
    id: str
    title: str
    sort_order: int
    lessons: list[LessonBasicRead] = []

    model_config = ConfigDict(from_attributes=True)


class ModuleWithProgressRead(BaseModel):
    """Module with lessons including progress."""
    id: str
    title: str
    sort_order: int
    lessons: list[LessonWithProgressRead] = []

    model_config = ConfigDict(from_attributes=True)


class ModuleDetailedRead(BaseModel):
    id: str
    title: str
    sort_order: int
    lessons: list[LessonDetailedRead] = []

    model_config = ConfigDict(from_attributes=True)


class CourseDetailedRead(BaseModel):
    """Course with all modules and lessons including progress."""
    id: str
    title: str
    description: str | None
    status: str
    estimated_minutes: int | None
    cover_url: str | None
    enrollment: EnrollmentRead | None = None
    modules: list[ModuleWithProgressRead] = []

    model_config = ConfigDict(from_attributes=True)


class LessonProgressUpdate(BaseModel):
    progress_percent: float
    time_spent_seconds: int
    status: str  # not_started, in_progress, completed


class BadgeRead(BaseModel):
    id: str
    name: str
    description: str | None = None
    icon_url: str | None = None
    main_color: str
    secondary_color: str

    model_config = ConfigDict(from_attributes=True)


class EarnedBadgeNotification(BaseModel):
    badge: BadgeRead
    awarded_at: str


class UserBadgeRead(BaseModel):
    id: str
    badge: BadgeRead
    awarded_at: str

    model_config = ConfigDict(from_attributes=True)


class AreaRead(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class CourseCardRead(BaseModel):
    """Course summary for card display — no module/lesson list, only counts."""
    id: str
    title: str
    description: str | None
    status: str
    estimated_minutes: int | None
    cover_url: str | None
    area: AreaRead | None = None
    created_by_name: str
    modules_count: int
    lessons_count: int
    total_enrolled: int
    total_completed: int
    is_enrolled: bool
    enrollment: EnrollmentRead | None = None
    has_certification: bool = False

    model_config = ConfigDict(from_attributes=True)


class CourseRankingRead(BaseModel):
    name: str
    total_completed_courses: int
    area: str


class LessonProgressUpdateResponse(BaseModel):
    lesson_id: str
    status: str
    progress_percent: float
    time_spent_seconds: int
    enrollment_progress_percent: float
    earned_badges: list[EarnedBadgeNotification] = []
    quiz_required: bool = False