"""Seed the database with mock data."""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from src.db.session import SessionLocal, engine
from src.db.models.base import Base
from src.db.models.learning_platform import (
    Area,
    User,
    Role,
    UserRole,
    Course,
    CourseModule,
    Lesson,
    LessonResource,
    Enrollment,
    ForumPost,
    ForumComment,
    RoleName,
    UserStatus,
    PublicationStatus,
    EnrollmentStatus,
    ResourceType,
)
from src.core.auth import hash_password


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def seed_database():
    """Seed the database with mock data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("Database already seeded, skipping...")
            return

        # Create areas
        area_tech = Area(
            id=generate_uuid(),
            name="Technology",
            created_at=datetime.utcnow(),
        )
        area_business = Area(
            id=generate_uuid(),
            name="Business",
            created_at=datetime.utcnow(),
        )
        db.add_all([area_tech, area_business])
        db.flush()

        # Create roles
        role_super_admin = Role(
            id=generate_uuid(),
            name=RoleName.SUPER_ADMIN,
            created_at=datetime.utcnow(),
        )
        role_admin = Role(
            id=generate_uuid(),
            name=RoleName.CONTENT_ADMIN,
            created_at=datetime.utcnow(),
        )
        role_user = Role(
            id=generate_uuid(),
            name=RoleName.LEARNER,
            created_at=datetime.utcnow(),
        )
        db.add_all([role_super_admin, role_admin, role_user])
        db.flush()

        # Create users
        user_super_admin = User(
            id=generate_uuid(),
            area_id=area_tech.id,
            email="superadmin@example.com",
            first_name="Super",
            last_name="Admin",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Male",
            created_at=datetime.utcnow(),
        )

        user_admin = User(
            id=generate_uuid(),
            area_id=area_business.id,
            email="admin@example.com",
            first_name="Content",
            last_name="Admin",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Female",
            created_at=datetime.utcnow(),
        )

        user_learner = User(
            id=generate_uuid(),
            area_id=area_tech.id,
            email="user@example.com",
            first_name="Juan",
            last_name="Perez",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Male",
            created_at=datetime.utcnow(),
        )

        db.add_all([user_super_admin, user_admin, user_learner])
        db.flush()

        # Assign roles to users
        user_role_super = UserRole(
            user_id=user_super_admin.id,
            role_id=role_super_admin.id,
            created_at=datetime.utcnow(),
        )
        user_role_admin = UserRole(
            user_id=user_admin.id,
            role_id=role_admin.id,
            created_at=datetime.utcnow(),
        )
        user_role_user = UserRole(
            user_id=user_learner.id,
            role_id=role_user.id,
            created_at=datetime.utcnow(),
        )
        db.add_all([user_role_super, user_role_admin, user_role_user])
        db.flush()

        # Create courses
        course1 = Course(
            id=generate_uuid(),
            area_id=area_tech.id,
            title="Python for Beginners",
            description="Learn the basics of Python programming language. Perfect for beginners with no prior experience.",
            status=PublicationStatus.PUBLISHED,
            estimated_minutes=480,
            cover_url="https://via.placeholder.com/300x200?text=Python",
            created_by_user_id=user_admin.id,
            created_at=datetime.utcnow(),
        )

        course2 = Course(
            id=generate_uuid(),
            area_id=area_tech.id,
            title="Web Development with FastAPI",
            description="Build modern web applications with FastAPI, a modern, fast web framework for building APIs.",
            status=PublicationStatus.PUBLISHED,
            estimated_minutes=600,
            cover_url="https://via.placeholder.com/300x200?text=FastAPI",
            created_by_user_id=user_admin.id,
            created_at=datetime.utcnow(),
        )

        course3 = Course(
            id=generate_uuid(),
            area_id=area_business.id,
            title="Business Management 101",
            description="Essential business management principles and practices for aspiring leaders.",
            status=PublicationStatus.PUBLISHED,
            estimated_minutes=360,
            cover_url="https://via.placeholder.com/300x200?text=Business",
            created_by_user_id=user_admin.id,
            created_at=datetime.utcnow(),
        )

        course4 = Course(
            id=generate_uuid(),
            area_id=area_tech.id,
            title="Database Design and SQL",
            description="Master database design principles and SQL queries for data management.",
            status=PublicationStatus.PUBLISHED,
            estimated_minutes=420,
            cover_url="https://via.placeholder.com/300x200?text=Database",
            created_by_user_id=user_admin.id,
            created_at=datetime.utcnow(),
        )

        course5 = Course(
            id=generate_uuid(),
            area_id=area_business.id,
            title="Leadership Skills",
            description="Develop essential leadership skills and become an effective team leader.",
            status=PublicationStatus.PUBLISHED,
            estimated_minutes=300,
            cover_url="https://via.placeholder.com/300x200?text=Leadership",
            created_by_user_id=user_admin.id,
            created_at=datetime.utcnow(),
        )

        db.add_all([course1, course2, course3, course4, course5])
        db.flush()

        # Create modules and lessons for course1
        module1 = CourseModule(
            id=generate_uuid(),
            course_id=course1.id,
            title="Introduction to Python",
            sort_order=1,
            created_at=datetime.utcnow(),
        )
        lesson1 = Lesson(
            id=generate_uuid(),
            module_id=module1.id,
            title="Python Basics",
            description="Learn the basics of Python syntax and variables.",
            sort_order=1,
            estimated_minutes=60,
            created_at=datetime.utcnow(),
        )
        resource1 = LessonResource(
            id=generate_uuid(),
            lesson_id=lesson1.id,
            resource_type=ResourceType.VIDEO,
            title="Python Basics Video",
            external_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
            duration_seconds=3600,
            created_at=datetime.utcnow(),
        )

        db.add_all([module1, lesson1, resource1])
        db.flush()

        # Create modules and lessons for course2
        module2 = CourseModule(
            id=generate_uuid(),
            course_id=course2.id,
            title="FastAPI Fundamentals",
            sort_order=1,
            created_at=datetime.utcnow(),
        )
        lesson2 = Lesson(
            id=generate_uuid(),
            module_id=module2.id,
            title="Setting up FastAPI",
            description="Learn how to set up a FastAPI project.",
            sort_order=1,
            estimated_minutes=45,
            created_at=datetime.utcnow(),
        )
        resource2 = LessonResource(
            id=generate_uuid(),
            lesson_id=lesson2.id,
            resource_type=ResourceType.PDF,
            title="FastAPI Setup Guide",
            external_url="https://example.com/fastapi-setup.pdf",
            created_at=datetime.utcnow(),
        )

        db.add_all([module2, lesson2, resource2])
        db.flush()

        # Create enrollments for the learner user
        enrollment1 = Enrollment(
            id=generate_uuid(),
            user_id=user_learner.id,
            course_id=course1.id,
            status=EnrollmentStatus.active,
            progress_percent=45,
            created_at=datetime.utcnow(),
        )

        enrollment2 = Enrollment(
            id=generate_uuid(),
            user_id=user_learner.id,
            course_id=course2.id,
            status=EnrollmentStatus.active,
            progress_percent=20,
            created_at=datetime.utcnow(),
        )

        enrollment3 = Enrollment(
            id=generate_uuid(),
            user_id=user_learner.id,
            course_id=course3.id,
            status=EnrollmentStatus.active,
            progress_percent=0,
            created_at=datetime.utcnow(),
        )

        db.add_all([enrollment1, enrollment2, enrollment3])

        # Create forum posts
        forum_post1 = ForumPost(
            id=generate_uuid(),
            area_id=area_tech.id,
            author_user_id=user_learner.id,
            title="Best practices for Python development",
            content="I'm looking for advice on best practices when developing Python applications. What tools and methodologies do you recommend for a beginner? I've heard about virtual environments, testing frameworks like pytest, and code formatting tools like black. Would love to hear your experiences!",
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        forum_post2 = ForumPost(
            id=generate_uuid(),
            area_id=area_tech.id,
            author_user_id=user_admin.id,
            title="Database design tips for beginners",
            content="Hello everyone! I'm sharing some database design tips for those just starting out. First, always normalize your data to at least 3NF to avoid redundancy. Second, use proper indexes on frequently queried columns. Third, think about your foreign key relationships carefully. What other tips would you add?",
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        forum_post3 = ForumPost(
            id=generate_uuid(),
            area_id=area_business.id,
            author_user_id=user_super_admin.id,
            title="Leadership in remote teams",
            content="With the rise of remote work, leadership strategies have had to evolve. What are your experiences leading remote teams? I've found that clear communication, regular check-ins, and trust are crucial. Async communication tools have been a game-changer for our team.",
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        forum_post4 = ForumPost(
            id=generate_uuid(),
            area_id=area_tech.id,
            author_user_id=user_learner.id,
            title="FastAPI vs Flask: Which to choose?",
            content="I'm starting a new web project and trying to decide between FastAPI and Flask. FastAPI seems modern with automatic API documentation and type hints, but Flask has a huge ecosystem. What are your thoughts? When would you choose one over the other?",
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        forum_post5 = ForumPost(
            id=generate_uuid(),
            area_id=area_business.id,
            author_user_id=user_admin.id,
            title="Time management strategies for professionals",
            content="As a professional juggling multiple projects, I've learned the importance of time management. I use the Pomodoro technique and time-blocking in my calendar. Also, saying 'no' to non-essential tasks has been liberating. What strategies work for you?",
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        db.add_all([forum_post1, forum_post2, forum_post3, forum_post4, forum_post5])
        db.flush()

        # Create forum comments
        comment1_1 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post1.id,
            author_user_id=user_admin.id,
            content="Great question! I'd definitely recommend starting with virtual environments (venv or conda). For testing, pytest is excellent. Also, check out pylint or flake8 for code quality checks.",
            created_at=datetime.utcnow(),
        )

        comment1_2 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post1.id,
            author_user_id=user_super_admin.id,
            content="Don't forget about type hints! They're not just for documentation - tools like mypy can catch bugs before runtime. Also, pre-commit hooks are great for enforcing standards.",
            created_at=datetime.utcnow(),
        )

        comment2_1 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post2.id,
            author_user_id=user_learner.id,
            content="This is super helpful! Could you elaborate on when NOT to normalize? I've heard that sometimes denormalization is acceptable for performance reasons.",
            created_at=datetime.utcnow(),
        )

        # Reply to comment
        comment2_1_1 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post2.id,
            author_user_id=user_admin.id,
            parent_comment_id=comment2_1.id,
            content="Good question! Denormalization can be useful in read-heavy applications where you need better query performance. For example, storing calculated totals instead of computing them every time.",
            created_at=datetime.utcnow(),
        )

        comment3_1 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post3.id,
            author_user_id=user_learner.id,
            content="Great insights! We've been struggling with time zones in our team. Any tips on scheduling meetings across multiple time zones?",
            created_at=datetime.utcnow(),
        )

        comment4_1 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post4.id,
            author_user_id=user_admin.id,
            content="FastAPI is my go-to for new projects. The automatic API docs alone save so much time. The async support is also better than Flask's. That said, Flask is still great for simpler projects.",
            created_at=datetime.utcnow(),
        )

        comment4_2 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post4.id,
            author_user_id=user_super_admin.id,
            content="I'd add that FastAPI's dependency injection system is really powerful for larger applications. Makes testing much easier too.",
            created_at=datetime.utcnow(),
        )

        db.add_all([
            comment1_1, comment1_2, comment2_1, comment2_1_1, 
            comment3_1, comment4_1, comment4_2
        ])

        # Commit all changes
        db.commit()
        print("✓ Database seeded successfully!")
        print("\n📝 Mock Users Created:")
        print("  - Super Admin: superadmin@example.com (password: password123)")
        print("  - Content Admin: admin@example.com (password: password123)")
        print("  - Learner: user@example.com (password: password123)")
        print("\n📚 Mock Courses Created:")
        print("  - Python for Beginners")
        print("  - Web Development with FastAPI")
        print("  - Business Management 101")
        print("  - Database Design and SQL")
        print("  - Leadership Skills")
        print("\n💬 Mock Forum Posts Created:")
        print("  - 5 forum posts with comments")

    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
