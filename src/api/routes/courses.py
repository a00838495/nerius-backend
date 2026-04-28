"""Courses routes."""

import unicodedata
import uuid
from datetime import datetime
from decimal import Decimal

from rapidfuzz import fuzz


def _normalize(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


def _matches_search(query: str, course: "Course") -> bool:
    q = _normalize(query)
    fields = [course.title, course.description or ""]
    for field in fields:
        t = _normalize(field)
        if q in t:
            return True
        if fuzz.partial_ratio(q, t) >= 65:
            return True
    return False

from fastapi import APIRouter, Depends, HTTPException, Cookie, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from src.core.auth import validate_session
from src.db.session import get_db
from src.db.models.learning_platform import (
    Area,
    User,
    Role,
    UserRole,
    RoleName,
    Course,
    CourseAssignment,
    Enrollment,
    EnrollmentStatus,
    PublicationStatus,
    CourseModule,
    Lesson,
    LessonResource,
    LessonProgress,
    LessonProgressStatus,
)
from src.db.models.learning_platform import Badge, CourseBadge, UserBadge, CourseGem, LessonGem, Gem, GemTagLink, GemTag, PublicationStatus as GemPubStatus, UserGemCollection, Quiz, QuizAttempt, QuizAttemptStatus, CourseCertification
from src.schemas.user import (
    CourseRead,
    CourseAssignmentCreate,
    CourseAssignmentRead,
    EnrollmentRead,
    CourseDetailedRead,
    ModuleDetailedRead,
    ModuleBasicRead,
    ModuleWithProgressRead,
    LessonDetailedRead,
    LessonBasicRead,
    LessonWithProgressRead,
    LessonResourceRead,
    LessonProgressRead,
    LessonProgressUpdate,
    LessonProgressUpdateResponse,
)
from src.schemas.user import AreaRead, BadgeRead, CourseCardRead, CourseRankingRead, EarnedBadgeNotification, UserBadgeRead

router = APIRouter(tags=["courses"], prefix="/courses")


def get_current_user(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user."""
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    session = validate_session(session_id, db)
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
        )

    user = db.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


def get_optional_current_user(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
) -> User | None:
    """Get current user if authenticated, otherwise return None."""
    if not session_id:
        return None
    session = validate_session(session_id, db)
    if not session:
        return None
    return db.query(User).filter(User.id == session["user_id"]).first()


def require_admin_user(current_user: User, db: Session) -> None:
    """Allow only super admins or content admins."""
    admin_role = (
        db.query(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .filter(
            UserRole.user_id == current_user.id,
            Role.name.in_([RoleName.SUPER_ADMIN, RoleName.CONTENT_ADMIN]),
        )
        .first()
    )
    if not admin_role:
        raise HTTPException(
            status_code=403,
            detail="Only admins can assign courses",
        )


def get_enrollment_completion_seconds(enrollment: Enrollment) -> float:
    """Return how long a completed enrollment took in seconds."""
    started_at = enrollment.started_at or enrollment.created_at
    completed_at = enrollment.completed_at
    if not started_at or not completed_at:
        return float("inf")

    return max((completed_at - started_at).total_seconds(), 0.0)


def build_course_assignment_read(assignment: CourseAssignment) -> CourseAssignmentRead:
    """Serialize a course assignment with course and assigner details."""
    assigned_by_name = None
    if assignment.assigned_by_user:
        assigned_by_name = (
            f"{assignment.assigned_by_user.first_name} {assignment.assigned_by_user.last_name}".strip()
        )

    return CourseAssignmentRead(
        id=assignment.id,
        course_id=assignment.course_id,
        assigned_by_user_id=assignment.assigned_by_user_id,
        assigned_to_user_id=assignment.assigned_to_user_id,
        due_date=assignment.due_date.isoformat(),
        created_at=assignment.created_at.isoformat(),
        assigned_by_name=assigned_by_name,
        course=CourseRead(
            id=assignment.course.id,
            title=assignment.course.title,
            description=assignment.course.description,
            status=assignment.course.status.value,
            estimated_minutes=assignment.course.estimated_minutes,
            cover_url=assignment.course.cover_url,
        ) if assignment.course else None,
    )


@router.get("", response_model=list[CourseCardRead])
def get_available_courses(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of courses to return"),
    skip: int = Query(default=0, ge=0, description="Number of courses to skip for pagination"),
    search: str | None = Query(default=None, description="Fuzzy/phonetic search term"),
):
    """
    Get all published courses with optional fuzzy search and pagination.

    - **search**: Optional term — tolerates typos and missing accents (e.g. "matematicas" finds "Matemáticas")
    - **limit**: Maximum number of courses to return (default: 10, max: 50)
    - **skip**: Number of courses to skip for pagination (default: 0)
    """
    query = (
        db.query(Course)
        .options(joinedload(Course.area), joinedload(Course.created_by_user))
        .filter(Course.status == PublicationStatus.PUBLISHED)
        .order_by(Course.created_at.desc())
    )

    if search and search.strip():
        all_courses = query.all()
        courses = [c for c in all_courses if _matches_search(search.strip(), c)]
        courses = courses[skip: skip + limit]
    else:
        courses = query.offset(skip).limit(limit).all()

    # Precompute which courses have certifications
    cert_course_ids = set(
        row[0] for row in db.query(CourseCertification.course_id).all()
    )

    result = []
    for course in courses:
        modules_count = (
            db.query(func.count(CourseModule.id))
            .filter(CourseModule.course_id == course.id)
            .scalar() or 0
        )
        lessons_count = (
            db.query(func.count(Lesson.id))
            .join(CourseModule, Lesson.module_id == CourseModule.id)
            .filter(CourseModule.course_id == course.id)
            .scalar() or 0
        )
        total_enrolled = (
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.course_id == course.id)
            .scalar() or 0
        )
        total_completed = (
            db.query(func.count(Enrollment.id))
            .filter(
                Enrollment.course_id == course.id,
                Enrollment.status == EnrollmentStatus.completed,
            )
            .scalar() or 0
        )

        enrollment = None
        is_enrolled = False
        if current_user:
            enrollment = (
                db.query(Enrollment)
                .filter(
                    Enrollment.course_id == course.id,
                    Enrollment.user_id == current_user.id,
                )
                .first()
            )
            is_enrolled = enrollment is not None

        creator = course.created_by_user
        created_by_name = f"{creator.first_name} {creator.last_name}".strip() if creator else "Unknown"

        result.append(
            CourseCardRead(
                id=course.id,
                title=course.title,
                description=course.description,
                status=course.status.value,
                estimated_minutes=course.estimated_minutes,
                cover_url=course.cover_url,
                area=AreaRead(id=course.area.id, name=course.area.name) if course.area else None,
                created_by_name=created_by_name,
                modules_count=modules_count,
                lessons_count=lessons_count,
                total_enrolled=total_enrolled,
                total_completed=total_completed,
                is_enrolled=is_enrolled,
                enrollment=EnrollmentRead(
                    id=enrollment.id,
                    course_id=enrollment.course_id,
                    status=enrollment.status.value,
                    progress_percent=float(enrollment.progress_percent),
                ) if enrollment else None,
                has_certification=course.id in cert_course_ids,
            )
        )

    return result


@router.get("/user/pending", response_model=list[EnrollmentRead])
def get_user_pending_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get pending courses for the current user.
    Returns only courses where the user has an active enrollment.
    """
    # Get active enrollments for the user
    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.status == EnrollmentStatus.active,
        )
        .all()
    )

    return [
        EnrollmentRead(
            id=enrollment.id,
            course_id=enrollment.course_id,
            status=enrollment.status.value,
            progress_percent=float(enrollment.progress_percent),
            course=CourseRead(
                id=enrollment.course.id,
                title=enrollment.course.title,
                description=enrollment.course.description,
                status=enrollment.course.status.value,
                estimated_minutes=enrollment.course.estimated_minutes,
                cover_url=enrollment.course.cover_url,
            ) if enrollment.course else None,
        )
        for enrollment in enrollments
    ]


