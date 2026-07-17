"""Video upload, background processing, and progress routes."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, File, Response, UploadFile, WebSocket, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from app.core.auth import CurrentUser
from app.db.repositories import incident_repository
from app.schemas.video import (
    IncidentSummary,
    ProcessingJobCreated,
    ProcessingProgressMessage,
    VideoProcessingResponse,
    VideoUploadResponse,
)
from app.services.alert_delivery import alert_delivery_service
from app.services.processing_jobs import JobStatus, ProcessingJob, processing_job_manager
from app.services.video_processing import ProcessedVideo, video_processing_service
from app.services.video_storage import video_storage_service

router = APIRouter()


def _processing_response(result: ProcessedVideo) -> VideoProcessingResponse:
    return VideoProcessingResponse(
        id=result.id,
        status="completed",
        processed_filename=result.processed_filename,
        frame_count=result.frame_count,
        width=result.width,
        height=result.height,
        fps=result.fps,
        duration_seconds=result.duration_seconds,
        detection_mode=result.detection_mode,
        total_person_detections=result.total_person_detections,
        frames_with_people=result.frames_with_people,
        unique_people_tracked=result.unique_people_tracked,
        maximum_inactivity_seconds=result.maximum_inactivity_seconds,
        maximum_risk_score=result.maximum_risk_score,
        danger_frame_count=result.danger_frame_count,
        pose_mode=result.pose_mode,
        pose_frames_analyzed=result.pose_frames_analyzed,
        incident_count=len(result.incidents),
        incidents=[
            IncidentSummary(
                id=incident.id,
                track_id=incident.track_id,
                risk_score=incident.risk_score,
                occurred_at_seconds=incident.occurred_at_seconds,
                status=incident.status,
                snapshot_url=f"/api/v1/incidents/{incident.id}/snapshot",
                clip_url=f"/api/v1/incidents/{incident.id}/clip",
                created_at=incident.created_at,
            )
            for incident in result.incidents
        ],
        download_url=f"/api/v1/videos/{result.id}/processed",
    )


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_video(
    file: Annotated[UploadFile, File(...)],
    user: CurrentUser,
) -> VideoUploadResponse:
    """Validate an uploaded pool video and save it using a safe generated name."""

    stored_video = await video_storage_service.store(file, user.id)
    return VideoUploadResponse(
        id=stored_video.id,
        original_filename=stored_video.original_filename,
        stored_filename=stored_video.stored_filename,
        content_type=stored_video.content_type,
        size_bytes=stored_video.size_bytes,
        status="uploaded",
        safety_notice=(
            "AquaGuard AI is an educational early-warning tool, not a certified safety "
            "device or replacement for trained lifeguards."
        ),
    )


@router.post("/{video_id}/process", response_model=VideoProcessingResponse)
async def process_video(video_id: str, user: CurrentUser) -> VideoProcessingResponse:
    """Read every frame with OpenCV and create an annotated output video."""

    safe_id = video_storage_service.require_owner(video_id, user.id)
    result = await run_in_threadpool(video_processing_service.process, safe_id)
    await incident_repository.save_many(result.incidents, user.id)
    await alert_delivery_service.dispatch_many(result.incidents)
    return _processing_response(result)


@router.post(
    "/{video_id}/process-background",
    response_model=ProcessingJobCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_background_processing(video_id: str, user: CurrentUser) -> ProcessingJobCreated:
    """Start processing immediately and return without waiting for the video."""

    # Validate the ID and upload before creating a job.
    safe_id = video_storage_service.require_owner(video_id, user.id)
    video_processing_service.find_upload(safe_id)
    job = processing_job_manager.start(safe_id, user.id)
    return ProcessingJobCreated(job_id=job.id, video_id=video_id, status=job.status)


@router.websocket("/ws/processing/{job_id}")
async def processing_progress(
    websocket: WebSocket,
    job_id: str,
    user: CurrentUser,
) -> None:
    """Stream actual frame-processing progress until completion or failure."""

    await websocket.accept()
    while True:
        job = processing_job_manager.get(job_id, user.id)
        if job is None:
            await websocket.send_json(
                {"status": "failed", "progress": 0, "error": "Job not found."}
            )
            await websocket.close(code=1008)
            return
        message = _job_message(job)
        await websocket.send_json(message.model_dump(mode="json"))
        if job.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            await websocket.close()
            return
        await asyncio.sleep(0.25)


def _job_message(job: ProcessingJob) -> ProcessingProgressMessage:
    return ProcessingProgressMessage(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        error=job.error,
        result=_processing_response(job.result) if job.result is not None else None,
    )


@router.get("/{video_id}/processed", response_class=FileResponse)
async def download_processed_video(video_id: str, user: CurrentUser) -> FileResponse:
    """Return a previously processed MP4 for browser playback or download."""

    safe_id = video_storage_service.require_owner(video_id, user.id)
    path = video_processing_service.get_processed_path(safe_id)
    return FileResponse(path, media_type="video/mp4", filename=path.name)


@router.post("/{video_id}/release", status_code=status.HTTP_204_NO_CONTENT)
async def release_video_files(video_id: str, user: CurrentUser) -> Response:
    """Delete temporary server video files after the owner's browser saved the result."""

    video_storage_service.release(video_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
