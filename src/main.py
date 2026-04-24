from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from src.api.router import api_router
from src.core.config import settings
from seed_data import seed_database


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)

# Seed database on startup
seed_database()

# Add CORS middleware to allow frontend requests (localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)

# Add Scalar API documentation
app.get("/scalar", include_in_schema=False)(
    lambda: get_scalar_api_reference(
        openapi_url="/openapi.json",
        title=f"{settings.app_name} - Scalar"
    )
)

@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {"message": f"{settings.app_name} is running"}