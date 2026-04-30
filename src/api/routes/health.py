import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import settings
from src.db.session import get_db


router = APIRouter()


@router.get("", summary="Health check")
def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
    }


@router.get("/db", summary="Database connectivity check")
def db_healthcheck(db: Session = Depends(get_db)) -> dict[str, object]:
    """Confirms the app can reach its DB. Useful right after deploy to verify
    that Cloud SQL via Unix socket is wired correctly without needing auth."""
    started = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — surface root cause
        raise HTTPException(status_code=503, detail=f"db_unreachable: {exc!s}") from exc

    latency_ms = int((time.perf_counter() - started) * 1000)
    return {
        "status": "ok",
        "mode": "cloud_sql_socket" if settings.is_cloud_sql_socket else "tcp",
        "socket_path": settings.cloud_sql_socket_path,
        "database": settings.mysql_database,
        "latency_ms": latency_ms,
    }