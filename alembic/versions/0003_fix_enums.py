"""fix enum values to uppercase

Revision ID: 0003_fix_enums
Revises: 0002_add_password_to_users
Create Date: 2026-03-11 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_fix_enums"
down_revision: Union[str, Sequence[str], None] = "0002_add_password_to_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update user_status_enum values in users table
    op.execute("UPDATE users SET status = 'ACTIVE' WHERE status = 'active'")
    op.execute("UPDATE users SET status = 'INACTIVE' WHERE status = 'inactive'")
    op.execute("UPDATE users SET status = 'SUSPENDED' WHERE status = 'suspended'")

    # Update course_status_enum values in courses table
    op.execute("UPDATE courses SET status = 'DRAFT' WHERE status = 'draft'")
    op.execute("UPDATE courses SET status = 'PUBLISHED' WHERE status = 'published'")
    op.execute("UPDATE courses SET status = 'ARCHIVED' WHERE status = 'archived'")

    # Update role_name_enum values in roles table
    op.execute("UPDATE roles SET name = 'SUPER_ADMIN' WHERE name = 'super_admin'")
    op.execute("UPDATE roles SET name = 'CONTENT_ADMIN' WHERE name = 'content_admin'")
    op.execute("UPDATE roles SET name = 'LEARNER' WHERE name = 'learner'")

    # Update enrollment_status_enum values in enrollments table
    op.execute("UPDATE enrollments SET status = 'ACTIVE' WHERE status = 'active'")
    op.execute("UPDATE enrollments SET status = 'COMPLETED' WHERE status = 'completed'")
    op.execute("UPDATE enrollments SET status = 'DROPPED' WHERE status = 'dropped'")

    # Update lesson_progress_status_enum values in lesson_progress table
    op.execute("UPDATE lesson_progress SET status = 'NOT_STARTED' WHERE status = 'not_started'")
    op.execute("UPDATE lesson_progress SET status = 'IN_PROGRESS' WHERE status = 'in_progress'")
    op.execute("UPDATE lesson_progress SET status = 'COMPLETED' WHERE status = 'completed'")

    # Update lesson_resource_type_enum values in lesson_resources table
    op.execute("UPDATE lesson_resources SET resource_type = 'VIDEO' WHERE resource_type = 'video'")
    op.execute("UPDATE lesson_resources SET resource_type = 'PDF' WHERE resource_type = 'pdf'")
    op.execute("UPDATE lesson_resources SET resource_type = 'PODCAST' WHERE resource_type = 'podcast'")
    op.execute("UPDATE lesson_resources SET resource_type = 'SLIDE' WHERE resource_type = 'slide'")

    # Update forum_post_status_enum values in forum_posts table
    op.execute("UPDATE forum_posts SET status = 'DRAFT' WHERE status = 'draft'")
    op.execute("UPDATE forum_posts SET status = 'PUBLISHED' WHERE status = 'published'")
    op.execute("UPDATE forum_posts SET status = 'ARCHIVED' WHERE status = 'archived'")


def downgrade() -> None:
    # Revert user_status_enum values
    op.execute("UPDATE users SET status = 'active' WHERE status = 'ACTIVE'")
    op.execute("UPDATE users SET status = 'inactive' WHERE status = 'INACTIVE'")
    op.execute("UPDATE users SET status = 'suspended' WHERE status = 'SUSPENDED'")

    # Revert course_status_enum values
    op.execute("UPDATE courses SET status = 'draft' WHERE status = 'DRAFT'")
    op.execute("UPDATE courses SET status = 'published' WHERE status = 'PUBLISHED'")
    op.execute("UPDATE courses SET status = 'archived' WHERE status = 'ARCHIVED'")

    # Revert role_name_enum values
    op.execute("UPDATE roles SET name = 'super_admin' WHERE name = 'SUPER_ADMIN'")
    op.execute("UPDATE roles SET name = 'content_admin' WHERE name = 'CONTENT_ADMIN'")
    op.execute("UPDATE roles SET name = 'learner' WHERE name = 'LEARNER'")

    # Revert enrollment_status_enum values
    op.execute("UPDATE enrollments SET status = 'active' WHERE status = 'ACTIVE'")
    op.execute("UPDATE enrollments SET status = 'completed' WHERE status = 'COMPLETED'")
    op.execute("UPDATE enrollments SET status = 'dropped' WHERE status = 'DROPPED'")

    # Revert lesson_progress_status_enum values
    op.execute("UPDATE lesson_progress SET status = 'not_started' WHERE status = 'NOT_STARTED'")
    op.execute("UPDATE lesson_progress SET status = 'in_progress' WHERE status = 'IN_PROGRESS'")
    op.execute("UPDATE lesson_progress SET status = 'completed' WHERE status = 'COMPLETED'")

    # Revert lesson_resource_type_enum values
    op.execute("UPDATE lesson_resources SET resource_type = 'video' WHERE resource_type = 'VIDEO'")
    op.execute("UPDATE lesson_resources SET resource_type = 'pdf' WHERE resource_type = 'PDF'")
    op.execute("UPDATE lesson_resources SET resource_type = 'podcast' WHERE resource_type = 'PODCAST'")
    op.execute("UPDATE lesson_resources SET resource_type = 'slide' WHERE resource_type = 'SLIDE'")

    # Revert forum_post_status_enum values
    op.execute("UPDATE forum_posts SET status = 'draft' WHERE status = 'DRAFT'")
    op.execute("UPDATE forum_posts SET status = 'published' WHERE status = 'PUBLISHED'")
    op.execute("UPDATE forum_posts SET status = 'archived' WHERE status = 'ARCHIVED'")

