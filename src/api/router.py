from fastapi import APIRouter

from src.api.routes.health import router as health_router
from src.api.routes.auth import router as auth_router
from src.api.routes.courses import router as courses_router


api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(courses_router)