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