from unittest.mock import AsyncMock

import cv2
import numpy as np

from app.core.config import get_settings
from app.db.repositories import incident_repository
from app.services.incident_evidence import IncidentEvidenceService
from app.services.incident_retention import incident_retention_service
from app.vision.risk import RiskAssessment, RiskStatus, SignalResult


def test_creates_snapshot_clip_and_incident_document(tmp_path) -> None:
    frame = np.full((64, 96, 3), 80, dtype=np.uint8)
    assessment = RiskAssessment(
        track_id=3,
        raw_score=90,
        score=82,
        status=RiskStatus.DANGER,
        danger_persistence_seconds=3,
        signals=(SignalResult("inactivity", True, 1, 35, "Inactive for 8 seconds."),),
    )

    incident = IncidentEvidenceService().create(
        video_id="video-id",
        track_id=3,
        assessment=assessment,
        timestamp_seconds=12.5,
        snapshot_frame=frame,
        clip_frames=[frame, frame],
        clip_fps=5,
        storage_root=tmp_path,
    )

    snapshot = tmp_path / "incidents" / "snapshots" / incident.snapshot_filename
    clip = tmp_path / "incidents" / "clips" / incident.clip_filename
    assert snapshot.is_file()
    assert cv2.imread(str(snapshot)) is not None
    assert clip.is_file()
    assert clip.stat().st_size > 0
    assert incident.status == "unresolved"
    assert incident.track_id == 3
    assert incident.triggered_signals == ["Inactive for 8 seconds."]


async def test_releases_server_evidence_without_deleting_report(tmp_path, monkeypatch) -> None:
    frame = np.full((64, 96, 3), 80, dtype=np.uint8)
    assessment = RiskAssessment(
        track_id=1,
        raw_score=90,
        score=85,
        status=RiskStatus.DANGER,
        danger_persistence_seconds=3,
        signals=(),
    )
    incident = IncidentEvidenceService().create(
        video_id="video-id",
        track_id=1,
        assessment=assessment,
        timestamp_seconds=2,
        snapshot_frame=frame,
        clip_frames=[frame],
        clip_fps=5,
        storage_root=tmp_path,
    )
    monkeypatch.setattr(get_settings(), "storage_root", tmp_path)
    get_incident = AsyncMock(return_value=incident)
    delete_incident = AsyncMock()
    monkeypatch.setattr(incident_repository, "get", get_incident)
    monkeypatch.setattr(incident_repository, "delete", delete_incident)

    released = await incident_retention_service.release_evidence(incident.id, "owner-1")

    assert released
    get_incident.assert_awaited_once_with(incident.id, "owner-1")
    delete_incident.assert_not_awaited()
    assert not (tmp_path / "incidents" / "snapshots" / incident.snapshot_filename).exists()
    assert not (tmp_path / "incidents" / "clips" / incident.clip_filename).exists()
