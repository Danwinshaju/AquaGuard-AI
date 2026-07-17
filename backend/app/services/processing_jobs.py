"""In-memory background video jobs with real progress values."""

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

from fastapi.concurrency import run_in_threadpool

from app.db.repositories import incident_repository
from app.services.alert_delivery import alert_delivery_service
from app.services.video_processing import ProcessedVideo, video_processing_service


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingJob:
    id: str
    video_id: str
    owner_id: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    result: ProcessedVideo | None = None
    error: str | None = None


class ProcessingJobManager:
    """Run CPU video work outside request handling and expose its progress."""

    def __init__(self) -> None:
        self._jobs: dict[str, ProcessingJob] = {}

    def start(self, video_id: str, owner_id: str) -> ProcessingJob:
        job = ProcessingJob(id=str(uuid4()), video_id=video_id, owner_id=owner_id)
        self._jobs[job.id] = job
        asyncio.create_task(self._run(job))
        return job

    def get(self, job_id: str, owner_id: str) -> ProcessingJob | None:
        job = self._jobs.get(job_id)
        return job if job is not None and job.owner_id == owner_id else None

    async def _run(self, job: ProcessingJob) -> None:
        job.status = JobStatus.PROCESSING

        def update_progress(value: float) -> None:
            job.progress = round(min(max(value, 0.0), 100.0), 1)

        try:
            result = await run_in_threadpool(
                video_processing_service.process,
                job.video_id,
                update_progress,
            )
            await incident_repository.save_many(result.incidents, job.owner_id)
            await alert_delivery_service.dispatch_many(result.incidents)
            job.result = result
            job.progress = 100.0
            job.status = JobStatus.COMPLETED
        except Exception as error:
            job.error = str(error)
            job.status = JobStatus.FAILED


processing_job_manager = ProcessingJobManager()
