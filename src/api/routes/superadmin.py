"""Super-admin endpoints: system health, sessions, metrics, audit logs, admin activity.

All endpoints require the `super_admin` role via `require_super_admin` dependency.
"""

from __future__ import annotations

import csv
import io
import os
import platform
import sys
import time
from datetime import datetime, timedelta
from typing import Any

import psutil
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import case, desc, func, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core.audit import ALL_ACTIONS, AuditAction, log_action
from src.core.permissions import require_super_admin
from src.db.models.audit import AuditLog, RequestMetric
from src.db.models.learning_platform import (
    Role,
    Session as UserSession,
    User,
    UserRole,
)
from src.db.session import get_db
from src.schemas.superadmin import (
    ActiveUsersBucketRead,
    ActiveUsersRead,
    AdminActivityRead,
    AdminRoleHistoryRead,
    AuditActionRead,
    AuditLogListRead,
    AuditLogRead,
    CleanupResponse,
    CPUInfo,
    DatabaseHealthRead,
    DatabaseMetricsRead,
    DiskInfo,
    EndpointMetricRead,
    ErrorMetricRead,
    ErrorsMetricsRead,
    HealthSummaryRead,
    MemoryInfo,
    ProcessInfo,
    RequestsMetricsRead,
    SessionListRead,
    SessionRead,
    SessionStatsRead,
    SuspiciousSessionRead,
    SystemHealthRead,
    TableMetricRead,
)


router = APIRouter(prefix="/superadmin", tags=["superadmin"])


# ============================================================================
# Helpers
# ============================================================================


def _now() -> datetime:
    return datetime.utcnow()


# ============================================================================
# 1. SYSTEM HEALTH
# ============================================================================


# Cache the process handle and start time once
_PROCESS = psutil.Process(os.getpid())
_PROCESS_STARTED_AT = datetime.fromtimestamp(_PROCESS.create_time())


def _build_system_health() -> SystemHealthRead:
    # CPU — call once with a small sample so it doesn't block long
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_logical = psutil.cpu_count(logical=True) or 1
    cpu_physical = psutil.cpu_count(logical=False)

    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    proc_mem_mb = _PROCESS.memory_info().rss / (1024 * 1024)
    proc_cpu = _PROCESS.cpu_percent(interval=0.0)
    proc_threads = _PROCESS.num_threads()
    uptime_seconds = int((datetime.utcnow() - _PROCESS_STARTED_AT).total_seconds())

    # Status thresholds
    status = "ok"
    if vm.percent > 90 or disk.percent > 90 or cpu_percent > 90:
        status = "degraded"

    return SystemHealthRead(
        status=status,
        timestamp=_now(),
        cpu=CPUInfo(
            percent=cpu_percent,
            count_logical=cpu_logical,
            count_physical=cpu_physical,
        ),
        memory=MemoryInfo(
            total_mb=vm.total // (1024 * 1024),
            available_mb=vm.available // (1024 * 1024),
            used_mb=vm.used // (1024 * 1024),
            percent=vm.percent,
        ),
        disk=DiskInfo(
            total_gb=round(disk.total / (1024**3), 2),
            used_gb=round(disk.used / (1024**3), 2),
            free_gb=round(disk.free / (1024**3), 2),
            percent=disk.percent,
        ),
        process=ProcessInfo(
            pid=_PROCESS.pid,
            memory_mb=round(proc_mem_mb, 2),
            cpu_percent=proc_cpu,
            threads=proc_threads,
            started_at=_PROCESS_STARTED_AT,
            uptime_seconds=uptime_seconds,
        ),
        platform={
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": sys.version.split()[0],
        },
    )


