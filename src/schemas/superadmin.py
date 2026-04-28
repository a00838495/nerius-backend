"""Pydantic schemas for super-admin endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# 1. SYSTEM HEALTH
# =============================================================================


class CPUInfo(BaseModel):
    percent: float = Field(..., description="Current CPU usage percentage")
    count_logical: int
    count_physical: int | None = None


class MemoryInfo(BaseModel):
    total_mb: int
    available_mb: int
    used_mb: int
    percent: float


class DiskInfo(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float


class ProcessInfo(BaseModel):
    pid: int
    memory_mb: float
    cpu_percent: float
    threads: int
    started_at: datetime
    uptime_seconds: int


class SystemHealthRead(BaseModel):
    status: str = Field(..., description="ok | degraded | error")
    timestamp: datetime
    cpu: CPUInfo
    memory: MemoryInfo
    disk: DiskInfo
    process: ProcessInfo
    platform: dict[str, Any]


class DatabaseHealthRead(BaseModel):
    status: str
    timestamp: datetime
    connected: bool
    latency_ms: int | None = None
    dialect: str
    total_size_mb: float | None = None
    table_count: int | None = None
    largest_tables: list[dict[str, Any]] = []
    error: str | None = None


class HealthSummaryRead(BaseModel):
    status: str
    timestamp: datetime
    system: SystemHealthRead
    database: DatabaseHealthRead


# =============================================================================
# 2. SESSIONS
# =============================================================================


class SessionRead(BaseModel):
    id: str
    user_id: str
    user_email: str | None = None
    user_full_name: str | None = None
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    user_agent: str | None = None
    ip_address: str | None = None
    is_expired: bool


class SessionListRead(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SessionRead]


class SessionStatsRead(BaseModel):
    total_active: int
    total_expired: int
    unique_users: int
    sessions_last_24h: int
    sessions_last_7d: int
    sessions_by_day: list[dict[str, Any]]


class SuspiciousSessionRead(BaseModel):
    user_id: str
    user_email: str | None = None
    user_full_name: str | None = None
    reason: str
    session_count: int
    unique_ips: int
    sessions: list[SessionRead]


class CleanupResponse(BaseModel):
    deleted: int
    message: str


# =============================================================================
# 3. METRICS
# =============================================================================


class EndpointMetricRead(BaseModel):
    method: str
    path: str
    request_count: int
    avg_duration_ms: float
    p95_duration_ms: float | None = None
    error_rate: float
    last_called_at: datetime | None = None


class RequestsMetricsRead(BaseModel):
    period_hours: int
    total_requests: int
    avg_duration_ms: float
    error_rate: float
    top_endpoints: list[EndpointMetricRead]
    slowest_endpoints: list[EndpointMetricRead]


class ErrorMetricRead(BaseModel):
    method: str
    path: str
    status_code: int
    count: int
    last_seen_at: datetime


class ErrorsMetricsRead(BaseModel):
    period_hours: int
    total_errors: int
    errors_4xx: int
    errors_5xx: int
    by_endpoint: list[ErrorMetricRead]


class ActiveUsersBucketRead(BaseModel):
    bucket: str  # ISO datetime or label
    unique_users: int
    request_count: int


class ActiveUsersRead(BaseModel):
    granularity: str  # "hour" | "day"
    period_hours: int
    buckets: list[ActiveUsersBucketRead]


class TableMetricRead(BaseModel):
    table_name: str
    row_count: int
    growth_24h: int | None = None


class DatabaseMetricsRead(BaseModel):
    timestamp: datetime
    tables: list[TableMetricRead]


# =============================================================================
# 4. AUDIT LOGS
# =============================================================================


class AuditLogRead(BaseModel):
    id: str
    created_at: datetime
    user_id: str | None
    user_email: str | None = None
    user_full_name: str | None = None
    action: str
    resource_type: str | None
    resource_id: str | None
    description: str | None
    extra_data: dict[str, Any] | None = None
    ip_address: str | None
    user_agent: str | None


class AuditLogListRead(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AuditLogRead]


class AuditActionRead(BaseModel):
    value: str
    label: str
    category: str


# =============================================================================
# 5. ADMIN ACTIVITY
# =============================================================================


class AdminActivityRead(BaseModel):
    user_id: str
    email: str
    full_name: str
    role_names: list[str]
    last_login_at: datetime | None
    actions_last_7d: int
    last_action_at: datetime | None


class AdminRoleHistoryRead(BaseModel):
    timestamp: datetime
    actor_id: str | None
    actor_email: str | None
    action: str
    description: str | None
    extra_data: dict[str, Any] | None = None
