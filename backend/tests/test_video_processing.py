"""Tests for the Stage 4 OpenCV processing workflow."""

from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services.video_storage import video_storage_service


@pytest.fixture
def storage_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(get_settings(), "storage_root", tmp_path)
    (tmp_path / "uploads").mkdir()
    return tmp_path


def create_test_avi(path: Path, frame_count: int = 4) -> None:
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"MJPG"),
        5.0,
        (96, 64),
    )
    assert writer.isOpened()
    for index in range(frame_count):
        frame = np.full((64, 96, 3), 30 + index * 20, dtype=np.uint8)
        writer.write(frame)
    writer.release()


def test_processes_uploaded_video_and_serves_result(storage_root: Path) -> None:
    video_id = str(uuid4())
    create_test_avi(storage_root / "uploads" / f"{video_id}.avi")
    video_storage_service._owners[video_id] = "test-user"

    with TestClient(app) as client:
        response = client.post(f"/api/v1/videos/{video_id}/process")
        download = client.get(f"/api/v1/videos/{video_id}/processed")
        release = client.post(f"/api/v1/videos/{video_id}/release")
        missing_after_release = client.get(f"/api/v1/videos/{video_id}/processed")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["frame_count"] == 4
    assert response.json()["width"] == 96
    assert response.json()["height"] == 64
    assert response.json()["duration_seconds"] == 0.8
    assert response.json()["detection_mode"] == "mock"
    assert response.json()["total_person_detections"] == 4
    assert response.json()["frames_with_people"] == 4
    assert response.json()["unique_people_tracked"] == 1
    assert response.json()["maximum_inactivity_seconds"] == 0.6
    assert 0 <= response.json()["maximum_risk_score"] <= 100
    assert response.json()["danger_frame_count"] == 0
    assert response.json()["pose_mode"] == "disabled"
    assert response.json()["pose_frames_analyzed"] == 0
    assert response.json()["incident_count"] == 0
    assert response.json()["incidents"] == []
    assert download.status_code == 200
    assert download.headers["content-type"] == "video/mp4"
    assert len(download.content) > 0
    assert release.status_code == 204
    assert missing_after_release.status_code == 404
    assert not list((storage_root / "uploads").iterdir())
    assert not (storage_root / "processed" / f"{video_id}.mp4").exists()


def test_processing_rejects_invalid_id(storage_root: Path) -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/videos/not-a-uuid/process")

    assert response.status_code == 400


def test_processing_reports_missing_upload(storage_root: Path) -> None:
    with TestClient(app) as client:
        response = client.post(f"/api/v1/videos/{uuid4()}/process")

    assert response.status_code == 404


def test_temporary_video_is_restricted_to_its_owner() -> None:
    video_id = str(uuid4())
    video_storage_service._owners[video_id] = "owner-a"

    assert video_storage_service.require_owner(video_id, "owner-a") == video_id
    with pytest.raises(HTTPException) as error:
        video_storage_service.require_owner(video_id, "owner-b")

    assert error.value.status_code == 404
