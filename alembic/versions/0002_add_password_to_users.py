"""add password to users

Revision ID: 0002_add_password_to_users
Revises: 0001_create_users_table
Create Date: 2026-03-11 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_password_to_users"
down_revision: Union[str, Sequence[str], None] = "0001_create_users_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password", sa.String(length=255), nullable=False, server_default=""),
    )
    # After the column is added, remove the server default so new inserts must provide a password
    op.alter_column("users", "password", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "password")
