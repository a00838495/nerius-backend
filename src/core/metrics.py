"""Request metrics middleware.

Records per-request data (method, path, status, duration, user) into
the `request_metrics` table. Designed to be lightweight and fail-safe —
any exception during metric recording is swallowed so it never breaks
the actual API request.

To avoid bloating the table, requests to noisy/health endpoints are skipped
by default (configurable via SKIP_PATH_PREFIXES below).
"""

from __future__ import annotations

import logging
import re
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.auth import validate_session
from src.db.models.audit import RequestMetric
from src.db.session import SessionLocal


logger = logging.getLogger(__name__)


# Paths to skip — do not write metrics for these
SKIP_PATH_PREFIXES: tuple[str, ...] = (
    "/api/v1/health",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/scalar",
    "/favicon.ico",
)


# Patterns to normalize dynamic segments (UUIDs, numeric IDs) so we can group
# them by route shape rather than literal path. /courses/abc-123 → /courses/{id}
_UUID_RE = re.compile(
    r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
_NUMERIC_ID_RE = re.compile(r"/\d+(?=/|$)")


def normalize_path(path: str) -> str:
    """Replace UUIDs and numeric IDs with `{id}` for grouping."""
    path = _UUID_RE.sub("/{id}", path)
    path = _NUMERIC_ID_RE.sub("/{id}", path)
    return path


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip noisy paths early
        if any(path.startswith(p) for p in SKIP_PATH_PREFIXES):
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            try:
                duration_ms = int((time.perf_counter() - start) * 1000)
                _record_metric(
                    request=request,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                )
            except Exception as exc:  # pragma: no cover — defensive
                logger.error("Failed to record request metric: %s", exc)


def _record_metric(
    *,
    request: Request,
    path: str,
    status_code: int,
    duration_ms: int,
) -> None:
    """Insert a metric row using its own short-lived DB session.

    We open a dedicated session so we don't interfere with the request's
    own session lifecycle.
    """
    method = request.method
    normalized = normalize_path(path)
    ip_address = request.client.host if request.client else None
    session_id = request.cookies.get("session_id")

    db = SessionLocal()
    try:
        user_id: str | None = None
        if session_id:
            try:
                # Lightweight resolution — does not refresh last_activity_at here
                from src.db.models.learning_platform import Session as SessionModel
                row = (
                    db.query(SessionModel.user_id)
                    .filter(SessionModel.id == session_id)
                    .first()
                )
                user_id = row[0] if row else None
            except Exception:
                user_id = None

        metric = RequestMetric(
            method=method,
            path=normalized,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            ip_address=ip_address,
        )
        db.add(metric)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        raise
    finally:
        db.close()
