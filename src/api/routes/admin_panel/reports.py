"""Reports — aggregated views for course progress, user progress, quizzes.

CSV export endpoints exist for each report type so the frontend can offer
a "Download CSV" button.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from src.core.permissions import require_admin
from src.db.models.learning_platform import (
    Area,
    Course,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    LessonProgress,
    LessonProgressStatus,
    Quiz,
    QuizAttempt,
    QuizAttemptResponse,
    QuizAttemptStatus,
    QuizQuestion,
    User,
    UserBadge,
    UserCertification,
)
from src.db.session import get_db
from src.schemas.admin_panel import (
    CourseProgressReportRow,
    QuizReportRow,
    UserProgressReportRow,
)


router = APIRouter(prefix="/reports")


# ============================================================================
# COURSE PROGRESS REPORT
# ============================================================================


def _course_progress_rows(db: Session, area_id: str | None = None) -> list[CourseProgressReportRow]:
    completed_case = case((Enrollment.status == EnrollmentStatus.completed, 1), else_=0)
    in_progress_case = case(
        (
            (Enrollment.status == EnrollmentStatus.active) & (Enrollment.progress_percent > 0),
            1,
        ),
        else_=0,
    )
    not_started_case = case(
        (
            (Enrollment.status == EnrollmentStatus.active) & (Enrollment.progress_percent == 0),
            1,
        ),
        else_=0,
    )

    q = (
        db.query(
            Course.id.label("cid"),
            Course.title.label("ctitle"),
            Area.name.label("aname"),
            func.count(Enrollment.id).label("enrolled"),
            func.sum(completed_case).label("completed"),
            func.sum(in_progress_case).label("in_progress"),
            func.sum(not_started_case).label("not_started"),
            func.avg(Enrollment.progress_percent).label("avg_progress"),
            func.avg(Enrollment.score).label("avg_score"),
        )
        .select_from(Course)
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .outerjoin(Area, Area.id == Course.area_id)
        .group_by(Course.id, Course.title, Area.name)
    )
    if area_id:
        q = q.filter(Course.area_id == area_id)

    rows = q.all()
    out: list[CourseProgressReportRow] = []
    for r in rows:
        enrolled = int(r.enrolled or 0)
        completed = int(r.completed or 0)
        rate = (completed / enrolled * 100) if enrolled > 0 else 0.0
        out.append(CourseProgressReportRow(
            course_id=r.cid,
            course_title=r.ctitle,
            area_name=r.aname,
            total_enrolled=enrolled,
            completed=completed,
            in_progress=int(r.in_progress or 0),
            not_started=int(r.not_started or 0),
            completion_rate=round(rate, 2),
            avg_progress=round(float(r.avg_progress or 0), 2),
            avg_score=round(float(r.avg_score), 2) if r.avg_score is not None else None,
        ))
    out.sort(key=lambda x: x.total_enrolled, reverse=True)
    return out


@router.get("/courses-progress", response_model=list[CourseProgressReportRow])
def course_progress_report(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    area_id: str | None = Query(None),
):
    """Per-course progress report."""
    return _course_progress_rows(db, area_id)


@router.get("/courses-progress/export")
def course_progress_export(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    area_id: str | None = Query(None),
):
    """CSV export of the courses-progress report."""
    rows = _course_progress_rows(db, area_id)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([
        "course_id", "course_title", "area_name", "total_enrolled",
        "completed", "in_progress", "not_started", "completion_rate",
        "avg_progress", "avg_score",
    ])
    for r in rows:
        w.writerow([
            r.course_id, r.course_title, r.area_name or "",
            r.total_enrolled, r.completed, r.in_progress, r.not_started,
            r.completion_rate, r.avg_progress,
            r.avg_score if r.avg_score is not None else "",
        ])
    buf.seek(0)
    filename = f"courses_progress_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============================================================================
# USER PROGRESS REPORT
# ============================================================================


def _user_progress_rows(
    db: Session,
    area_id: str | None = None,
    limit: int = 1000,
) -> list[UserProgressReportRow]:
    completed_case = case((Enrollment.status == EnrollmentStatus.completed, 1), else_=0)
    in_progress_case = case(
        (
            (Enrollment.status == EnrollmentStatus.active) & (Enrollment.progress_percent > 0),
            1,
        ),
        else_=0,
    )

    q = (
        db.query(
            User.id.label("uid"),
            User.first_name,
            User.last_name,
            User.email,
            Area.name.label("aname"),
            func.count(Enrollment.id).label("enrolls"),
            func.sum(completed_case).label("completed"),
            func.sum(in_progress_case).label("in_progress"),
            func.avg(Enrollment.progress_percent).label("avg_progress"),
            func.max(Enrollment.last_activity_at).label("last_activity"),
        )
        .select_from(User)
        .outerjoin(Enrollment, Enrollment.user_id == User.id)
        .outerjoin(Area, Area.id == User.area_id)
        .group_by(User.id, User.first_name, User.last_name, User.email, Area.name)
    )
    if area_id:
        q = q.filter(User.area_id == area_id)
    q = q.order_by(desc("enrolls")).limit(limit)
    rows = q.all()

    if not rows:
        return []

    user_ids = [r.uid for r in rows]
    badges_by_user = dict(
        db.query(UserBadge.user_id, func.count(UserBadge.id))
        .filter(UserBadge.user_id.in_(user_ids))
        .group_by(UserBadge.user_id)
        .all()
    )
    certs_by_user = dict(
        db.query(UserCertification.user_id, func.count(UserCertification.id))
        .filter(UserCertification.user_id.in_(user_ids))
        .group_by(UserCertification.user_id)
        .all()
    )

    out: list[UserProgressReportRow] = []
    for r in rows:
        out.append(UserProgressReportRow(
            user_id=r.uid,
            full_name=f"{r.first_name} {r.last_name}",
            email=r.email,
            area_name=r.aname,
            total_enrollments=int(r.enrolls or 0),
            completed=int(r.completed or 0),
            in_progress=int(r.in_progress or 0),
            avg_progress=round(float(r.avg_progress or 0), 2),
            badges_count=int(badges_by_user.get(r.uid, 0)),
            certifications_count=int(certs_by_user.get(r.uid, 0)),
            last_activity_at=r.last_activity,
        ))
    return out


@router.get("/users-progress", response_model=list[UserProgressReportRow])
def user_progress_report(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    area_id: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
):
    return _user_progress_rows(db, area_id, limit)


@router.get("/users-progress/export")
def user_progress_export(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    area_id: str | None = Query(None),
):
    rows = _user_progress_rows(db, area_id, limit=10000)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([
        "user_id", "full_name", "email", "area_name",
        "total_enrollments", "completed", "in_progress",
        "avg_progress", "badges_count", "certifications_count",
        "last_activity_at",
    ])
    for r in rows:
        w.writerow([
            r.user_id, r.full_name, r.email, r.area_name or "",
            r.total_enrollments, r.completed, r.in_progress,
            r.avg_progress, r.badges_count, r.certifications_count,
            r.last_activity_at.isoformat() if r.last_activity_at else "",
        ])
    buf.seek(0)
    filename = f"users_progress_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============================================================================
# QUIZ REPORT
# ============================================================================


@router.get("/quizzes", response_model=list[QuizReportRow])
def quiz_report(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    course_id: str | None = Query(None),
):
    """Per-quiz stats: pass rate, avg score, hardest question."""
    q = (
        db.query(Quiz, Lesson)
        .join(Lesson, Lesson.id == Quiz.lesson_id)
    )
    if course_id:
        from src.db.models.learning_platform import CourseModule
        q = q.join(CourseModule, CourseModule.id == Lesson.module_id).filter(CourseModule.course_id == course_id)
    quizzes = q.all()

    if not quizzes:
        return []

    out: list[QuizReportRow] = []
    for quiz, lesson in quizzes:
        # Resolve course title via lesson.module.course
        from src.db.models.learning_platform import CourseModule
        module = db.query(CourseModule).filter(CourseModule.id == lesson.module_id).first()
        course = db.query(Course).filter(Course.id == module.course_id).first() if module else None

        # Attempt stats
        attempts = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.quiz_id == quiz.id, QuizAttempt.status == QuizAttemptStatus.COMPLETED)
            .all()
        )
        total_attempts = len(attempts)
        passed = sum(1 for a in attempts if a.passed)
        failed = total_attempts - passed
        scores = [float(a.score) for a in attempts if a.score is not None]
        avg_score = round(sum(scores) / len(scores), 2) if scores else None
        pass_rate = round((passed / total_attempts * 100), 2) if total_attempts > 0 else 0.0

        # Hardest question = highest fail rate
        hardest_q_id = None
        hardest_q_text = None
        hardest_q_fail_rate: float | None = None

        questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).all()
        if questions and total_attempts > 0:
            best_fail_rate = -1.0
            for question in questions:
                resp_rows = (
                    db.query(
                        func.count(QuizAttemptResponse.id).label("total"),
                        func.sum(case((QuizAttemptResponse.is_correct == True, 0), else_=1)).label("wrong"),
                    )
                    .join(QuizAttempt, QuizAttempt.id == QuizAttemptResponse.attempt_id)
                    .filter(
                        QuizAttemptResponse.question_id == question.id,
                        QuizAttempt.status == QuizAttemptStatus.COMPLETED,
                    )
                    .first()
                )
                total = int(resp_rows.total or 0) if resp_rows else 0
                wrong = int(resp_rows.wrong or 0) if resp_rows else 0
                if total > 0:
                    fr = (wrong / total) * 100
                    if fr > best_fail_rate:
                        best_fail_rate = fr
                        hardest_q_id = question.id
                        hardest_q_text = question.question_text
                        hardest_q_fail_rate = round(fr, 2)

        out.append(QuizReportRow(
            quiz_id=quiz.id,
            lesson_title=lesson.title,
            course_title=course.title if course else "",
            total_attempts=total_attempts,
            passed=passed,
            failed=failed,
            pass_rate=pass_rate,
            avg_score=avg_score,
            hardest_question_id=hardest_q_id,
            hardest_question_text=hardest_q_text,
            hardest_question_fail_rate=hardest_q_fail_rate,
        ))
    out.sort(key=lambda x: x.total_attempts, reverse=True)
    return out
