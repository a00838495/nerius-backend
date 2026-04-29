"""Admin panel routes — split by feature for readability.

Each module exposes a `router` that gets included in the parent admin_panel router
exported from this package.
"""

from fastapi import APIRouter

from src.api.routes.admin_panel.dashboard import router as dashboard_router
from src.api.routes.admin_panel.users import router as users_router
from src.api.routes.admin_panel.areas import router as areas_router
from src.api.routes.admin_panel.assignments import router as assignments_router
from src.api.routes.admin_panel.forum_moderation import router as forum_moderation_router
from src.api.routes.admin_panel.gems_global import router as gems_global_router
from src.api.routes.admin_panel.badges_global import router as badges_global_router
from src.api.routes.admin_panel.certifications_admin import router as certifications_admin_router
from src.api.routes.admin_panel.reports import router as reports_router
from src.api.routes.admin_panel.enrollments import router as enrollments_router


# Master router for the admin panel — mounted under /admin in the main API router.
# All sub-routers already declare their own sub-prefixes (e.g. "/users", "/areas").
admin_panel_router = APIRouter(prefix="/admin", tags=["admin-panel"])

admin_panel_router.include_router(dashboard_router)
admin_panel_router.include_router(users_router)
admin_panel_router.include_router(areas_router)
admin_panel_router.include_router(assignments_router)
admin_panel_router.include_router(forum_moderation_router)
admin_panel_router.include_router(gems_global_router)
admin_panel_router.include_router(badges_global_router)
admin_panel_router.include_router(certifications_admin_router)
admin_panel_router.include_router(reports_router)
admin_panel_router.include_router(enrollments_router)


__all__ = ["admin_panel_router"]
