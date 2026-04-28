"""Admin panel routes for course management.

All endpoints here require content_admin or super_admin role.
Mounted at /admin prefix.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from src.core.permissions import (
    require_admin,
    require_course_reader,
    require_course_editor,
    require_course_publisher,
    require_super_admin,
)
from src.db.session import get_db
from src.db.models.learning_platform import (
    User, Course, CourseModule, Lesson, LessonResource, Enrollment, Area,
    PublicationStatus, CourseAccessType, ResourceType,
    Quiz, QuizQuestion, QuizQuestionOption, QuestionType,
    Badge, CourseBadge,
    Gem, CourseGem, LessonGem,
    CourseCertification,
    UserCourseGrant,
    Role, UserRole, RoleName,
)
from src.schemas.admin import (
    CourseAdminCreate, CourseAdminUpdate, CourseAdminRead,
    CourseAreaMini, CourseCreatorMini,
    ModuleCreate, ModuleUpdate, ModuleReorder, ModuleAdminRead,
    LessonAdminCreate, LessonAdminUpdate, LessonReorder, LessonAdminRead,
    ResourceAdminCreate, ResourceAdminUpdate, ResourceAdminRead,
    QuizAdminCreate, QuizAdminUpdate,
    QuestionAdminCreate, QuestionAdminUpdate, QuestionReorder,
    OptionsBulkReplace,
    BadgeMini, CourseBadgeLinkCreate, CourseBadgeLinkUpdate, CourseBadgeLinkRead,
    GemLinkCreate, GemMini, CourseGemLinkRead, LessonGemLinkRead,
    CertificationAdminCreate, CertificationAdminUpdate, CertificationAdminRead,
    GrantCreate, GrantAdminRead, GrantUserMini,
    UserWithRolesRead, SetAdminRoleRequest,
)

router = APIRouter(tags=["admin"], prefix="/admin")


def _course_to_admin_read(course: Course, db: Session) -> CourseAdminRead:
    modules_count = db.query(func.count(CourseModule.id)).filter(CourseModule.course_id == course.id).scalar() or 0
    lessons_count = (
        db.query(func.count(Lesson.id))
        .join(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(CourseModule.course_id == course.id)
        .scalar() or 0
    )
    total_enrolled = db.query(func.count(Enrollment.id)).filter(Enrollment.course_id == course.id).scalar() or 0
    total_completed = (
        db.query(func.count(Enrollment.id))
        .filter(Enrollment.course_id == course.id, Enrollment.status == "completed")
        .scalar() or 0
    )
    return CourseAdminRead(
        id=course.id,
        title=course.title,
        description=course.description,
        status=course.status.value,
        access_type=course.access_type.value,
        estimated_minutes=course.estimated_minutes,
        cover_url=course.cover_url,
        created_at=course.created_at,
        updated_at=course.updated_at,
        area=CourseAreaMini(id=course.area.id, name=course.area.name) if course.area else None,
        created_by_user=CourseCreatorMini(
            id=course.created_by_user.id,
            first_name=course.created_by_user.first_name,
            last_name=course.created_by_user.last_name,
        ),
        modules_count=modules_count,
        lessons_count=lessons_count,
        total_enrolled=total_enrolled,
        total_completed=total_completed,
    )


# ============================================================
# Course CRUD
# ============================================================


@router.get("/courses", response_model=list[CourseAdminRead])
def list_courses_admin(
    status: str | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search in title"),
    area_id: str | None = Query(None),
    current_user: User = Depends(require_course_reader),
    db: Session = Depends(get_db),
):
    """List ALL courses (any status) for admin management."""
    query = db.query(Course).options(
        joinedload(Course.area),
        joinedload(Course.created_by_user),
    )
    if status:
        try:
            query = query.filter(Course.status == PublicationStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if search:
        query = query.filter(Course.title.ilike(f"%{search}%"))
    if area_id:
        query = query.filter(Course.area_id == area_id)

    courses = query.order_by(Course.updated_at.desc()).all()
    return [_course_to_admin_read(c, db) for c in courses]


@router.post("/courses", response_model=CourseAdminRead, status_code=201)
def create_course(
    body: CourseAdminCreate,
    current_user: User = Depends(require_course_publisher),
    db: Session = Depends(get_db),
):
    """Create a new course shell (defaults to draft)."""
    try:
        status_enum = PublicationStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")
    try:
        access_enum = CourseAccessType(body.access_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid access_type: {body.access_type}")

    if body.area_id:
        area = db.query(Area).filter(Area.id == body.area_id).first()
        if not area:
            raise HTTPException(status_code=404, detail="Area not found")

    course = Course(
        id=str(uuid.uuid4()),
        title=body.title,
        description=body.description,
        area_id=body.area_id,
        cover_url=body.cover_url,
        estimated_minutes=body.estimated_minutes,
        access_type=access_enum,
        status=status_enum,
        created_by_user_id=current_user.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    # Eager-load relations for response
    db.refresh(course, attribute_names=["area", "created_by_user"])
    return _course_to_admin_read(course, db)


def _validate_publish_requirements(course: Course, db: Session) -> None:
    """Ensure the course has at least 1 module with 1 lesson before publishing."""
    modules = db.query(CourseModule).filter(CourseModule.course_id == course.id).all()
    if not modules:
        raise HTTPException(status_code=400, detail="El curso debe tener al menos 1 módulo para publicarse")
    for m in modules:
        lesson_count = db.query(func.count(Lesson.id)).filter(Lesson.module_id == m.id).scalar()
        if lesson_count and lesson_count > 0:
            return
    raise HTTPException(status_code=400, detail="El curso debe tener al menos 1 lección para publicarse")


@router.put("/courses/{course_id}", response_model=CourseAdminRead)
def update_course(
    course_id: str,
    body: CourseAdminUpdate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    from src.core.permissions import _user_has_any_role, COURSE_PUBLISHER_ROLES
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Validate before mutation
    if body.status is not None:
        try:
            new_status = PublicationStatus(body.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")
        # Publishing/unpublishing/archiving requires publisher role
        if new_status != course.status:
            if not _user_has_any_role(db, current_user.id, COURSE_PUBLISHER_ROLES):
                raise HTTPException(
                    status_code=403,
                    detail="Solo administradores de contenido pueden cambiar el estado de publicación",
                )
        # Gating: require content before publish
        if new_status == PublicationStatus.PUBLISHED and course.status != PublicationStatus.PUBLISHED:
            _validate_publish_requirements(course, db)
        course.status = new_status

    if body.access_type is not None:
        try:
            course.access_type = CourseAccessType(body.access_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid access_type: {body.access_type}")

    if body.area_id is not None:
        if body.area_id:
            area = db.query(Area).filter(Area.id == body.area_id).first()
            if not area:
                raise HTTPException(status_code=404, detail="Area not found")
        course.area_id = body.area_id or None

    for field in ("title", "description", "cover_url", "estimated_minutes"):
        val = getattr(body, field)
        if val is not None:
            setattr(course, field, val)

    db.commit()
    db.refresh(course)
    db.refresh(course, attribute_names=["area", "created_by_user"])
    return _course_to_admin_read(course, db)


@router.delete("/courses/{course_id}", status_code=204)
def delete_course(
    course_id: str,
    current_user: User = Depends(require_course_publisher),
    db: Session = Depends(get_db),
):
    """Soft delete: sets status=archived. Never hard deletes."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.status = PublicationStatus.ARCHIVED
    db.commit()
    return None