@router.get("/user/completed", response_model=list[EnrollmentRead])
def get_user_completed_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get completed courses for the current user, most recent first."""
    enrollments = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.course))
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.status == EnrollmentStatus.completed,
        )
        .order_by(Enrollment.completed_at.desc())
        .all()
    )

    return [
        EnrollmentRead(
            id=enrollment.id,
            course_id=enrollment.course_id,
            status=enrollment.status.value,
            progress_percent=float(enrollment.progress_percent),
            course=CourseRead(
                id=enrollment.course.id,
                title=enrollment.course.title,
                description=enrollment.course.description,
                status=enrollment.course.status.value,
                estimated_minutes=enrollment.course.estimated_minutes,
                cover_url=enrollment.course.cover_url,
            ) if enrollment.course else None,
        )
        for enrollment in enrollments
    ]


@router.get("/user/assigned", response_model=list[CourseAssignmentRead])
def get_user_assigned_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get courses assigned to the current user without creating enrollments."""
    assignments = (
        db.query(CourseAssignment)
        .options(
            joinedload(CourseAssignment.course),
            joinedload(CourseAssignment.assigned_by_user),
        )
        .filter(CourseAssignment.assigned_to_user_id == current_user.id)
        .order_by(CourseAssignment.due_date.asc(), CourseAssignment.created_at.desc())
        .all()
    )

    return [build_course_assignment_read(assignment) for assignment in assignments]


