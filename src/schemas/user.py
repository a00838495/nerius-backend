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

    model_config = ConfigDict(from_attributes=True)


class LessonBasicRead(BaseModel):
    id: str
    title: str
    sort_order: int
    estimated_minutes: int | None

    model_config = ConfigDict(from_attributes=True)


class LessonDetailedRead(LessonBasicRead):
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


class ModuleDetailedRead(BaseModel):
    id: str
    title: str
    sort_order: int
    lessons: list[LessonDetailedRead] = []

    model_config = ConfigDict(from_attributes=True)


class CourseDetailedRead(BaseModel):
    id: str
    title: str
    description: str | None
    status: str
    estimated_minutes: int | None
    cover_url: str | None
    enrollment: EnrollmentRead | None = None
    first_module: ModuleDetailedRead | None = None
    other_modules: list[ModuleBasicRead] = []

    model_config = ConfigDict(from_attributes=True)


class LessonProgressUpdate(BaseModel):
    progress_percent: float
    time_spent_seconds: int
    status: str  # not_started, in_progress, completed


class LessonProgressUpdateResponse(BaseModel):
    lesson_id: str
    status: str
    progress_percent: float
    time_spent_seconds: int
    enrollment_progress_percent: float