"""Health endpoints used by developers and deployment systems."""

import shutil

from fastapi import APIRouter

from app.core.config import get_settings
from app.db.mongodb import mongo_database
from app.schemas.health import DatabaseHealthResponse, HealthResponse
from app.services.camera_manager import camera_manager

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def application_health() -> HealthResponse:
    """Confirm that the web application process is responding."""

    settings = get_settings()
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        environment=settings.app_env,
    )


@router.get("/health/database", response_model=DatabaseHealthResponse)
async def database_health() -> DatabaseHealthResponse:
    """Check whether MongoDB accepts a ping command."""

    connected, detail = await mongo_database.ping()
    return DatabaseHealthResponse(
        status="connected" if connected else "disconnected",
        database=get_settings().mongodb_database,
        detail=detail,
    )


@router.get("/health/system")
async def system_health() -> dict[str, object]:
    """Report AI acceleration, models, storage, cameras, and database readiness."""

    import torch

    settings = get_settings()
    database_connected, _ = await mongo_database.ping()
    storage = shutil.disk_usage(settings.storage_root)
    online_cameras = sum(camera.status == "online" for camera in camera_manager.cameras.values())
    return {
        "status": "ok" if database_connected else "degraded",
        "mongodb": database_connected,
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "configured_device": settings.yolo_device or "automatic",
        "temporal_model_ready": settings.temporal_model_path.is_file(),
        "online_cameras": online_cameras,
        "total_cameras": len(camera_manager.cameras),
        "storage_free_gb": round(storage.free / (1024**3), 1),
    }