@router.get("/user/assigned/pending", response_model=list[CourseAssignmentRead])
def get_user_pending_assigned_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get assigned courses for the current user that are not completed."""
    completed_course_ids = {
        course_id
        for (course_id,) in (
            db.query(Enrollment.course_id)
            .filter(
                Enrollment.user_id == current_user.id,
                Enrollment.status == EnrollmentStatus.completed,
            )
            .all()
        )
    }

    assignments_query = (
        db.query(CourseAssignment)
        .options(
            joinedload(CourseAssignment.course),
            joinedload(CourseAssignment.assigned_by_user),
        )
        .filter(CourseAssignment.assigned_to_user_id == current_user.id)
    )

    if completed_course_ids:
        assignments_query = assignments_query.filter(
            CourseAssignment.course_id.notin_(completed_course_ids)
        )

    assignments = (
        assignments_query
        .order_by(CourseAssignment.due_date.asc(), CourseAssignment.created_at.desc())
        .all()
    )

    return [build_course_assignment_read(assignment) for assignment in assignments]


@router.get("/user/recommended", response_model=list[CourseRead])
def get_recommended_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get recommended courses for the current user.
    Prioritize published courses from the same area that the user has not taken yet.
    If there are no same-area matches, return published courses from any area that
    the user has not taken yet.
    """
    # Get all course IDs where the user already has an enrollment (any status)
    enrolled_course_ids = (
        db.query(Enrollment.course_id)
        .filter(Enrollment.user_id == current_user.id)
        .all()
    )
    enrolled_ids = [course_id for (course_id,) in enrolled_course_ids]

    base_query = (
        db.query(Course)
        .filter(
            Course.status == PublicationStatus.PUBLISHED,
            Course.id.notin_(enrolled_ids) if enrolled_ids else True,
        )
    )

    same_area_courses = []
    if current_user.area_id:
        same_area_courses = (
            base_query
            .filter(Course.area_id == current_user.area_id)
            .order_by(Course.created_at.desc())
            .all()
        )

    recommended_courses = same_area_courses
    if not recommended_courses:
        recommended_courses = base_query.order_by(Course.created_at.desc()).all()
    
    return [
        CourseRead(
            id=course.id,
            title=course.title,
            description=course.description,
            status=course.status.value,
            estimated_minutes=course.estimated_minutes,
            cover_url=course.cover_url,
        )
        for course in recommended_courses
    ]


@router.get("/user/badges", response_model=list[UserBadgeRead])
def get_user_badges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all badges earned by the current user, ordered by most recently awarded."""
    user_badges = (
        db.query(UserBadge)
        .options(joinedload(UserBadge.badge))
        .filter(UserBadge.user_id == current_user.id)
        .order_by(UserBadge.awarded_at.desc())
        .all()
    )
    return [
        UserBadgeRead(
            id=ub.id,
            badge=BadgeRead(
                id=ub.badge.id,
                name=ub.badge.name,
                description=ub.badge.description,
                icon_url=ub.badge.icon_url,
                main_color=ub.badge.main_color,
                secondary_color=ub.badge.secondary_color,
            ),
            awarded_at=ub.awarded_at.isoformat(),
        )
        for ub in user_badges
    ]


@router.get("/ranking", response_model=list[CourseRankingRead])
def get_courses_ranking(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the employee ranking ordered by completed courses and completion speed."""
    completed_enrollments = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.user).joinedload(User.area))
        .filter(Enrollment.status == EnrollmentStatus.completed)
        .all()
    )

    ranking_by_user = {}
    for enrollment in completed_enrollments:
        if not enrollment.user:
            continue

        user = enrollment.user
        ranking_entry = ranking_by_user.setdefault(
            user.id,
            {
                "name": f"{user.first_name} {user.last_name}",
                "area": user.area.name if user.area else "Sin area",
                "total_completed_courses": 0,
                "total_completion_seconds": 0.0,
            },
        )
        ranking_entry["total_completed_courses"] += 1
        ranking_entry["total_completion_seconds"] += get_enrollment_completion_seconds(enrollment)

    sorted_ranking = sorted(
        ranking_by_user.values(),
        key=lambda entry: (
            -entry["total_completed_courses"],
            entry["total_completion_seconds"],
            entry["name"].lower(),
        ),
    )

    return [
        CourseRankingRead(
            name=entry["name"],
            total_completed_courses=entry["total_completed_courses"],
            area=entry["area"],
        )
        for entry in sorted_ranking
    ]


