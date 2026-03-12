from fastapi import APIRouter

from src.core.config import settings


router = APIRouter()


@router.get("", summary="Health check")
def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
    }