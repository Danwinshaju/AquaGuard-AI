"""Top-level API router.

Feature routers are registered here so ``main.py`` stays small.
"""

from fastapi import APIRouter, Depends

from app.api.auth import router as auth_router
from app.api.cameras import router as cameras_router
from app.api.dashboard import router as dashboard_router
from app.api.documentation import router as documentation_router
from app.api.health import router as health_router
from app.api.incidents import router as incidents_router
from app.api.live import router as live_router
from app.api.model import router as model_router
from app.api.videos import router as videos_router
from app.core.auth import get_current_user

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Accounts"])
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(videos_router, prefix="/videos", tags=["Videos"])
api_router.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(cameras_router, prefix="/cameras", tags=["Cameras"])
api_router.include_router(live_router, prefix="/live", tags=["Live Monitoring"])
api_router.include_router(
    model_router,
    prefix="/model",
    tags=["AI Model"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    documentation_router,
    prefix="/documentation",
    tags=["Documentation"],
)
