"""Clear all data from the database."""

from sqlalchemy import text
from src.db.session import SessionLocal


def clear_database():
    """Clear all data from the database."""
    db = SessionLocal()
    try:
        print("Clearing database...")
        
        # Disable foreign key checks temporarily
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        # Children → parents order (FK checks are disabled above, so order is
        # only a safety net). Covers gems, quizzes, certifications, audit logs
        # and sessions added after the original seed.
        tables = [
            "analytics_events",
            "request_metrics",
            "audit_logs",
            "sessions",
            "quiz_attempt_responses",
            "quiz_attempts",
            "quiz_question_options",
            "quiz_questions",
            "quizzes",
            "user_certifications",
            "course_certifications",
            "user_course_grants",
            "user_gem_collection",
            "lesson_gems",
            "course_gems",
            "gem_tag_links",
            "gem_area_links",
            "gem_tags",
            "gems",
            "gem_categories",
            "user_badges",
            "course_badges",
            "lesson_progress",
            "lesson_resources",
            "lessons",
            "course_modules",
            "forum_comments",
            "forum_posts",
            "course_assignments",
            "enrollments",
            "courses",
            "badges",
            "user_roles",
            "users",
            "roles",
            "areas",
        ]
        
        for table in tables:
            db.execute(text(f"DELETE FROM {table}"))
            print(f"  ✓ Cleared {table}")
        
        # Re-enable foreign key checks
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        
        db.commit()
        print("\n✓ Database cleared successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error clearing database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_database()