def _build_database_health(db: Session) -> DatabaseHealthRead:
    dialect = db.bind.dialect.name if db.bind else "unknown"
    timestamp = _now()
    try:
        start = time.perf_counter()
        db.execute(text("SELECT 1"))
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Try to get table sizes — only works on MySQL
        total_size_mb: float | None = None
        table_count: int | None = None
        largest_tables: list[dict[str, Any]] = []

        if dialect == "mysql":
            try:
                row = db.execute(text(
                    "SELECT COUNT(*), "
                    "COALESCE(SUM(data_length + index_length) / 1024 / 1024, 0) "
                    "FROM information_schema.tables "
                    "WHERE table_schema = DATABASE()"
                )).first()
                if row:
                    table_count = int(row[0])
                    total_size_mb = round(float(row[1]), 2)

                rows = db.execute(text(
                    "SELECT table_name, "
                    "ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb, "
                    "table_rows "
                    "FROM information_schema.tables "
                    "WHERE table_schema = DATABASE() "
                    "ORDER BY (data_length + index_length) DESC "
                    "LIMIT 10"
                )).all()
                largest_tables = [
                    {
                        "table_name": r[0],
                        "size_mb": float(r[1]) if r[1] is not None else 0.0,
                        "row_count": int(r[2]) if r[2] is not None else 0,
                    }
                    for r in rows
                ]
            except SQLAlchemyError:
                pass
        else:
            # SQLite fallback — just count tables via inspector
            try:
                insp = inspect(db.bind)
                table_names = insp.get_table_names()
                table_count = len(table_names)
            except Exception:
                pass

        return DatabaseHealthRead(
            status="ok",
            timestamp=timestamp,
            connected=True,
            latency_ms=latency_ms,
            dialect=dialect,
            total_size_mb=total_size_mb,
            table_count=table_count,
            largest_tables=largest_tables,
        )
    except Exception as exc:
        return DatabaseHealthRead(
            status="error",
            timestamp=timestamp,
            connected=False,
            dialect=dialect,
            error=str(exc),
        )


@router.get("/health/system", response_model=SystemHealthRead)
def get_system_health(_: User = Depends(require_super_admin)):
    """CPU, memory, disk, and process metrics for the running backend."""
    return _build_system_health()


