import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings

logger = logging.getLogger(__name__)


def _engine_options() -> dict:
    if settings.database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    # Cloud SQL via Unix socket: TLS is handled by the Cloud SQL proxy/socket,
    # so we must NOT pass ssl args to PyMySQL or it will reject the connection.
    if settings.is_cloud_sql_socket:
        return {"pool_pre_ping": True, "pool_recycle": 1800, "pool_size": 5, "max_overflow": 2}
    if settings.db_ssl_ca:
        return {
            "connect_args": {"ssl": {"ca": settings.db_ssl_ca}},
            "pool_pre_ping": True,
            "pool_recycle": 1800,
        }
    return {"pool_pre_ping": True, "pool_recycle": 1800}


def _log_db_target() -> None:
    """Log the active DB target on startup so Cloud Run logs show what we hit."""
    if settings.is_cloud_sql_socket:
        logger.info(
            "DB connection: Cloud SQL via Unix socket at %s (db=%s, user=%s)",
            settings.cloud_sql_socket_path,
            settings.mysql_database,
            settings.mysql_user,
        )
    elif settings.database_url.startswith("sqlite"):
        logger.warning("DB connection: SQLite fallback (%s) — set MYSQL_* envs for prod.", settings.database_url)
    else:
        # Strip credentials before logging.
        safe = settings.database_url
        if "@" in safe:
            scheme, _, rest = safe.partition("://")
            _, _, host_part = rest.partition("@")
            safe = f"{scheme}://***:***@{host_part}"
        logger.info("DB connection: TCP MySQL at %s", safe)


_log_db_target()

engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    future=True,
    **_engine_options(),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()