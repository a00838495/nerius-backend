from fastapi import APIRouter

from src.api.routes.health import router as health_router
from src.api.routes.auth import router as auth_router
from src.api.routes.courses import router as courses_router
from src.api.routes.forum import router as forum_router
from src.api.routes.gems import router as gems_router
from src.api.routes.quizzes import router as quizzes_router
from src.api.routes.certifications import router as certifications_router
from src.api.routes.admin import router as admin_router
from src.api.routes.chat import router as chat_router


api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(courses_router)
api_router.include_router(forum_router)
api_router.include_router(gems_router)
api_router.include_router(quizzes_router)
api_router.include_router(certifications_router)
api_router.include_router(admin_router)
api_router.include_router(chat_router)