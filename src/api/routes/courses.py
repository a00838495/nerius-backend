"""Courses routes."""

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session, joinedload

from src.core.auth import validate_session
from src.db.session import get_db
from src.db.models.learning_platform import (
    User,
    Course,
    Enrollment,
    EnrollmentStatus,
    PublicationStatus,
    CourseModule,
    Lesson,
    LessonResource,
    LessonProgress,
    LessonProgressStatus,
)
from src.schemas.user import (
    CourseRead,
    EnrollmentRead,
    CourseDetailedRead,
    ModuleDetailedRead,
    ModuleBasicRead,
    LessonDetailedRead,
    LessonBasicRead,
    LessonResourceRead,
    LessonProgressRead,
    LessonProgressUpdate,
    LessonProgressUpdateResponse,
)

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

    session = validate_session(session_id)
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


@router.get("", response_model=list[CourseRead])
def get_available_courses(db: Session = Depends(get_db)):
    """Get all published courses in the platform."""
    courses = (
        db.query(Course)
        .filter(Course.status == "published")
        .all()
    )
    return [
        CourseRead(
            id=course.id,
            title=course.title,
            description=course.description,
            status=course.status.value,
            estimated_minutes=course.estimated_minutes,
            cover_url=course.cover_url,
        )
        for course in courses
    ]


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


@router.get("/user/recommended", response_model=list[CourseRead])
def get_recommended_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get recommended courses for the current user.
    Returns all published courses where the user is NOT enrolled.
    """
    # Get all course IDs where user has an enrollment (any status)
    enrolled_course_ids = (
        db.query(Enrollment.course_id)
        .filter(Enrollment.user_id == current_user.id)
        .all()
    )
    enrolled_ids = [course_id for (course_id,) in enrolled_course_ids]
    
    # Get all published courses NOT in the enrolled list
    recommended_courses = (
        db.query(Course)
        .filter(
            Course.status == PublicationStatus.PUBLISHED,
            Course.id.notin_(enrolled_ids) if enrolled_ids else True,
        )
        .all()
    )
    
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
    focus_module_id: str | None = None,
    focus_lesson_id: str | None = None,
):
    """
    Get detailed course information with all modules and lessons.
    
    By default, returns detailed information (including resources and progress) for the first module and first lesson.
    Use focus_module_id and focus_lesson_id query parameters to load detailed info for a specific lesson.
    
    - **course_id**: UUID of the course
    - **focus_module_id** (optional): UUID of the module to focus on
    - **focus_lesson_id** (optional): UUID of the lesson to focus on (requires focus_module_id)
    
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
    
    # Prepare response
    first_module_data = None
    other_modules_data = []
    
    # Sort modules by sort_order
    sorted_modules = sorted(course.modules, key=lambda m: m.sort_order)
    
    # Determine which module and lesson to focus on
    focus_module = None
    focus_lesson = None
    
    if focus_module_id:
        # Find the specified module
        focus_module = next((m for m in sorted_modules if m.id == focus_module_id), None)
        if not focus_module:
            raise HTTPException(
                status_code=404,
                detail="Focus module not found in this course",
            )
        
        if focus_lesson_id:
            # Find the specified lesson in the focus module
            focus_lesson = next((l for l in focus_module.lessons if l.id == focus_lesson_id), None)
            if not focus_lesson:
                raise HTTPException(
                    status_code=404,
                    detail="Focus lesson not found in the specified module",
                )
        else:
            # Default to first lesson of the focus module
            sorted_focus_lessons = sorted(focus_module.lessons, key=lambda l: l.sort_order)
            focus_lesson = sorted_focus_lessons[0] if sorted_focus_lessons else None
    else:
        # Default to first module and first lesson
        if sorted_modules:
            focus_module = sorted_modules[0]
            sorted_focus_lessons = sorted(focus_module.lessons, key=lambda l: l.sort_order)
            focus_lesson = sorted_focus_lessons[0] if sorted_focus_lessons else None
    
    # Build modules structure
    for module in sorted_modules:
        # Sort lessons by sort_order
        sorted_lessons = sorted(module.lessons, key=lambda l: l.sort_order)
        
        if focus_module and module.id == focus_module.id:
            # This is the focus module: detailed with all lessons including progress
            detailed_lessons = []
            
            for lesson in sorted_lessons:
                # Get progress for this lesson
                lesson_progress = lesson_progress_map.get(lesson.id)
                progress_data = None
                if lesson_progress:
                    progress_data = LessonProgressRead(
                        lesson_id=lesson.id,
                        status=lesson_progress.status.value,
                        progress_percent=float(lesson_progress.progress_percent),
                    )
                
                # Load resources only for the focus lesson
                resources = []
                if focus_lesson and lesson.id == focus_lesson.id:
                    resources_list = (
                        db.query(LessonResource)
                        .filter(LessonResource.lesson_id == lesson.id)
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
                
                detailed_lessons.append(
                    LessonDetailedRead(
                        id=lesson.id,
                        title=lesson.title,
                        description=lesson.description,
                        sort_order=lesson.sort_order,
                        estimated_minutes=lesson.estimated_minutes,
                        resources=resources,
                        progress=progress_data,
                    )
                )
            
            first_module_data = ModuleDetailedRead(
                id=module.id,
                title=module.title,
                sort_order=module.sort_order,
                lessons=detailed_lessons,
            )
        else:
            # Other modules: basic info only
            basic_lessons = [
                LessonBasicRead(
                    id=lesson.id,
                    title=lesson.title,
                    sort_order=lesson.sort_order,
                    estimated_minutes=lesson.estimated_minutes,
                )
                for lesson in sorted_lessons
            ]
            
            other_modules_data.append(
                ModuleBasicRead(
                    id=module.id,
                    title=module.title,
                    sort_order=module.sort_order,
                    lessons=basic_lessons,
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
        first_module=first_module_data,
        other_modules=other_modules_data,
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
    else:
        # Create new progress entry
        lesson_progress = LessonProgress(
            id=str(uuid.uuid4()),
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
            status=status_enum,
            progress_percent=Decimal(str(progress_data.progress_percent)),
            time_spent_seconds=progress_data.time_spent_seconds,
        )
        db.add(lesson_progress)
    
    # Update enrollment last_activity_at
    enrollment.last_activity_at = datetime.now()
    
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
            enrollment.completed_at = datetime.now()
    
    db.commit()
    db.refresh(lesson_progress)
    db.refresh(enrollment)
    
    return LessonProgressUpdateResponse(
        lesson_id=lesson_progress.lesson_id,
        status=lesson_progress.status.value,
        progress_percent=float(lesson_progress.progress_percent),
        time_spent_seconds=lesson_progress.time_spent_seconds,
        enrollment_progress_percent=float(enrollment.progress_percent),
    )