@router.get("/courses/{course_id}", response_model=CourseAdminRead)
def get_course_admin(
    course_id: str,
    current_user: User = Depends(require_course_reader),
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .options(joinedload(Course.area), joinedload(Course.created_by_user))
        .filter(Course.id == course_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return _course_to_admin_read(course, db)


# ============================================================
# Module CRUD
# ============================================================


def _module_to_read(module: CourseModule, db: Session) -> ModuleAdminRead:
    lessons_count = db.query(func.count(Lesson.id)).filter(Lesson.module_id == module.id).scalar() or 0
    return ModuleAdminRead(
        id=module.id,
        course_id=module.course_id,
        title=module.title,
        sort_order=module.sort_order,
        lessons_count=lessons_count,
    )


@router.get("/courses/{course_id}/modules", response_model=list[ModuleAdminRead])
def list_modules(
    course_id: str,
    current_user: User = Depends(require_course_reader),
    db: Session = Depends(get_db),
):
    modules = (
        db.query(CourseModule)
        .filter(CourseModule.course_id == course_id)
        .order_by(CourseModule.sort_order)
        .all()
    )
    return [_module_to_read(m, db) for m in modules]


@router.post("/courses/{course_id}/modules", response_model=ModuleAdminRead, status_code=201)
def create_module(
    course_id: str,
    body: ModuleCreate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    max_sort = (
        db.query(func.max(CourseModule.sort_order))
        .filter(CourseModule.course_id == course_id)
        .scalar() or 0
    )
    module = CourseModule(
        id=str(uuid.uuid4()),
        course_id=course_id,
        title=body.title,
        sort_order=max_sort + 1,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return _module_to_read(module, db)


@router.put("/modules/{module_id}", response_model=ModuleAdminRead)
def update_module(
    module_id: str,
    body: ModuleUpdate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    module = db.query(CourseModule).filter(CourseModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    if body.title is not None:
        module.title = body.title
    db.commit()
    db.refresh(module)
    return _module_to_read(module, db)


@router.delete("/modules/{module_id}", status_code=204)
def delete_module(
    module_id: str,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    module = db.query(CourseModule).filter(CourseModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    db.delete(module)
    db.commit()
    return None


@router.post("/courses/{course_id}/modules/reorder", status_code=204)
def reorder_modules(
    course_id: str,
    body: ModuleReorder,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    """Reorder modules atomically. Uses a 2-pass update to avoid unique constraint conflicts."""
    modules = db.query(CourseModule).filter(CourseModule.course_id == course_id).all()
    mod_map = {m.id: m for m in modules}
    # Validate all IDs belong to this course
    for mid in body.module_ids:
        if mid not in mod_map:
            raise HTTPException(status_code=400, detail=f"Module {mid} not in course")
    # Pass 1: assign negative temp sort_order to avoid conflicts
    for i, mid in enumerate(body.module_ids):
        mod_map[mid].sort_order = -(i + 1)
    db.flush()
    # Pass 2: final sort_order
    for i, mid in enumerate(body.module_ids):
        mod_map[mid].sort_order = i + 1
    db.commit()
    return None


# ============================================================
# Lesson CRUD
# ============================================================


def _lesson_to_read(lesson: Lesson, db: Session) -> LessonAdminRead:
    has_quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson.id).first() is not None
    resources_count = db.query(func.count(LessonResource.id)).filter(LessonResource.lesson_id == lesson.id).scalar() or 0
    return LessonAdminRead(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        description=lesson.description,
        sort_order=lesson.sort_order,
        estimated_minutes=lesson.estimated_minutes,
        has_quiz=has_quiz,
        resources_count=resources_count,
    )


@router.get("/modules/{module_id}/lessons", response_model=list[LessonAdminRead])
def list_lessons(
    module_id: str,
    current_user: User = Depends(require_course_reader),
    db: Session = Depends(get_db),
):
    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).order_by(Lesson.sort_order).all()
    return [_lesson_to_read(l, db) for l in lessons]


@router.post("/modules/{module_id}/lessons", response_model=LessonAdminRead, status_code=201)
def create_lesson(
    module_id: str,
    body: LessonAdminCreate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    module = db.query(CourseModule).filter(CourseModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    max_sort = db.query(func.max(Lesson.sort_order)).filter(Lesson.module_id == module_id).scalar() or 0
    lesson = Lesson(
        id=str(uuid.uuid4()),
        module_id=module_id,
        title=body.title,
        description=body.description,
        estimated_minutes=body.estimated_minutes,
        sort_order=max_sort + 1,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return _lesson_to_read(lesson, db)


@router.put("/lessons/{lesson_id}", response_model=LessonAdminRead)
def update_lesson(
    lesson_id: str,
    body: LessonAdminUpdate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    for field in ("title", "description", "estimated_minutes"):
        val = getattr(body, field)
        if val is not None:
            setattr(lesson, field, val)
    db.commit()
    db.refresh(lesson)
    return _lesson_to_read(lesson, db)


@router.delete("/lessons/{lesson_id}", status_code=204)
def delete_lesson(
    lesson_id: str,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    db.delete(lesson)
    db.commit()
    return None


@router.post("/modules/{module_id}/lessons/reorder", status_code=204)
def reorder_lessons(
    module_id: str,
    body: LessonReorder,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).all()
    lesson_map = {l.id: l for l in lessons}
    for lid in body.lesson_ids:
        if lid not in lesson_map:
            raise HTTPException(status_code=400, detail=f"Lesson {lid} not in module")
    for i, lid in enumerate(body.lesson_ids):
        lesson_map[lid].sort_order = -(i + 1)
    db.flush()
    for i, lid in enumerate(body.lesson_ids):
        lesson_map[lid].sort_order = i + 1
    db.commit()
    return None


# ============================================================
# Resource CRUD
# ============================================================


@router.get("/lessons/{lesson_id}/resources", response_model=list[ResourceAdminRead])
def list_resources(
    lesson_id: str,
    current_user: User = Depends(require_course_reader),
    db: Session = Depends(get_db),
):
    resources = db.query(LessonResource).filter(LessonResource.lesson_id == lesson_id).all()
    return [
        ResourceAdminRead(
            id=r.id,
            lesson_id=r.lesson_id,
            resource_type=r.resource_type.value,
            title=r.title,
            external_url=r.external_url,
            thumbnail_url=r.thumbnail_url,
            duration_seconds=r.duration_seconds,
        )
        for r in resources
    ]


@router.post("/lessons/{lesson_id}/resources", response_model=ResourceAdminRead, status_code=201)
def create_resource(
    lesson_id: str,
    body: ResourceAdminCreate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    try:
        rtype = ResourceType(body.resource_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid resource_type: {body.resource_type}")
    resource = LessonResource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        resource_type=rtype,
        title=body.title,
        external_url=body.external_url,
        thumbnail_url=body.thumbnail_url,
        duration_seconds=body.duration_seconds,
        resource_metadata=body.resource_metadata,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return ResourceAdminRead(
        id=resource.id, lesson_id=resource.lesson_id,
        resource_type=resource.resource_type.value, title=resource.title,
        external_url=resource.external_url, thumbnail_url=resource.thumbnail_url,
        duration_seconds=resource.duration_seconds,
    )


@router.put("/resources/{resource_id}", response_model=ResourceAdminRead)
def update_resource(
    resource_id: str,
    body: ResourceAdminUpdate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    resource = db.query(LessonResource).filter(LessonResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if body.resource_type is not None:
        try:
            resource.resource_type = ResourceType(body.resource_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid resource_type: {body.resource_type}")
    for field in ("title", "external_url", "thumbnail_url", "duration_seconds", "resource_metadata"):
        val = getattr(body, field)
        if val is not None:
            setattr(resource, field, val)
    db.commit()
    db.refresh(resource)
    return ResourceAdminRead(
        id=resource.id, lesson_id=resource.lesson_id,
        resource_type=resource.resource_type.value, title=resource.title,
        external_url=resource.external_url, thumbnail_url=resource.thumbnail_url,
        duration_seconds=resource.duration_seconds,
    )


@router.delete("/resources/{resource_id}", status_code=204)
def delete_resource(
    resource_id: str,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    resource = db.query(LessonResource).filter(LessonResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    db.delete(resource)
    db.commit()
    return None


# ============================================================
# Quiz CRUD
# ============================================================


@router.post("/lessons/{lesson_id}/quiz", status_code=201)
def create_quiz(
    lesson_id: str,
    body: QuizAdminCreate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    existing = db.query(Quiz).filter(Quiz.lesson_id == lesson_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Lesson already has a quiz")
    quiz = Quiz(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        title=body.title,
        description=body.description,
        passing_score=Decimal(str(body.passing_score)),
        max_attempts=body.max_attempts,
        time_limit_seconds=body.time_limit_seconds,
        is_required=body.is_required,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return {"id": quiz.id, "lesson_id": quiz.lesson_id, "title": quiz.title}


@router.put("/quizzes/{quiz_id}")
def update_quiz(
    quiz_id: str,
    body: QuizAdminUpdate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if body.title is not None:
        quiz.title = body.title
    if body.description is not None:
        quiz.description = body.description
    if body.passing_score is not None:
        quiz.passing_score = Decimal(str(body.passing_score))
    if body.max_attempts is not None:
        quiz.max_attempts = body.max_attempts
    if body.time_limit_seconds is not None:
        quiz.time_limit_seconds = body.time_limit_seconds
    if body.is_required is not None:
        quiz.is_required = body.is_required
    db.commit()
    db.refresh(quiz)
    return {"id": quiz.id, "title": quiz.title}


@router.delete("/quizzes/{quiz_id}", status_code=204)
def delete_quiz(
    quiz_id: str,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    db.delete(quiz)
    db.commit()
    return None


@router.post("/quizzes/{quiz_id}/questions", status_code=201)
def create_question(
    quiz_id: str,
    body: QuestionAdminCreate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    try:
        qtype = QuestionType(body.question_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid question_type: {body.question_type}")
    max_sort = db.query(func.max(QuizQuestion.sort_order)).filter(QuizQuestion.quiz_id == quiz_id).scalar() or 0
    question = QuizQuestion(
        id=str(uuid.uuid4()),
        quiz_id=quiz_id,
        question_type=qtype,
        question_text=body.question_text,
        explanation=body.explanation,
        points=Decimal(str(body.points)),
        sort_order=max_sort + 1,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return {"id": question.id, "question_text": question.question_text, "sort_order": question.sort_order}


@router.put("/questions/{question_id}")
def update_question(
    question_id: str,
    body: QuestionAdminUpdate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    if body.question_type is not None:
        try:
            q.question_type = QuestionType(body.question_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid question_type: {body.question_type}")
    if body.question_text is not None:
        q.question_text = body.question_text
    if body.explanation is not None:
        q.explanation = body.explanation
    if body.points is not None:
        q.points = Decimal(str(body.points))
    db.commit()
    db.refresh(q)
    return {"id": q.id, "question_text": q.question_text}


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(
    question_id: str,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return None


@router.post("/questions/{question_id}/options/bulk", status_code=200)
def replace_options(
    question_id: str,
    body: OptionsBulkReplace,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    """Atomically replace all options for a question."""
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    db.query(QuizQuestionOption).filter(QuizQuestionOption.question_id == question_id).delete()
    db.flush()
    for opt in body.options:
        db.add(QuizQuestionOption(
            id=str(uuid.uuid4()),
            question_id=question_id,
            option_text=opt.option_text,
            is_correct=opt.is_correct,
            sort_order=opt.sort_order,
            match_target=opt.match_target,
        ))
    db.commit()
    return {"message": "Options replaced", "count": len(body.options)}


# ============================================================
# Badge linking
# ============================================================


@router.get("/badges", response_model=list[BadgeMini])
def list_all_badges(
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    badges = db.query(Badge).order_by(Badge.name).all()
    return [BadgeMini.model_validate(b) for b in badges]


@router.get("/courses/{course_id}/badges", response_model=list[CourseBadgeLinkRead])
def list_course_badges(
    course_id: str,
    current_user: User = Depends(require_course_reader),
    db: Session = Depends(get_db),
):
    links = (
        db.query(CourseBadge)
        .options(joinedload(CourseBadge.badge))
        .filter(CourseBadge.course_id == course_id)
        .all()
    )
    return [
        CourseBadgeLinkRead(
            id=l.id, course_id=l.course_id,
            badge=BadgeMini.model_validate(l.badge),
            progress_percentage=float(l.progress_percentage),
        )
        for l in links
    ]


@router.post("/courses/{course_id}/badges", response_model=CourseBadgeLinkRead, status_code=201)
def link_badge(
    course_id: str,
    body: CourseBadgeLinkCreate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    badge = db.query(Badge).filter(Badge.id == body.badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")
    existing = db.query(CourseBadge).filter(
        CourseBadge.course_id == course_id, CourseBadge.badge_id == body.badge_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Badge already linked")
    link = CourseBadge(
        id=str(uuid.uuid4()),
        course_id=course_id,
        badge_id=body.badge_id,
        progress_percentage=Decimal(str(body.progress_percentage)),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    db.refresh(link, attribute_names=["badge"])
    return CourseBadgeLinkRead(
        id=link.id, course_id=link.course_id,
        badge=BadgeMini.model_validate(link.badge),
        progress_percentage=float(link.progress_percentage),
    )


@router.put("/course-badges/{link_id}", response_model=CourseBadgeLinkRead)
def update_badge_link(
    link_id: str,
    body: CourseBadgeLinkUpdate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    link = db.query(CourseBadge).options(joinedload(CourseBadge.badge)).filter(CourseBadge.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    link.progress_percentage = Decimal(str(body.progress_percentage))
    db.commit()
    db.refresh(link)
    return CourseBadgeLinkRead(
        id=link.id, course_id=link.course_id,
        badge=BadgeMini.model_validate(link.badge),
        progress_percentage=float(link.progress_percentage),
    )


@router.delete("/course-badges/{link_id}", status_code=204)
def unlink_badge(
    link_id: str,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    link = db.query(CourseBadge).filter(CourseBadge.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(link)
    db.commit()
    return None


# ============================================================
# Gem linking
# ============================================================


@router.get("/gems/all", response_model=list[GemMini])
def list_all_gems(
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    gems = db.query(Gem).filter(Gem.status == PublicationStatus.PUBLISHED).order_by(Gem.title).all()
    return [GemMini.model_validate(g) for g in gems]


@router.get("/courses/{course_id}/gems", response_model=list[CourseGemLinkRead])
def list_course_gems(
    course_id: str,
    current_user: User = Depends(require_course_reader),
    db: Session = Depends(get_db),
):
    links = (
        db.query(CourseGem)
        .options(joinedload(CourseGem.gem))
        .filter(CourseGem.course_id == course_id)
        .order_by(CourseGem.sort_order)
        .all()
    )
    return [
        CourseGemLinkRead(id=l.id, course_id=l.course_id, gem=GemMini.model_validate(l.gem), sort_order=l.sort_order)
        for l in links
    ]


@router.post("/courses/{course_id}/gems", response_model=CourseGemLinkRead, status_code=201)
def link_gem_to_course(
    course_id: str,
    body: GemLinkCreate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    gem = db.query(Gem).filter(Gem.id == body.gem_id).first()
    if not gem:
        raise HTTPException(status_code=404, detail="Gem not found")
    existing = db.query(CourseGem).filter(
        CourseGem.course_id == course_id, CourseGem.gem_id == body.gem_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Gem already linked")
    link = CourseGem(
        id=str(uuid.uuid4()),
        course_id=course_id,
        gem_id=body.gem_id,
        sort_order=body.sort_order,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    db.refresh(link, attribute_names=["gem"])
    return CourseGemLinkRead(id=link.id, course_id=link.course_id, gem=GemMini.model_validate(link.gem), sort_order=link.sort_order)


@router.delete("/course-gems/{link_id}", status_code=204)
def unlink_gem_from_course(
    link_id: str,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    link = db.query(CourseGem).filter(CourseGem.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(link)
    db.commit()
    return None


@router.get("/lessons/{lesson_id}/gems", response_model=list[LessonGemLinkRead])
def list_lesson_gems(
    lesson_id: str,
    current_user: User = Depends(require_course_reader),
    db: Session = Depends(get_db),
):
    links = (
        db.query(LessonGem)
        .options(joinedload(LessonGem.gem))
        .filter(LessonGem.lesson_id == lesson_id)
        .order_by(LessonGem.sort_order)
        .all()
    )
    return [
        LessonGemLinkRead(id=l.id, lesson_id=l.lesson_id, gem=GemMini.model_validate(l.gem), sort_order=l.sort_order)
        for l in links
    ]


@router.post("/lessons/{lesson_id}/gems", response_model=LessonGemLinkRead, status_code=201)
def link_gem_to_lesson(
    lesson_id: str,
    body: GemLinkCreate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    gem = db.query(Gem).filter(Gem.id == body.gem_id).first()
    if not gem:
        raise HTTPException(status_code=404, detail="Gem not found")
    existing = db.query(LessonGem).filter(
        LessonGem.lesson_id == lesson_id, LessonGem.gem_id == body.gem_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Gem already linked to lesson")
    link = LessonGem(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        gem_id=body.gem_id,
        sort_order=body.sort_order,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    db.refresh(link, attribute_names=["gem"])
    return LessonGemLinkRead(id=link.id, lesson_id=link.lesson_id, gem=GemMini.model_validate(link.gem), sort_order=link.sort_order)


@router.delete("/lesson-gems/{link_id}", status_code=204)
def unlink_gem_from_lesson(
    link_id: str,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    link = db.query(LessonGem).filter(LessonGem.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(link)
    db.commit()
    return None


# ============================================================
# Certification
# ============================================================


@router.get("/courses/{course_id}/certification", response_model=CertificationAdminRead)
def get_course_certification(
    course_id: str,
    current_user: User = Depends(require_course_reader),
    db: Session = Depends(get_db),
):
    cert = db.query(CourseCertification).filter(CourseCertification.course_id == course_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not configured")
    return CertificationAdminRead(
        id=cert.id, course_id=cert.course_id, title=cert.title,
        description=cert.description,
        cost=float(cert.cost) if cert.cost is not None else None,
        validity_days=cert.validity_days,
    )


@router.post("/courses/{course_id}/certification", response_model=CertificationAdminRead, status_code=201)
def create_certification(
    course_id: str,
    body: CertificationAdminCreate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    existing = db.query(CourseCertification).filter(CourseCertification.course_id == course_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Certification already exists")
    cert = CourseCertification(
        id=str(uuid.uuid4()),
        course_id=course_id,
        title=body.title,
        description=body.description,
        cost=Decimal(str(body.cost)) if body.cost is not None else None,
        validity_days=body.validity_days,
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return CertificationAdminRead(
        id=cert.id, course_id=cert.course_id, title=cert.title,
        description=cert.description,
        cost=float(cert.cost) if cert.cost is not None else None,
        validity_days=cert.validity_days,
    )


@router.put("/certifications/{cert_id}", response_model=CertificationAdminRead)
def update_certification(
    cert_id: str,
    body: CertificationAdminUpdate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    cert = db.query(CourseCertification).filter(CourseCertification.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    if body.title is not None:
        cert.title = body.title
    if body.description is not None:
        cert.description = body.description
    if body.cost is not None:
        cert.cost = Decimal(str(body.cost))
    if body.validity_days is not None:
        cert.validity_days = body.validity_days
    db.commit()
    db.refresh(cert)
    return CertificationAdminRead(
        id=cert.id, course_id=cert.course_id, title=cert.title,
        description=cert.description,
        cost=float(cert.cost) if cert.cost is not None else None,
        validity_days=cert.validity_days,
    )


@router.delete("/certifications/{cert_id}", status_code=204)
def delete_certification(
    cert_id: str,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    cert = db.query(CourseCertification).filter(CourseCertification.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    db.delete(cert)
    db.commit()
    return None


# ============================================================
# Access grants
# ============================================================


@router.get("/courses/{course_id}/grants", response_model=list[GrantAdminRead])
def list_course_grants(
    course_id: str,
    current_user: User = Depends(require_course_reader),
    db: Session = Depends(get_db),
):
    grants = (
        db.query(UserCourseGrant)
        .options(joinedload(UserCourseGrant.user))
        .filter(UserCourseGrant.course_id == course_id)
        .all()
    )
    return [
        GrantAdminRead(
            id=g.id, course_id=g.course_id,
            user=GrantUserMini.model_validate(g.user),
            granted_at=g.created_at,
        )
        for g in grants
    ]


@router.post("/courses/{course_id}/grants", status_code=201)
def create_grants(
    course_id: str,
    body: GrantCreate,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    created = []
    for uid in body.user_ids:
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            continue
        existing = db.query(UserCourseGrant).filter(
            UserCourseGrant.user_id == uid, UserCourseGrant.course_id == course_id
        ).first()
        if existing:
            continue
        grant = UserCourseGrant(
            id=str(uuid.uuid4()),
            user_id=uid,
            course_id=course_id,
            granted_by_user_id=current_user.id,
        )
        db.add(grant)
        created.append(grant.id)
    db.commit()
    return {"created": len(created), "grant_ids": created}


@router.delete("/grants/{grant_id}", status_code=204)
def revoke_grant(
    grant_id: str,
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    grant = db.query(UserCourseGrant).filter(UserCourseGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")
    db.delete(grant)
    db.commit()
    return None


# ============================================================
# Areas + Users lookup (for forms)
# ============================================================


@router.get("/areas", response_model=list[CourseAreaMini])
def list_areas(
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    areas = db.query(Area).order_by(Area.name).all()
    return [CourseAreaMini.model_validate(a) for a in areas]


@router.get("/users/search", response_model=list[GrantUserMini])
def search_users(
    q: str = Query(..., min_length=2),
    current_user: User = Depends(require_course_editor),
    db: Session = Depends(get_db),
):
    users = (
        db.query(User)
        .filter(or_(
            User.first_name.ilike(f"%{q}%"),
            User.last_name.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
        ))
        .limit(20)
        .all()
    )
    return [GrantUserMini.model_validate(u) for u in users]


# ============================================================
# User role management (super admin only)
# ============================================================


# Admin roles (NOT including super_admin, which is special and not assignable via this UI)
ASSIGNABLE_ADMIN_ROLES = {
    RoleName.CONTENT_ADMIN.value,
    RoleName.CONTENT_EDITOR.value,
    RoleName.CONTENT_VIEWER.value,
}

ALL_ADMIN_ROLES = ASSIGNABLE_ADMIN_ROLES | {RoleName.SUPER_ADMIN.value}


def _user_to_role_read(user: User, db: Session) -> UserWithRolesRead:
    role_names = [
        r[0].value for r in
        db.query(Role.name).join(UserRole, UserRole.role_id == Role.id).filter(UserRole.user_id == user.id).all()
    ]
    # Pick the admin role (highest priority)
    priority = ["super_admin", "content_admin", "content_editor", "content_viewer"]
    admin_role = next((r for r in priority if r in role_names), None)
    return UserWithRolesRead(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        status=user.status.value,
        area_name=user.area.name if user.area else None,
        roles=role_names,
        admin_role=admin_role,
        is_learner="learner" in role_names,
        created_at=user.created_at,
    )


@router.get("/users", response_model=list[UserWithRolesRead])
def list_users_for_role_mgmt(
    role: str | None = Query(None, description="Filter: 'admins' | 'super_admin' | 'content_admin' | 'content_editor' | 'content_viewer' | 'learner'"),
    search: str | None = Query(None),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """List all users with their roles. Super admin only."""
    query = db.query(User).options(joinedload(User.area))

    if search:
        query = query.filter(or_(
            User.first_name.ilike(f"%{search}%"),
            User.last_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
        ))

    users = query.order_by(User.created_at.desc()).all()
    results = [_user_to_role_read(u, db) for u in users]

    # Apply role filter in Python (since roles are M2M)
    if role:
        if role == "admins":
            results = [r for r in results if r.admin_role is not None]
        else:
            results = [r for r in results if role in r.roles]

    return results


@router.put("/users/{user_id}/admin-role", response_model=UserWithRolesRead)
def set_user_admin_role(
    user_id: str,
    body: SetAdminRoleRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Set or remove a user's admin role.

    Body:
    - `role: "content_admin" | "content_editor" | "content_viewer"` → assign this admin role (replaces any previous)
    - `role: null` → remove any admin role from this user
    """
    # Prevent modifying yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes modificar tu propio rol")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validate requested role
    if body.role is not None and body.role not in ASSIGNABLE_ADMIN_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Rol inválido. Debe ser uno de: {', '.join(ASSIGNABLE_ADMIN_ROLES)} o null",
        )

    # Cannot demote a super_admin via this endpoint — they're sacred
    existing_user_roles = (
        db.query(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    existing_role_names = {r.name.value for r in existing_user_roles}
    if RoleName.SUPER_ADMIN.value in existing_role_names:
        raise HTTPException(
            status_code=400,
            detail="No se puede modificar el rol de un super administrador",
        )

    # Remove any existing admin roles (except super_admin, handled above)
    for role_obj in existing_user_roles:
        if role_obj.name.value in ASSIGNABLE_ADMIN_ROLES:
            db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role_obj.id,
            ).delete()

    # Add the new admin role if provided
    if body.role is not None:
        target_role = db.query(Role).filter(Role.name == RoleName(body.role)).first()
        if not target_role:
            raise HTTPException(status_code=500, detail=f"Role '{body.role}' not in database")
        # Check if already has this role (shouldn't happen after delete above, but safe)
        existing_link = (
            db.query(UserRole)
            .filter(UserRole.user_id == user_id, UserRole.role_id == target_role.id)
            .first()
        )
        if not existing_link:
            db.add(UserRole(
                user_id=user_id,
                role_id=target_role.id,
                assigned_by_user_id=current_user.id,
            ))

    # Ensure user ALWAYS has the learner role as base
    learner_role = db.query(Role).filter(Role.name == RoleName.LEARNER).first()
    if learner_role:
        has_learner = (
            db.query(UserRole)
            .filter(UserRole.user_id == user_id, UserRole.role_id == learner_role.id)
            .first()
        )
        if not has_learner:
            db.add(UserRole(
                user_id=user_id,
                role_id=learner_role.id,
                assigned_by_user_id=current_user.id,
            ))

    db.commit()
    db.refresh(user)
    return _user_to_role_read(user, db)


@router.get("/roles", response_model=list[dict])
def list_assignable_roles(
    current_user: User = Depends(require_super_admin),
):
    """Return the list of admin roles that can be assigned (not super_admin)."""
    return [
        {"value": "content_admin", "label": "Administrador de Contenido", "description": "Acceso total: crear, publicar, editar, eliminar cursos"},
        {"value": "content_editor", "label": "Editor de Contenido", "description": "Editar cursos existentes (no crear ni publicar)"},
        {"value": "content_viewer", "label": "Observador", "description": "Acceso al panel admin pero sin gestionar cursos"},
    ]
