"""Create annotated snapshots and short incident evidence clips."""

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import cv2
import numpy as np
from numpy.typing import NDArray

from app.models import IncidentDocument
from app.services.media_encoding import media_encoding_service
from app.vision.risk import RiskAssessment


class IncidentEvidenceService:
    """Write evidence files and construct the matching database document."""

    def create(
        self,
        *,
        video_id: str,
        source: Literal["uploaded_video", "live_camera"] = "uploaded_video",
        source_name: str | None = None,
        track_id: int,
        assessment: RiskAssessment,
        timestamp_seconds: float,
        snapshot_frame: NDArray[np.uint8],
        clip_frames: Sequence[NDArray[np.uint8]],
        clip_fps: float,
        storage_root: Path,
    ) -> IncidentDocument:
        incident_id = str(uuid4())
        snapshot_directory = storage_root / "incidents" / "snapshots"
        clip_directory = storage_root / "incidents" / "clips"
        snapshot_directory.mkdir(parents=True, exist_ok=True)
        clip_directory.mkdir(parents=True, exist_ok=True)
        snapshot_filename = f"{incident_id}.jpg"
        clip_filename = f"{incident_id}.mp4"
        snapshot_path = snapshot_directory / snapshot_filename
        clip_path = clip_directory / clip_filename

        if not cv2.imwrite(str(snapshot_path), snapshot_frame):
            raise RuntimeError("OpenCV could not save the incident snapshot.")
        self._write_clip(clip_path, clip_frames, clip_fps, snapshot_frame)

        now = datetime.now(UTC)
        return IncidentDocument(
            id=incident_id,
            video_id=video_id,
            source=source,
            source_name=source_name,
            track_id=track_id,
            risk_score=assessment.score,
            occurred_at_seconds=timestamp_seconds,
            triggered_signals=[
                result.explanation for result in assessment.signals if result.triggered
            ],
            snapshot_filename=snapshot_filename,
            clip_filename=clip_filename,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _write_clip(
        path: Path,
        frames: Sequence[NDArray[np.uint8]],
        fps: float,
        fallback_frame: NDArray[np.uint8],
    ) -> None:
        frames_to_write = list(frames) or [fallback_frame]
        height, width = frames_to_write[0].shape[:2]
        opencv_path = path.with_suffix(".opencv.mp4")
        temporary_path = path.with_suffix(".part.mp4")
        writer = cv2.VideoWriter(
            str(opencv_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            opencv_path.unlink(missing_ok=True)
            raise RuntimeError("OpenCV could not create the incident evidence clip.")
        try:
            for frame in frames_to_write:
                writer.write(frame)
        finally:
            writer.release()
        try:
            media_encoding_service.convert_to_browser_mp4(opencv_path, temporary_path)
            path.unlink(missing_ok=True)
            temporary_path.replace(path)
        finally:
            opencv_path.unlink(missing_ok=True)
            temporary_path.unlink(missing_ok=True)


incident_evidence_service = IncidentEvidenceService()
