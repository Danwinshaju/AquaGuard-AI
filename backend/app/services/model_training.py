"""Background jobs for training the optional temporal classifier from labelled CSV."""

import asyncio
import subprocess
import sys
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from app.core.config import BACKEND_DIRECTORY, get_settings


class TrainingStatus(StrEnum):
    QUEUED = "queued"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TrainingJob:
    id: str
    dataset_path: Path
    epochs: int
    status: TrainingStatus = TrainingStatus.QUEUED
    output: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    error: str | None = None


class ModelTrainingManager:
    def __init__(self) -> None:
        self.jobs: dict[str, TrainingJob] = {}

    def start(self, dataset_path: Path, epochs: int) -> TrainingJob:
        job = TrainingJob(id=str(uuid4()), dataset_path=dataset_path, epochs=epochs)
        self.jobs[job.id] = job
        asyncio.create_task(self._run(job))
        return job

    def get(self, job_id: str) -> TrainingJob | None:
        return self.jobs.get(job_id)

    async def _run(self, job: TrainingJob) -> None:
        job.status = TrainingStatus.TRAINING
        settings = get_settings()
        output_path = settings.temporal_model_path
        if not output_path.is_absolute():
            output_path = BACKEND_DIRECTORY / output_path
        command = [
            sys.executable,
            str(BACKEND_DIRECTORY / "ml" / "train_temporal_model.py"),
            str(job.dataset_path),
            "--output",
            str(output_path),
            "--sequence-length",
            str(settings.temporal_sequence_length),
            "--epochs",
            str(job.epochs),
        ]
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                cwd=BACKEND_DIRECTORY,
                capture_output=True,
                text=True,
                timeout=7200,
                check=False,
            )
            job.output = result.stdout.splitlines()[-50:]
            if result.returncode != 0:
                job.error = result.stderr.strip() or "Training command failed."
                job.status = TrainingStatus.FAILED
                return
            for line in job.output:
                name, separator, value = line.partition("=")
                if separator and name in {
                    "accuracy",
                    "precision",
                    "recall",
                    "f1",
                    "false_positive_rate",
                }:
                    job.metrics[name] = float(value)
            job.status = TrainingStatus.COMPLETED
        except Exception as error:
            job.error = str(error)
            job.status = TrainingStatus.FAILED
        finally:
            job.dataset_path.unlink(missing_ok=True)


model_training_manager = ModelTrainingManager()
