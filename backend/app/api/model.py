"""Temporal-model dataset upload, training, and readiness endpoints."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.config import BACKEND_DIRECTORY, get_settings
from app.services.model_training import TrainingJob, model_training_manager

router = APIRouter()


def _job_response(job: TrainingJob) -> dict[str, object]:
    return {
        "id": job.id,
        "status": job.status,
        "metrics": job.metrics,
        "output": job.output,
        "error": job.error,
    }


@router.get("/status")
async def model_status() -> dict[str, object]:
    model_path = get_settings().temporal_model_path
    if not model_path.is_absolute():
        model_path = BACKEND_DIRECTORY / model_path
    aquatic_model_path = get_settings().aquatic_model_path
    if not aquatic_model_path.is_absolute():
        aquatic_model_path = BACKEND_DIRECTORY / aquatic_model_path
    return {
        "model_ready": model_path.is_file(),
        "model_path": str(model_path),
        "aquatic_model_ready": aquatic_model_path.is_file(),
        "aquatic_model_path": str(aquatic_model_path),
        "sequence_length": get_settings().temporal_sequence_length,
        "notice": "A trained file does not prove safety accuracy; validate on independent videos.",
    }


@router.get("/dataset-template", response_class=FileResponse)
async def dataset_template() -> FileResponse:
    return FileResponse(
        BACKEND_DIRECTORY / "ml" / "dataset-template.csv",
        media_type="text/csv",
        filename="aquaguard-dataset-template.csv",
    )


@router.post("/train", status_code=status.HTTP_202_ACCEPTED)
async def train_model(
    file: Annotated[UploadFile, File(...)],
    epochs: Annotated[int, Form(ge=1, le=500)] = 30,
) -> dict[str, object]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Choose a labelled CSV dataset.")
    training_directory = get_settings().storage_root / "training"
    training_directory.mkdir(parents=True, exist_ok=True)
    dataset_path = training_directory / f"{uuid4()}.csv"
    size = 0
    with dataset_path.open("wb") as destination:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > 100 * 1024 * 1024:
                dataset_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Training CSV exceeds 100 MB.")
            destination.write(chunk)
    job = model_training_manager.start(dataset_path, epochs)
    return _job_response(job)


@router.get("/jobs/{job_id}")
async def training_job(job_id: str) -> dict[str, object]:
    job = model_training_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Training job not found.")
    return _job_response(job)
