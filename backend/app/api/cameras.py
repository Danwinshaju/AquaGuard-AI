"""RTSP/HTTP multi-camera management and annotated previews."""

import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from app.core.auth import CurrentUser
from app.schemas.camera import CameraCreate, CameraStatus
from app.services.camera_manager import ManagedCamera, camera_manager

router = APIRouter()


def _camera_response(camera: ManagedCamera) -> CameraStatus:
    return CameraStatus(
        id=camera.id,
        name=camera.name,
        status=camera.status,
        people=camera.people,
        highest_risk=camera.highest_risk,
        last_frame_at=camera.last_frame_at,
        reconnect_count=camera.reconnect_count,
        error=camera.error,
        stream_url=f"/api/v1/cameras/{camera.id}/stream",
    )


@router.get("", response_model=list[CameraStatus])
async def list_cameras(user: CurrentUser) -> list[CameraStatus]:
    return [
        _camera_response(camera)
        for camera in camera_manager.cameras.values()
        if camera.owner_id == user.id
    ]


@router.post("", response_model=CameraStatus, status_code=status.HTTP_201_CREATED)
async def add_camera(payload: CameraCreate, user: CurrentUser) -> CameraStatus:
    try:
        camera = await camera_manager.create(payload.name, payload.source_url, user.id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _camera_response(camera)


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: str, user: CurrentUser) -> Response:
    if not await camera_manager.delete(camera_id, user.id):
        raise HTTPException(status_code=404, detail="Camera not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{camera_id}/stream", response_class=StreamingResponse)
async def camera_stream(camera_id: str, user: CurrentUser) -> StreamingResponse:
    camera = camera_manager.cameras.get(camera_id)
    if camera is None or camera.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Camera not found.")

    async def frames() -> AsyncIterator[bytes]:
        while camera_id in camera_manager.cameras:
            if camera.latest_jpeg is not None:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + camera.latest_jpeg + b"\r\n"
            await asyncio.sleep(0.2)

    return StreamingResponse(
        frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
