"""Audit log and request metric models.

Kept in a separate file from learning_platform.py to avoid bloating that module.
No back_populates relationships to User to keep this isolated; we use plain FKs
and resolve user info via explicit joins when needed.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CHAR, JSON, TIMESTAMP, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base
from src.db.models.learning_platform import UUIDPrimaryKeyMixin, CreatedAtMixin


class AuditLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Audit log for critical actions across the platform.

    Examples of actions tracked:
        - auth.login, auth.logout, auth.login_failed
        - user.role_changed, user.suspended, user.activated
        - course.created, course.published, course.deleted
        - session.revoked, session.cleanup
    """
    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )


class RequestMetric(Base):
    """Per-request metric. Populated by middleware. High-volume table.

    Stored as a separate, lightweight model — no UUID, just an autoincrement
    integer to keep inserts fast.
    """
    __tablename__ = "request_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        Index("idx_request_metrics_path", "path"),
        Index("idx_request_metrics_status", "status_code"),
        Index("idx_request_metrics_created_at", "created_at"),
        Index("idx_request_metrics_user_id", "user_id"),
    )