@router.post("/assignments", response_model=CourseAssignmentRead, status_code=201)
def assign_course_to_user(
    assignment_data: CourseAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign a course to a learner without enrolling them."""
    require_admin_user(current_user, db)

    course = db.query(Course).filter(Course.id == assignment_data.course_id).first()
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    assigned_user = (
        db.query(User)
        .filter(User.id == assignment_data.assigned_to_user_id)
        .first()
    )
    if not assigned_user:
        raise HTTPException(
            status_code=404,
            detail="Assigned user not found",
        )

    learner_role = (
        db.query(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .filter(
            UserRole.user_id == assigned_user.id,
            Role.name == RoleName.LEARNER,
        )
        .first()
    )
    if not learner_role:
        raise HTTPException(
            status_code=400,
            detail="Assigned user must have learner role",
        )

    existing_assignment = (
        db.query(CourseAssignment)
        .filter(
            CourseAssignment.course_id == assignment_data.course_id,
            CourseAssignment.assigned_to_user_id == assignment_data.assigned_to_user_id,
        )
        .first()
    )
    if existing_assignment:
        raise HTTPException(
            status_code=409,
            detail="This course is already assigned to this user",
        )

    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == assignment_data.course_id,
            Enrollment.user_id == assignment_data.assigned_to_user_id,
        )
        .first()
    )
    if existing_enrollment:
        raise HTTPException(
            status_code=409,
            detail="User is already enrolled in this course",
        )

    assignment = CourseAssignment(
        id=str(uuid.uuid4()),
        course_id=assignment_data.course_id,
        assigned_by_user_id=current_user.id,
        assigned_to_user_id=assignment_data.assigned_to_user_id,
        due_date=assignment_data.due_date,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return CourseAssignmentRead(
        id=assignment.id,
        course_id=assignment.course_id,
        assigned_by_user_id=assignment.assigned_by_user_id,
        assigned_to_user_id=assignment.assigned_to_user_id,
        due_date=assignment.due_date.isoformat(),
        created_at=assignment.created_at.isoformat(),
        assigned_by_name=f"{current_user.first_name} {current_user.last_name}".strip(),
        course=CourseRead(
            id=course.id,
            title=course.title,
            description=course.description,
            status=course.status.value,
            estimated_minutes=course.estimated_minutes,
            cover_url=course.cover_url,
        ),
    )


@router.get("/{course_id}", response_model=CourseCardRead)
def get_course_card(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get course summary for card display.

    Returns all the information needed to render a course card:
    title, description, area, creator name, module/lesson counts,
    enrollment stats (total enrolled and completed), and whether
    the current user is already enrolled.

    Does NOT require the user to be enrolled.
    """
    course = (
        db.query(Course)
        .options(
            joinedload(Course.area),
            joinedload(Course.created_by_user),
        )
        .filter(Course.id == course_id)
        .first()
    )

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Counts via efficient scalar queries
    modules_count: int = (
        db.query(func.count(CourseModule.id))
        .filter(CourseModule.course_id == course_id)
        .scalar()
    ) or 0

    lessons_count: int = (
        db.query(func.count(Lesson.id))
        .join(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(CourseModule.course_id == course_id)
        .scalar()
    ) or 0

    total_enrolled: int = (
        db.query(func.count(Enrollment.id))
        .filter(Enrollment.course_id == course_id)
        .scalar()
    ) or 0

    total_completed: int = (
        db.query(func.count(Enrollment.id))
        .filter(
            Enrollment.course_id == course_id,
            Enrollment.status == EnrollmentStatus.completed,
        )
        .scalar()
    ) or 0

    # Current user enrollment (optional)
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course_id,
        )
        .first()
    )

    return CourseCardRead(
        id=course.id,
        title=course.title,
        description=course.description,
        status=course.status.value,
        estimated_minutes=course.estimated_minutes,
        cover_url=course.cover_url,
        area=AreaRead(
            id=course.area.id,
            name=course.area.name,
        ) if course.area else None,
        created_by_name=(
            f"{course.created_by_user.first_name} {course.created_by_user.last_name}"
        ),
        modules_count=modules_count,
        lessons_count=lessons_count,
        total_enrolled=total_enrolled,
        total_completed=total_completed,
        is_enrolled=enrollment is not None,
        enrollment=EnrollmentRead(
            id=enrollment.id,
            course_id=enrollment.course_id,
            status=enrollment.status.value,
            progress_percent=float(enrollment.progress_percent),
        ) if enrollment else None,
        has_certification=db.query(CourseCertification).filter(CourseCertification.course_id == course_id).first() is not None,
    )


