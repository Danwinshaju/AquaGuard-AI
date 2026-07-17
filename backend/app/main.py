"""FastAPI application entry point."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import PROJECT_DIRECTORY, get_settings
from app.db.mongodb import mongo_database
from app.services.alert_delivery import alert_delivery_service
from app.services.camera_manager import camera_manager
from app.services.incident_retention import incident_retention_service

logger = logging.getLogger(__name__)


async def _incident_cleanup_loop() -> None:
    """Remove expired incident records and evidence for the application's lifetime."""

    settings = get_settings()
    await asyncio.sleep(5)
    while True:
        try:
            deleted_count = await incident_retention_service.cleanup_expired()
            if deleted_count:
                logger.info("Deleted %s expired incident(s).", deleted_count)
        except Exception:
            logger.exception("Automatic incident evidence cleanup failed.")
        await asyncio.sleep(settings.incident_cleanup_interval_seconds)


async def _alert_escalation_loop() -> None:
    """Escalate danger reports that remain unseen by an operator."""

    await asyncio.sleep(10)
    while True:
        try:
            await alert_delivery_service.escalate_due_incidents()
        except Exception:
            logger.exception("Incident alert escalation failed.")
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Open shared resources on startup and close them on shutdown."""

    mongo_database.connect()
    try:
        await camera_manager.restore()
    except Exception:
        logger.exception("Persistent network cameras could not be restored.")
    cleanup_task = asyncio.create_task(_incident_cleanup_loop())
    escalation_task = asyncio.create_task(_alert_escalation_loop())
    try:
        yield
    finally:
        cleanup_task.cancel()
        escalation_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task
        with suppress(asyncio.CancelledError):
            await escalation_task
        await camera_manager.stop_all()
        await mongo_database.close()


def create_application() -> FastAPI:
    """Build and configure the FastAPI application."""

    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Educational pool-safety early-warning API. "
            "Not a certified safety device and not a replacement for trained lifeguards."
        ),
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix="/api/v1")

    # Serve the built beginner interface from the same address as the API.
    # API routes are registered first so the frontend cannot hide them.
    frontend_directory = PROJECT_DIRECTORY / "frontend" / "dist"
    if frontend_directory.is_dir():

        async def frontend_page() -> FileResponse:
            """Return the React app for every user-facing browser page."""

            return FileResponse(frontend_directory / "index.html")

        frontend_routes = (
            "/",
            "/analyze",
            "/live",
            "/cameras",
            "/dashboard",
            "/incidents",
            "/model",
            "/documentation",
            "/login",
            "/signup",
        )
        for frontend_route in frontend_routes:
            application.add_api_route(
                frontend_route,
                frontend_page,
                methods=["GET"],
                include_in_schema=False,
            )
        application.mount(
            "/",
            StaticFiles(directory=frontend_directory, html=True),
            name="frontend",
        )
    return application


app = create_application()
