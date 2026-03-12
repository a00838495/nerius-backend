"""Add forum data to existing database."""

import uuid
from datetime import datetime

from src.db.session import SessionLocal
from src.db.models.learning_platform import (
    Area,
    User,
    ForumPost,
    ForumComment,
    PublicationStatus,
)


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def add_forum_data():
    """Add forum posts and comments to the database."""
    db = SessionLocal()
    try:
        # Check if forum posts already exist
        existing_posts = db.query(ForumPost).count()
        if existing_posts > 0:
            print(f"✓ Forum posts already exist ({existing_posts} posts). Skipping...")
            return

        # Get existing areas and users
        area_tech = db.query(Area).filter(Area.name == "Technology").first()
        area_business = db.query(Area).filter(Area.name == "Business").first()
        
        user_learner = db.query(User).filter(User.email == "user@example.com").first()
        user_admin = db.query(User).filter(User.email == "admin@example.com").first()
        user_super_admin = db.query(User).filter(User.email == "superadmin@example.com").first()

        if not all([area_tech, area_business, user_learner, user_admin, user_super_admin]):
            print("✗ Required areas or users not found. Please run seed_database first.")
            return

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

        db.commit()
        print("✓ Forum data added successfully!")
        print("\n💬 Created:")
        print("  - 5 forum posts")
        print("  - 7 comments (including 1 nested reply)")

    except Exception as e:
        db.rollback()
        print(f"✗ Error adding forum data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_forum_data()