@router.post("/{course_id}/enroll", response_model=EnrollmentRead, status_code=201)
def enroll_user_in_course(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enroll the current authenticated user in a specific course.
    
    - **course_id**: UUID of the course to enroll in
    
    Returns the created enrollment with course details.
    
    Raises:
    - **404**: Course not found or not published
    - **409**: User already enrolled in this course
    - **401**: User not authenticated
    """
    # Verify course exists and is published
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )
    
    if course.status != PublicationStatus.PUBLISHED:
        raise HTTPException(
            status_code=404,
            detail="Course is not available for enrollment",
        )
    
    # Check if user is already enrolled
    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course_id,
        )
        .first()
    )
    
    if existing_enrollment:
        raise HTTPException(
            status_code=409,
            detail=f"User already enrolled in this course with status: {existing_enrollment.status.value}",
        )
    
    # Create new enrollment
    new_enrollment = Enrollment(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        course_id=course_id,
        status=EnrollmentStatus.active,
        progress_percent=Decimal("0.00"),
        started_at=datetime.now(),
        last_activity_at=datetime.now(),
    )
    
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    
    # Return enrollment with course details
    return EnrollmentRead(
        id=new_enrollment.id,
        course_id=new_enrollment.course_id,
        status=new_enrollment.status.value,
        progress_percent=float(new_enrollment.progress_percent),
        course=CourseRead(
            id=course.id,
            title=course.title,
            description=course.description,
            status=course.status.value,
            estimated_minutes=course.estimated_minutes,
            cover_url=course.cover_url,
        ),
    )


@router.get("/{course_id}/detailed", response_model=CourseDetailedRead)
def get_course_detailed(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get course with all modules and lessons including progress status.
    
    Returns all modules and all lessons with their progress percentage and status,
    but WITHOUT resources. To get full lesson details with resources,
    use GET /courses/{course_id}/lessons/{lesson_id}
    
    - **course_id**: UUID of the course
    
    Requires the user to be enrolled in the course.
    """
    # Get course with modules and lessons
    course = (
        db.query(Course)
        .options(
            joinedload(Course.modules).joinedload(CourseModule.lessons)
        )
        .filter(Course.id == course_id)
        .first()
    )
    
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )
    
    # Check if user is enrolled
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course_id,
        )
        .first()
    )
    
    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="User is not enrolled in this course",
        )
    
    # Get all lesson progress for this enrollment
    lesson_progress_map = {}
    lesson_progresses = (
        db.query(LessonProgress)
        .filter(LessonProgress.enrollment_id == enrollment.id)
        .all()
    )
    for lp in lesson_progresses:
        lesson_progress_map[lp.lesson_id] = lp

    # Get lesson IDs that have quizzes
    quiz_lesson_ids = set(
        row[0] for row in db.query(Quiz.lesson_id).filter(
            Quiz.lesson_id.in_([
                l.id for m in course.modules for l in m.lessons
            ])
        ).all()
    )
    
    # Build modules with lessons including progress
    modules_data = []
    sorted_modules = sorted(course.modules, key=lambda m: m.sort_order)
    
    for module in sorted_modules:
        sorted_lessons = sorted(module.lessons, key=lambda l: l.sort_order)
        
        lessons_with_progress = []
        for lesson in sorted_lessons:
            # Get progress for this lesson
            lesson_progress = lesson_progress_map.get(lesson.id)
            
            if lesson_progress:
                status = lesson_progress.status.value
                progress_percent = float(lesson_progress.progress_percent)
            else:
                # Default values for lessons without progress
                status = "not_started"
                progress_percent = 0.0
            
            lessons_with_progress.append(
                LessonWithProgressRead(
                    id=lesson.id,
                    title=lesson.title,
                    sort_order=lesson.sort_order,
                    estimated_minutes=lesson.estimated_minutes,
                    status=status,
                    progress_percent=progress_percent,
                    has_quiz=lesson.id in quiz_lesson_ids,
                )
            )
        
        modules_data.append(
            ModuleWithProgressRead(
                id=module.id,
                title=module.title,
                sort_order=module.sort_order,
                lessons=lessons_with_progress,
            )
        )
    
    return CourseDetailedRead(
        id=course.id,
        title=course.title,
        description=course.description,
        status=course.status.value,
        estimated_minutes=course.estimated_minutes,
        cover_url=course.cover_url,
        enrollment=EnrollmentRead(
            id=enrollment.id,
            course_id=enrollment.course_id,
            status=enrollment.status.value,
            progress_percent=float(enrollment.progress_percent),
        ),
        modules=modules_data,
    )


