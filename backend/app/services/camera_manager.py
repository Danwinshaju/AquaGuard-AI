"""Concurrent RTSP/HTTP camera ingestion with reconnection and AI processing."""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

import cv2

from app.db.repositories import camera_repository, incident_repository
from app.models import CameraDocument
from app.services.alert_delivery import alert_delivery_service
from app.services.live_monitoring import LiveMonitoringSession

CameraState = Literal["starting", "online", "reconnecting", "stopped", "error"]


@dataclass
class ManagedCamera:
    id: str
    owner_id: str | None
    name: str
    source_url: str
    status: CameraState = "starting"
    people: int = 0
    highest_risk: float = 0.0
    last_frame_at: datetime | None = None
    reconnect_count: int = 0
    error: str | None = None
    latest_jpeg: bytes | None = None
    task: asyncio.Task[None] | None = field(default=None, repr=False)


class CameraManager:
    def __init__(self) -> None:
        self.cameras: dict[str, ManagedCamera] = {}

    def _start(
        self,
        name: str,
        source_url: str,
        owner_id: str | None,
        camera_id: str | None = None,
    ) -> ManagedCamera:
        if not source_url.lower().startswith(("rtsp://", "http://", "https://")):
            raise ValueError("Camera URL must start with rtsp://, http://, or https://.")
        camera = ManagedCamera(
            id=camera_id or str(uuid4()),
            owner_id=owner_id,
            name=name.strip(),
            source_url=source_url.strip(),
        )
        self.cameras[camera.id] = camera
        camera.task = asyncio.create_task(self._run(camera))
        return camera

    async def create(self, name: str, source_url: str, owner_id: str) -> ManagedCamera:
        camera = self._start(name, source_url, owner_id)
        try:
            await camera_repository.save(
                CameraDocument(
                    id=camera.id,
                    owner_id=owner_id,
                    name=camera.name,
                    source_url=camera.source_url,
                )
            )
        except Exception:
            await self._stop(camera)
            self.cameras.pop(camera.id, None)
            raise
        return camera

    async def restore(self) -> int:
        restored = 0
        for document in await camera_repository.list_all():
            if document.id not in self.cameras:
                self._start(
                    document.name,
                    document.source_url,
                    document.owner_id,
                    document.id,
                )
                restored += 1
        return restored

    async def delete(self, camera_id: str, owner_id: str) -> bool:
        camera = self.cameras.get(camera_id)
        if camera is None or camera.owner_id != owner_id:
            return False
        self.cameras.pop(camera_id)
        await self._stop(camera)
        await camera_repository.delete(camera_id, owner_id)
        return True

    @staticmethod
    async def _stop(camera: ManagedCamera) -> None:
        if camera.task is not None:
            camera.task.cancel()
            try:
                await camera.task
            except asyncio.CancelledError:
                pass

    async def stop_all(self) -> None:
        for camera in list(self.cameras.values()):
            await self._stop(camera)
        self.cameras.clear()

    async def _run(self, camera: ManagedCamera) -> None:
        try:
            session = await asyncio.to_thread(LiveMonitoringSession)
            session.session_id = f"camera-{camera.id}"
            session.source_name = camera.name
        except Exception as error:
            camera.status = "error"
            camera.error = f"AI initialization failed: {error}"
            return
        while True:
            capture = await asyncio.to_thread(cv2.VideoCapture, camera.source_url)
            if not capture.isOpened():
                camera.status = "reconnecting"
                camera.error = "Camera connection failed. Retrying automatically."
                camera.reconnect_count += 1
                await asyncio.to_thread(capture.release)
                await asyncio.sleep(3)
                continue
            camera.status = "online"
            camera.error = None
            try:
                while True:
                    success, frame = await asyncio.to_thread(capture.read)
                    if not success:
                        camera.status = "reconnecting"
                        camera.error = "Camera stream was interrupted."
                        camera.reconnect_count += 1
                        break
                    encoded, jpeg = cv2.imencode(".jpg", frame)
                    if not encoded:
                        continue
                    metadata, annotated = await asyncio.to_thread(
                        session.process_jpeg,
                        jpeg.tobytes(),
                    )
                    incidents = session.drain_pending_incidents()
                    if camera.owner_id is not None:
                        await incident_repository.save_many(incidents, camera.owner_id)
                    await alert_delivery_service.dispatch_many(incidents)
                    camera.latest_jpeg = annotated
                    camera.people = int(metadata["people"])
                    camera.highest_risk = float(metadata["highest_risk"])
                    camera.last_frame_at = datetime.now(UTC)
                    camera.status = "online"
                    await asyncio.sleep(0)
            finally:
                await asyncio.to_thread(capture.release)
            await asyncio.sleep(2)


camera_manager = CameraManager()