@router.get("/health/database", response_model=DatabaseHealthRead)
def get_database_health(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Database connection latency, dialect, total size, and largest tables."""
    return _build_database_health(db)


@router.get("/health/summary", response_model=HealthSummaryRead)
def get_health_summary(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Combined system + database snapshot. Convenient for the dashboard tile."""
    sys_h = _build_system_health()
    db_h = _build_database_health(db)
    overall = "ok"
    if sys_h.status != "ok" or db_h.status != "ok":
        overall = "degraded" if "ok" not in (sys_h.status, db_h.status) else "degraded"
    if db_h.status == "error":
        overall = "error"
    return HealthSummaryRead(
        status=overall,
        timestamp=_now(),
        system=sys_h,
        database=db_h,
    )


# ============================================================================
# 2. SESSIONS
# ============================================================================


def _session_to_read(s: UserSession, user: User | None = None) -> SessionRead:
    return SessionRead(
        id=s.id,
        user_id=s.user_id,
        user_email=user.email if user else None,
        user_full_name=f"{user.first_name} {user.last_name}" if user else None,
        created_at=s.created_at,
        expires_at=s.expires_at,
        last_activity_at=s.last_activity_at,
        user_agent=s.user_agent,
        ip_address=s.ip_address,
        is_expired=s.expires_at < _now(),
    )


@router.get("/sessions", response_model=SessionListRead)
def list_sessions(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str | None = Query(None),
    email: str | None = Query(None, description="Substring match on email"),
    only_active: bool = Query(False),
    only_expired: bool = Query(False),
):
    """Paginated list of all sessions with filters."""
    q = db.query(UserSession, User).join(User, User.id == UserSession.user_id)

    if user_id:
        q = q.filter(UserSession.user_id == user_id)
    if email:
        q = q.filter(User.email.ilike(f"%{email}%"))
    if only_active:
        q = q.filter(UserSession.expires_at >= _now())
    if only_expired:
        q = q.filter(UserSession.expires_at < _now())

    total = q.count()
    rows = (
        q.order_by(desc(UserSession.last_activity_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [_session_to_read(s, u) for s, u in rows]
    return SessionListRead(total=total, page=page, page_size=page_size, items=items)


@router.get("/sessions/stats", response_model=SessionStatsRead)
def session_stats(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Aggregated session statistics for the dashboard."""
    now = _now()
    total_active = (
        db.query(func.count(UserSession.id))
        .filter(UserSession.expires_at >= now)
        .scalar() or 0
    )
    total_expired = (
        db.query(func.count(UserSession.id))
        .filter(UserSession.expires_at < now)
        .scalar() or 0
    )
    unique_users = (
        db.query(func.count(func.distinct(UserSession.user_id)))
        .filter(UserSession.expires_at >= now)
        .scalar() or 0
    )
    sessions_last_24h = (
        db.query(func.count(UserSession.id))
        .filter(UserSession.created_at >= now - timedelta(hours=24))
        .scalar() or 0
    )
    sessions_last_7d = (
        db.query(func.count(UserSession.id))
        .filter(UserSession.created_at >= now - timedelta(days=7))
        .scalar() or 0
    )

    # Sessions per day for last 7 days
    rows = (
        db.query(
            func.date(UserSession.created_at).label("day"),
            func.count(UserSession.id).label("count"),
        )
        .filter(UserSession.created_at >= now - timedelta(days=7))
        .group_by(func.date(UserSession.created_at))
        .order_by(func.date(UserSession.created_at))
        .all()
    )
    sessions_by_day = [
        {"date": str(r.day), "count": int(r.count)} for r in rows
    ]

    return SessionStatsRead(
        total_active=total_active,
        total_expired=total_expired,
        unique_users=unique_users,
        sessions_last_24h=sessions_last_24h,
        sessions_last_7d=sessions_last_7d,
        sessions_by_day=sessions_by_day,
    )


@router.get("/sessions/suspicious", response_model=list[SuspiciousSessionRead])
def list_suspicious_sessions(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    min_unique_ips: int = Query(3, ge=2, description="Flag users with at least N unique IPs"),
):
    """Detect users with multiple concurrent sessions from many IPs."""
    now = _now()

    # Group active sessions by user, count distinct IPs
    rows = (
        db.query(
            UserSession.user_id,
            func.count(UserSession.id).label("session_count"),
            func.count(func.distinct(UserSession.ip_address)).label("unique_ips"),
        )
        .filter(UserSession.expires_at >= now)
        .filter(UserSession.ip_address.isnot(None))
        .group_by(UserSession.user_id)
        .having(func.count(func.distinct(UserSession.ip_address)) >= min_unique_ips)
        .all()
    )

    out: list[SuspiciousSessionRead] = []
    for row in rows:
        user = db.query(User).filter(User.id == row.user_id).first()
        sessions = (
            db.query(UserSession)
            .filter(UserSession.user_id == row.user_id, UserSession.expires_at >= now)
            .order_by(desc(UserSession.last_activity_at))
            .all()
        )
        out.append(SuspiciousSessionRead(
            user_id=row.user_id,
            user_email=user.email if user else None,
            user_full_name=f"{user.first_name} {user.last_name}" if user else None,
            reason=f"{row.unique_ips} IPs distintas en {row.session_count} sesiones activas",
            session_count=int(row.session_count),
            unique_ips=int(row.unique_ips),
            sessions=[_session_to_read(s, user) for s in sessions],
        ))
    return out


@router.delete("/sessions/{target_session_id}", status_code=204)
def revoke_session(
    target_session_id: str,
    request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Forcefully revoke (delete) a single session."""
    s = db.query(UserSession).filter(UserSession.id == target_session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    target_user_id = s.user_id
    db.delete(s)
    db.commit()

    log_action(
        db,
        AuditAction.SESSION_REVOKED,
        user_id=current_user.id,
        resource_type="session",
        resource_id=target_session_id,
        description=f"Sesión revocada del usuario {target_user_id}",
        extra_data={"target_user_id": target_user_id},
        request=request,
    )
    return None


@router.delete("/sessions/user/{user_id}", status_code=200)
def revoke_user_sessions(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Revoke all sessions of a specific user."""
    sessions = db.query(UserSession).filter(UserSession.user_id == user_id).all()
    count = len(sessions)
    for s in sessions:
        db.delete(s)
    db.commit()

    log_action(
        db,
        AuditAction.SESSION_REVOKED_ALL,
        user_id=current_user.id,
        resource_type="user",
        resource_id=user_id,
        description=f"{count} sesiones revocadas para el usuario {user_id}",
        extra_data={"target_user_id": user_id, "count": count},
        request=request,
    )
    return {"deleted": count, "user_id": user_id}


@router.post("/sessions/cleanup", response_model=CleanupResponse)
def cleanup_sessions_endpoint(
    request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Delete all expired sessions from the database."""
    now = _now()
    expired = db.query(UserSession).filter(UserSession.expires_at < now).all()
    count = len(expired)
    for s in expired:
        db.delete(s)
    db.commit()

    log_action(
        db,
        AuditAction.SESSION_CLEANUP,
        user_id=current_user.id,
        resource_type="session",
        description=f"Limpieza de sesiones expiradas: {count} eliminadas",
        extra_data={"count": count},
        request=request,
    )
    return CleanupResponse(deleted=count, message=f"{count} sesiones expiradas eliminadas")


# ============================================================================
# 3. METRICS
# ============================================================================


@router.get("/metrics/requests", response_model=RequestsMetricsRead)
def metrics_requests(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=720),
    top_n: int = Query(10, ge=1, le=50),
):
    """Top endpoints by request count and slowest endpoints by avg duration."""
    cutoff = _now() - timedelta(hours=hours)

    base_q = db.query(RequestMetric).filter(RequestMetric.created_at >= cutoff)

    total_requests = base_q.count()
    avg_duration = (
        base_q.with_entities(func.avg(RequestMetric.duration_ms)).scalar() or 0
    )
    error_count = (
        base_q.filter(RequestMetric.status_code >= 400).count()
    )
    error_rate = (error_count / total_requests) if total_requests > 0 else 0.0

    # Group by (method, path)
    error_case = case((RequestMetric.status_code >= 400, 1), else_=0)
    grouped = (
        db.query(
            RequestMetric.method,
            RequestMetric.path,
            func.count(RequestMetric.id).label("cnt"),
            func.avg(RequestMetric.duration_ms).label("avg_dur"),
            func.sum(error_case).label("err_cnt"),
            func.max(RequestMetric.created_at).label("last_at"),
        )
        .filter(RequestMetric.created_at >= cutoff)
        .group_by(RequestMetric.method, RequestMetric.path)
    )

    rows = grouped.order_by(desc("cnt")).limit(top_n).all()
    top_endpoints = [
        EndpointMetricRead(
            method=r.method,
            path=r.path,
            request_count=int(r.cnt),
            avg_duration_ms=round(float(r.avg_dur or 0), 2),
            error_rate=round((float(r.err_cnt or 0) / r.cnt) if r.cnt else 0.0, 4),
            last_called_at=r.last_at,
        )
        for r in rows
    ]

    slow_rows = grouped.order_by(desc("avg_dur")).limit(top_n).all()
    slowest_endpoints = [
        EndpointMetricRead(
            method=r.method,
            path=r.path,
            request_count=int(r.cnt),
            avg_duration_ms=round(float(r.avg_dur or 0), 2),
            error_rate=round((float(r.err_cnt or 0) / r.cnt) if r.cnt else 0.0, 4),
            last_called_at=r.last_at,
        )
        for r in slow_rows
    ]

    return RequestsMetricsRead(
        period_hours=hours,
        total_requests=total_requests,
        avg_duration_ms=round(float(avg_duration), 2),
        error_rate=round(error_rate, 4),
        top_endpoints=top_endpoints,
        slowest_endpoints=slowest_endpoints,
    )


@router.get("/metrics/errors", response_model=ErrorsMetricsRead)
def metrics_errors(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=720),
    top_n: int = Query(20, ge=1, le=100),
):
    """Recent 4xx and 5xx errors grouped by endpoint."""
    cutoff = _now() - timedelta(hours=hours)
    base = db.query(RequestMetric).filter(
        RequestMetric.created_at >= cutoff,
        RequestMetric.status_code >= 400,
    )
    total_errors = base.count()
    errors_4xx = base.filter(
        RequestMetric.status_code.between(400, 499)
    ).count()
    errors_5xx = base.filter(RequestMetric.status_code >= 500).count()

    rows = (
        db.query(
            RequestMetric.method,
            RequestMetric.path,
            RequestMetric.status_code,
            func.count(RequestMetric.id).label("cnt"),
            func.max(RequestMetric.created_at).label("last_at"),
        )
        .filter(RequestMetric.created_at >= cutoff, RequestMetric.status_code >= 400)
        .group_by(RequestMetric.method, RequestMetric.path, RequestMetric.status_code)
        .order_by(desc("cnt"))
        .limit(top_n)
        .all()
    )
    by_endpoint = [
        ErrorMetricRead(
            method=r.method,
            path=r.path,
            status_code=int(r.status_code),
            count=int(r.cnt),
            last_seen_at=r.last_at,
        )
        for r in rows
    ]
    return ErrorsMetricsRead(
        period_hours=hours,
        total_errors=total_errors,
        errors_4xx=errors_4xx,
        errors_5xx=errors_5xx,
        by_endpoint=by_endpoint,
    )


@router.get("/metrics/active-users", response_model=ActiveUsersRead)
def metrics_active_users(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=720),
    granularity: str = Query("hour", pattern="^(hour|day)$"),
):
    """Active users bucketed by hour or day, based on request_metrics."""
    cutoff = _now() - timedelta(hours=hours)

    if granularity == "hour":
        # Truncate created_at to the hour
        if db.bind.dialect.name == "mysql":
            bucket_expr = func.date_format(RequestMetric.created_at, "%Y-%m-%d %H:00:00")
        else:
            bucket_expr = func.strftime("%Y-%m-%d %H:00:00", RequestMetric.created_at)
    else:
        if db.bind.dialect.name == "mysql":
            bucket_expr = func.date_format(RequestMetric.created_at, "%Y-%m-%d")
        else:
            bucket_expr = func.strftime("%Y-%m-%d", RequestMetric.created_at)

    rows = (
        db.query(
            bucket_expr.label("bucket"),
            func.count(func.distinct(RequestMetric.user_id)).label("uniq"),
            func.count(RequestMetric.id).label("cnt"),
        )
        .filter(RequestMetric.created_at >= cutoff)
        .group_by("bucket")
        .order_by("bucket")
        .all()
    )

    buckets = [
        ActiveUsersBucketRead(
            bucket=str(r.bucket),
            unique_users=int(r.uniq or 0),
            request_count=int(r.cnt or 0),
        )
        for r in rows
    ]
    return ActiveUsersRead(
        granularity=granularity,
        period_hours=hours,
        buckets=buckets,
    )


@router.get("/metrics/database", response_model=DatabaseMetricsRead)
def metrics_database(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Per-table row counts. Best-effort and dialect-aware."""
    timestamp = _now()
    tables: list[TableMetricRead] = []

    try:
        insp = inspect(db.bind)
        for name in insp.get_table_names():
            try:
                row = db.execute(text(f"SELECT COUNT(*) FROM {name}")).first()
                count = int(row[0]) if row else 0
            except SQLAlchemyError:
                count = 0
            tables.append(TableMetricRead(table_name=name, row_count=count))
    except Exception:
        pass

    tables.sort(key=lambda t: t.row_count, reverse=True)
    return DatabaseMetricsRead(timestamp=timestamp, tables=tables)


# ============================================================================
# 4. AUDIT LOGS
# ============================================================================


def _audit_to_read(log: AuditLog, user: User | None) -> AuditLogRead:
    return AuditLogRead(
        id=log.id,
        created_at=log.created_at,
        user_id=log.user_id,
        user_email=user.email if user else None,
        user_full_name=f"{user.first_name} {user.last_name}" if user else None,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        description=log.description,
        extra_data=log.extra_data,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
    )


@router.get("/audit-logs/actions", response_model=list[AuditActionRead])
def audit_log_actions(_: User = Depends(require_super_admin)):
    """Catalog of canonical audit actions, grouped by category for the UI."""
    out: list[AuditActionRead] = []
    for action in ALL_ACTIONS:
        category, _, leaf = action.partition(".")
        out.append(AuditActionRead(
            value=action,
            label=leaf.replace("_", " ").title() if leaf else action,
            category=category,
        ))
    return out


@router.get("/audit-logs/export")
def audit_logs_export(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    user_id: str | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
):
    """Export filtered audit logs as CSV. (Defined before /{log_id} on purpose.)"""
    q = db.query(AuditLog)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if date_from:
        q = q.filter(AuditLog.created_at >= date_from)
    if date_to:
        q = q.filter(AuditLog.created_at <= date_to)
    q = q.order_by(desc(AuditLog.created_at))

    rows = q.all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "created_at", "user_id", "action", "resource_type",
        "resource_id", "description", "ip_address", "user_agent",
    ])
    for r in rows:
        writer.writerow([
            r.id,
            r.created_at.isoformat() if r.created_at else "",
            r.user_id or "",
            r.action,
            r.resource_type or "",
            r.resource_id or "",
            (r.description or "").replace("\n", " "),
            r.ip_address or "",
            (r.user_agent or "").replace("\n", " "),
        ])

    buf.seek(0)
    filename = f"audit_logs_{_now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/audit-logs", response_model=AuditLogListRead)
def list_audit_logs(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    user_id: str | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    search: str | None = Query(None, description="Substring match on description"),
):
    """Paginated, filterable list of audit logs."""
    q = db.query(AuditLog)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        q = q.filter(AuditLog.resource_id == resource_id)
    if date_from:
        q = q.filter(AuditLog.created_at >= date_from)
    if date_to:
        q = q.filter(AuditLog.created_at <= date_to)
    if search:
        q = q.filter(AuditLog.description.ilike(f"%{search}%"))

    total = q.count()
    rows = (
        q.order_by(desc(AuditLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Resolve users in one query
    user_ids = {r.user_id for r in rows if r.user_id}
    users_by_id: dict[str, User] = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(list(user_ids))).all()
        users_by_id = {u.id: u for u in users}

    items = [_audit_to_read(r, users_by_id.get(r.user_id) if r.user_id else None) for r in rows]
    return AuditLogListRead(total=total, page=page, page_size=page_size, items=items)


@router.get("/audit-logs/{log_id}", response_model=AuditLogRead)
def get_audit_log(
    log_id: str,
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Detail of a single audit log entry."""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log no encontrado")
    user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
    return _audit_to_read(log, user)


# ============================================================================
# 5. ADMIN ACTIVITY
# ============================================================================


_ADMIN_ROLE_NAMES = {"super_admin", "content_admin", "content_editor", "content_viewer"}


@router.get("/admins/activity", response_model=list[AdminActivityRead])
def admins_activity(
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=90),
):
    """Recent activity overview of all users with admin roles."""
    cutoff = _now() - timedelta(days=days)

    # All users with at least one admin-tier role
    admin_users = (
        db.query(User, Role)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .filter(Role.name.in_(list(_ADMIN_ROLE_NAMES)))
        .all()
    )

    # Group roles by user
    roles_by_user: dict[str, list[str]] = {}
    user_objs: dict[str, User] = {}
    for u, r in admin_users:
        roles_by_user.setdefault(u.id, []).append(r.name.value)
        user_objs[u.id] = u

    # Action counts for the period
    if user_objs:
        action_rows = (
            db.query(
                AuditLog.user_id,
                func.count(AuditLog.id).label("cnt"),
                func.max(AuditLog.created_at).label("last_at"),
            )
            .filter(
                AuditLog.user_id.in_(list(user_objs.keys())),
                AuditLog.created_at >= cutoff,
            )
            .group_by(AuditLog.user_id)
            .all()
        )
    else:
        action_rows = []
    actions_by_user = {r.user_id: (int(r.cnt), r.last_at) for r in action_rows}

    out: list[AdminActivityRead] = []
    for uid, u in user_objs.items():
        cnt, last_at = actions_by_user.get(uid, (0, None))
        out.append(AdminActivityRead(
            user_id=uid,
            email=u.email,
            full_name=f"{u.first_name} {u.last_name}",
            role_names=sorted(set(roles_by_user.get(uid, []))),
            last_login_at=u.last_login_at,
            actions_last_7d=cnt,
            last_action_at=last_at,
        ))
    out.sort(key=lambda x: (x.last_action_at or datetime.min), reverse=True)
    return out


@router.get("/admins/{user_id}/history", response_model=list[AdminRoleHistoryRead])
def admin_role_history(
    user_id: str,
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Role change history for a specific admin user, sourced from audit logs."""
    rows = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == AuditAction.USER_ROLE_CHANGED,
            AuditLog.resource_type == "user",
            AuditLog.resource_id == user_id,
        )
        .order_by(desc(AuditLog.created_at))
        .all()
    )

    actor_ids = {r.user_id for r in rows if r.user_id}
    actors = (
        {a.id: a for a in db.query(User).filter(User.id.in_(list(actor_ids))).all()}
        if actor_ids else {}
    )

    return [
        AdminRoleHistoryRead(
            timestamp=r.created_at,
            actor_id=r.user_id,
            actor_email=actors[r.user_id].email if r.user_id in actors else None,
            action=r.action,
            description=r.description,
            extra_data=r.extra_data,
        )
        for r in rows
    ]


@router.get("/admins/{user_id}/actions", response_model=list[AuditLogRead])
def admin_actions(
    user_id: str,
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=500),
):
    """Most recent audit log entries authored by a specific admin user."""
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
        .all()
    )
    user = db.query(User).filter(User.id == user_id).first()
    return [_audit_to_read(r, user) for r in rows]