@router.get("/{course_id}/lessons/{lesson_id}", response_model=LessonDetailedRead)
def get_lesson_detailed(
    course_id: str,
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information for a specific lesson including resources and progress.
    
    - **course_id**: UUID of the course
    - **lesson_id**: UUID of the lesson
    
    Returns full lesson details with:
    - Title, description, estimated_minutes
    - All resources (videos, PDFs, slides, etc.)
    - User's progress (status, progress_percent)
    
    Requires the user to be enrolled in the course.
    """
    # Check if user is enrolled
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course_id,
        )
        .first()
    )
    
    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="User is not enrolled in this course",
        )
    
    # Get lesson with resources
    lesson = (
        db.query(Lesson)
        .join(CourseModule)
        .filter(
            Lesson.id == lesson_id,
            CourseModule.course_id == course_id,
        )
        .first()
    )
    
    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found in this course",
        )
    
    # Get lesson resources
    resources_list = (
        db.query(LessonResource)
        .filter(LessonResource.lesson_id == lesson_id)
        .all()
    )
    
    resources = [
        LessonResourceRead(
            id=r.id,
            resource_type=r.resource_type.value,
            title=r.title,
            external_url=r.external_url,
            thumbnail_url=r.thumbnail_url,
            duration_seconds=r.duration_seconds,
        )
        for r in resources_list
    ]
    
    # Get lesson progress
    lesson_progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.enrollment_id == enrollment.id,
            LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )
    
    progress_data = None
    if lesson_progress:
        progress_data = LessonProgressRead(
            lesson_id=lesson.id,
            status=lesson_progress.status.value,
            progress_percent=float(lesson_progress.progress_percent),
            time_spent_seconds=lesson_progress.time_spent_seconds,
            completed_at=lesson_progress.completed_at.isoformat() if lesson_progress.completed_at else None,
            last_activity_at=lesson_progress.last_activity_at.isoformat() if lesson_progress.last_activity_at else None,
        )
    
    return LessonDetailedRead(
        id=lesson.id,
        title=lesson.title,
        description=lesson.description,
        sort_order=lesson.sort_order,
        estimated_minutes=lesson.estimated_minutes,
        resources=resources,
        progress=progress_data,
    )


@router.put("/{course_id}/lessons/{lesson_id}/progress", response_model=LessonProgressUpdateResponse)
def update_lesson_progress(
    course_id: str,
    lesson_id: str,
    progress_data: LessonProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update user's progress for a specific lesson.
    This endpoint is called frequently by the frontend to track progress.
    
    - **course_id**: UUID of the course
    - **lesson_id**: UUID of the lesson
    - **progress_data**: Progress information (percent, time spent, status)
    
    Returns updated progress and overall enrollment progress.
    """
    # Verify enrollment exists
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course_id,
        )
        .first()
    )
    
    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="User is not enrolled in this course",
        )
    
    # Verify lesson exists and belongs to the course
    lesson = (
        db.query(Lesson)
        .join(CourseModule)
        .filter(
            Lesson.id == lesson_id,
            CourseModule.course_id == course_id,
        )
        .first()
    )
    
    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found in this course",
        )
    
    # Validate status
    try:
        status_enum = LessonProgressStatus(progress_data.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: not_started, in_progress, completed",
        )
    
    # Find or create lesson progress
    lesson_progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.enrollment_id == enrollment.id,
            LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )
    
    if lesson_progress:
        # Update existing progress
        lesson_progress.status = status_enum
        lesson_progress.progress_percent = Decimal(str(progress_data.progress_percent))
        lesson_progress.time_spent_seconds = progress_data.time_spent_seconds
        lesson_progress.last_activity_at = datetime.utcnow()
        
        # Quiz gate: check if lesson has a required quiz that must be passed
        quiz_required = False
        quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson_id, Quiz.is_required.is_(True)).first()
        if quiz:
            quiz_required = True
            quiz_passed = (
                db.query(QuizAttempt)
                .filter(
                    QuizAttempt.quiz_id == quiz.id,
                    QuizAttempt.user_id == current_user.id,
                    QuizAttempt.passed.is_(True),
                )
                .first()
            ) is not None
        else:
            quiz_passed = True

        # Mark as completed if progress is 100% or status is completed — BUT only if quiz is passed
        wants_complete = progress_data.progress_percent >= 100 or status_enum == LessonProgressStatus.completed
        if wants_complete and quiz_passed:
            lesson_progress.status = LessonProgressStatus.completed
            if not lesson_progress.completed_at:
                lesson_progress.completed_at = datetime.utcnow()
        elif wants_complete and not quiz_passed:
            # Cap at 99% — quiz not yet passed
            lesson_progress.progress_percent = min(lesson_progress.progress_percent, Decimal("99.00"))
            lesson_progress.status = LessonProgressStatus.in_progress
    else:
        # Create new progress entry
        lesson_progress = LessonProgress(
            id=str(uuid.uuid4()),
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
            status=status_enum,
            progress_percent=Decimal(str(progress_data.progress_percent)),
            time_spent_seconds=progress_data.time_spent_seconds,
            last_activity_at=datetime.utcnow(),
        )

        # Quiz gate for new entries too
        quiz_required = False
        quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson_id, Quiz.is_required.is_(True)).first()
        if quiz:
            quiz_required = True
            quiz_passed = (
                db.query(QuizAttempt)
                .filter(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == current_user.id, QuizAttempt.passed.is_(True))
                .first()
            ) is not None
        else:
            quiz_passed = True

        wants_complete = progress_data.progress_percent >= 100 or status_enum == LessonProgressStatus.completed
        if wants_complete and quiz_passed:
            lesson_progress.status = LessonProgressStatus.completed
            lesson_progress.completed_at = datetime.utcnow()
        elif wants_complete and not quiz_passed:
            lesson_progress.progress_percent = min(Decimal(str(progress_data.progress_percent)), Decimal("99.00"))
            lesson_progress.status = LessonProgressStatus.in_progress
        
        db.add(lesson_progress)
    
    # Flush to make the new lesson_progress visible in subsequent queries
    db.flush()
    
    # Update enrollment last_activity_at
    enrollment.last_activity_at = datetime.utcnow()
    
    # Calculate overall course progress based on ALL lessons
    # Get all lessons in the course
    all_lessons = (
        db.query(Lesson.id)
        .join(CourseModule)
        .filter(CourseModule.course_id == course_id)
        .all()
    )
    
    total_lessons = len(all_lessons)
    
    if total_lessons > 0:
        # Get all lesson progress for this enrollment
        lesson_progress_records = (
            db.query(LessonProgress)
            .filter(LessonProgress.enrollment_id == enrollment.id)
            .all()
        )
        
        # Create a map of lesson_id -> progress_percent
        progress_map = {
            lp.lesson_id: float(lp.progress_percent) 
            for lp in lesson_progress_records
        }
        
        # Calculate average progress across ALL lessons
        # Lessons without progress are considered 0%
        total_progress = sum(
            progress_map.get(lesson_id, 0.0) 
            for (lesson_id,) in all_lessons
        )
        
        enrollment.progress_percent = Decimal(str(total_progress / total_lessons))
        
        # Check if all lessons are completed
        completed_count = sum(
            1 for lp in lesson_progress_records
            if lp.status == LessonProgressStatus.completed
        )
        
        # Mark course as completed only if ALL lessons are 100% completed
        if completed_count == total_lessons:
            enrollment.status = EnrollmentStatus.completed
            if not enrollment.completed_at:
                enrollment.completed_at = datetime.utcnow()
    
    # Check for newly earned badges based on updated enrollment progress
    new_progress = float(enrollment.progress_percent)
    course_badges = (
        db.query(CourseBadge)
        .options(joinedload(CourseBadge.badge))
        .filter(
            CourseBadge.course_id == course_id,
            CourseBadge.progress_percentage <= new_progress,
        )
        .all()
    )

    earned_badges = []
    for cb in course_badges:
        existing = (
            db.query(UserBadge)
            .filter(
                UserBadge.user_id == current_user.id,
                UserBadge.badge_id == cb.badge_id,
            )
            .first()
        )
        if not existing:
            db.add(UserBadge(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                badge_id=cb.badge_id,
            ))
            earned_badges.append(EarnedBadgeNotification(
                badge=BadgeRead(
                    id=cb.badge.id,
                    name=cb.badge.name,
                    description=cb.badge.description,
                    icon_url=cb.badge.icon_url,
                    main_color=cb.badge.main_color,
                    secondary_color=cb.badge.secondary_color,
                ),
                awarded_at=datetime.utcnow().isoformat(),
            ))

    db.commit()
    db.refresh(lesson_progress)
    db.refresh(enrollment)
    
    return LessonProgressUpdateResponse(
        lesson_id=lesson_progress.lesson_id,
        status=lesson_progress.status.value,
        progress_percent=float(lesson_progress.progress_percent),
        time_spent_seconds=lesson_progress.time_spent_seconds,
        enrollment_progress_percent=float(enrollment.progress_percent),
        earned_badges=earned_badges,
        quiz_required=quiz_required,
    )


