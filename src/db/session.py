from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings


def _engine_options() -> dict:
    if settings.database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    # Cloud SQL via Unix socket: TLS is handled by the Cloud SQL proxy/socket,
    # so we must NOT pass ssl args to PyMySQL or it will reject the connection.
    if settings.is_cloud_sql_socket:
        return {"pool_pre_ping": True, "pool_recycle": 1800}
    if settings.db_ssl_ca:
        return {
            "connect_args": {"ssl": {"ca": settings.db_ssl_ca}},
            "pool_pre_ping": True,
            "pool_recycle": 1800,
        }
    return {"pool_pre_ping": True, "pool_recycle": 1800}


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