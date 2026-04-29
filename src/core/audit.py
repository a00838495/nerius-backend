"""Audit logging helpers.

Use these from any route to record critical actions. The helper is fail-safe —
if writing the audit log fails, the request still succeeds (audit failures are
logged but never raised).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session as DBSession

from src.db.models.audit import AuditLog


logger = logging.getLogger(__name__)


# Canonical action names. Keep this list as the single source of truth so
# the frontend can build filters from /superadmin/audit-logs/actions.
class AuditAction:
    # Auth
    AUTH_LOGIN = "auth.login"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_LOGOUT = "auth.logout"

    # User / role management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_SUSPENDED = "user.suspended"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"
    USER_DELETED = "user.deleted"
    USER_PASSWORD_RESET = "user.password_reset"

    # Course management
    COURSE_CREATED = "course.created"
    COURSE_UPDATED = "course.updated"
    COURSE_PUBLISHED = "course.published"
    COURSE_ARCHIVED = "course.archived"
    COURSE_DELETED = "course.deleted"

    # Course assignments
    ASSIGNMENT_CREATED = "assignment.created"
    ASSIGNMENT_DELETED = "assignment.deleted"
    ASSIGNMENT_BULK_CREATED = "assignment.bulk_created"

    # Enrollments
    ENROLLMENT_UPDATED = "enrollment.updated"
    ENROLLMENT_CANCELLED = "enrollment.cancelled"

    # Areas
    AREA_CREATED = "area.created"
    AREA_UPDATED = "area.updated"
    AREA_DELETED = "area.deleted"

    # Forum moderation
    FORUM_POST_HIDDEN = "forum.post_hidden"
    FORUM_POST_PUBLISHED = "forum.post_published"
    FORUM_POST_UPDATED = "forum.post_updated"
    FORUM_POST_DELETED = "forum.post_deleted"
    FORUM_COMMENT_DELETED = "forum.comment_deleted"

    # Gems (global)
    GEM_CREATED = "gem.created"
    GEM_UPDATED = "gem.updated"
    GEM_DELETED = "gem.deleted"
    GEM_CATEGORY_CREATED = "gem_category.created"
    GEM_CATEGORY_UPDATED = "gem_category.updated"
    GEM_CATEGORY_DELETED = "gem_category.deleted"

    # Badges (global)
    BADGE_CREATED = "badge.created"
    BADGE_UPDATED = "badge.updated"
    BADGE_DELETED = "badge.deleted"

    # Session management
    SESSION_REVOKED = "session.revoked"
    SESSION_REVOKED_ALL = "session.revoked_all"
    SESSION_CLEANUP = "session.cleanup"

    # Certifications
    CERT_APPROVED = "certification.approved"
    CERT_REJECTED = "certification.rejected"
    CERT_REVOKED = "certification.revoked"
    CERT_ISSUED = "certification.issued"


# All known actions — used by the /audit-logs/actions endpoint
ALL_ACTIONS: list[str] = [
    v for k, v in vars(AuditAction).items()
    if not k.startswith("_") and isinstance(v, str)
]


def log_action(
    db: DBSession,
    action: str,
    *,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    description: str | None = None,
    extra_data: dict[str, Any] | None = None,
    request: Request | None = None,
    commit: bool = True,
) -> AuditLog | None:
    """Record an audit log entry.

    Args:
        db: Active SQLAlchemy session.
        action: Canonical action name (use `AuditAction.*` constants).
        user_id: Who performed the action (None for anonymous/system actions).
        resource_type: Type of resource affected (e.g. "course", "user").
        resource_id: ID of the resource affected.
        description: Human-readable summary.
        extra_data: Arbitrary structured payload (kept as JSON).
        request: Optional FastAPI Request to extract IP and user-agent.
        commit: Whether to commit the session. Pass False if the caller is
                managing the transaction.

    Returns:
        The persisted AuditLog instance, or None if writing failed.
    """
    try:
        ip_address: str | None = None
        user_agent: str | None = None
        if request is not None:
            try:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
            except Exception:
                pass

        entry = AuditLog(
            id=_uuid(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            extra_data=extra_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(entry)
        if commit:
            db.commit()
        else:
            db.flush()
        return entry
    except Exception as exc:  # pragma: no cover — defensive
        logger.error("Failed to write audit log for action=%s: %s", action, exc)
        try:
            db.rollback()
        except Exception:
            pass
        return None


def _uuid() -> str:
    import uuid
    return str(uuid.uuid4())