# ============================================================
# Gems associated with courses and lessons
# ============================================================

from src.schemas.gems import GemCardRead, GemCategoryRead, GemCreatorRead, GemTagRead, AreaRead as GemAreaRead


def _course_gem_to_card(gem: Gem, saved_ids: set[str], saves_counts: dict[str, int]) -> GemCardRead:
    tags = [GemTagRead(id=link.tag.id, name=link.tag.name) for link in gem.tag_links]
    return GemCardRead(
        id=gem.id,
        title=gem.title,
        description=gem.description,
        icon_url=gem.icon_url,
        gemini_url=gem.gemini_url,
        visibility=gem.visibility.value,
        is_featured=gem.is_featured,
        status=gem.status.value,
        saves_count=saves_counts.get(gem.id, 0),
        created_at=gem.created_at,
        category=GemCategoryRead(
            id=gem.category.id, name=gem.category.name,
            description=gem.category.description, icon=gem.category.icon,
            sort_order=gem.category.sort_order,
        ) if gem.category else None,
        area=GemAreaRead(id=gem.area.id, name=gem.area.name) if gem.area else None,
        created_by_user=GemCreatorRead(
            id=gem.created_by_user.id,
            first_name=gem.created_by_user.first_name,
            last_name=gem.created_by_user.last_name,
        ),
        tags=tags,
        is_saved=gem.id in saved_ids,
    )


def _get_course_gem_saves_counts(gem_ids: list[str], db: Session) -> dict[str, int]:
    if not gem_ids:
        return {}
    rows = (
        db.query(UserGemCollection.gem_id, func.count(UserGemCollection.id))
        .filter(UserGemCollection.gem_id.in_(gem_ids))
        .group_by(UserGemCollection.gem_id)
        .all()
    )
    return {gid: cnt for gid, cnt in rows}


def _get_user_saved_gem_ids(session_id: str | None, db: Session) -> set[str]:
    if not session_id:
        return set()
    from src.core.auth import validate_session as _vs
    sess = _vs(session_id, db)
    if not sess:
        return set()
    rows = db.query(UserGemCollection.gem_id).filter(UserGemCollection.user_id == sess["user_id"]).all()
    return {r[0] for r in rows}


@router.get("/{course_id}/gems", response_model=list[GemCardRead])
def get_course_gems(
    course_id: str,
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Get gems associated with a course."""
    saved_ids = _get_user_saved_gem_ids(session_id, db)
    course_gems = (
        db.query(CourseGem)
        .options(
            joinedload(CourseGem.gem).joinedload(Gem.category),
            joinedload(CourseGem.gem).joinedload(Gem.area),
            joinedload(CourseGem.gem).joinedload(Gem.created_by_user),
            joinedload(CourseGem.gem).joinedload(Gem.tag_links).joinedload(GemTagLink.tag),
        )
        .filter(CourseGem.course_id == course_id)
        .order_by(CourseGem.sort_order)
        .all()
    )
    published_gems = [cg.gem for cg in course_gems if cg.gem.status == GemPubStatus.PUBLISHED]
    gem_ids = [g.id for g in published_gems]
    saves_counts = _get_course_gem_saves_counts(gem_ids, db)
    return [_course_gem_to_card(g, saved_ids, saves_counts) for g in published_gems]


@router.get("/{course_id}/lessons/{lesson_id}/gems", response_model=list[GemCardRead])
def get_lesson_gems(
    course_id: str,
    lesson_id: str,
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Get gems associated with a lesson."""
    saved_ids = _get_user_saved_gem_ids(session_id, db)
    lesson_gems = (
        db.query(LessonGem)
        .options(
            joinedload(LessonGem.gem).joinedload(Gem.category),
            joinedload(LessonGem.gem).joinedload(Gem.area),
            joinedload(LessonGem.gem).joinedload(Gem.created_by_user),
            joinedload(LessonGem.gem).joinedload(Gem.tag_links).joinedload(GemTagLink.tag),
        )
        .filter(LessonGem.lesson_id == lesson_id)
        .order_by(LessonGem.sort_order)
        .all()
    )
    published_gems = [lg.gem for lg in lesson_gems if lg.gem.status == GemPubStatus.PUBLISHED]
    gem_ids = [g.id for g in published_gems]
    saves_counts = _get_course_gem_saves_counts(gem_ids, db)
    return [_course_gem_to_card(g, saved_ids, saves_counts) for g in published_gems]
