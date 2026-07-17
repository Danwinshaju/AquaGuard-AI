"""API tests for secure video upload validation and storage."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture
def upload_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    settings = get_settings()
    monkeypatch.setattr(settings, "storage_root", tmp_path)
    return tmp_path / "uploads"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_uploads_valid_mp4_with_generated_name(client: TestClient, upload_directory: Path) -> None:
    fake_mp4 = b"\x00\x00\x00\x18ftypmp42" + b"video-data"

    response = client.post(
        "/api/v1/videos/upload",
        files={"file": ("pool.MP4", fake_mp4, "video/mp4")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "pool.MP4"
    assert body["stored_filename"].endswith(".mp4")
    assert body["stored_filename"] != "pool.MP4"
    assert body["size_bytes"] == len(fake_mp4)
    assert (upload_directory / body["stored_filename"]).read_bytes() == fake_mp4


def test_rejects_unsupported_extension(client: TestClient, upload_directory: Path) -> None:
    response = client.post(
        "/api/v1/videos/upload",
        files={"file": ("notes.txt", b"not a video", "text/plain")},
    )

    assert response.status_code == 415
    assert not upload_directory.exists()


def test_rejects_mime_type_mismatch(client: TestClient, upload_directory: Path) -> None:
    response = client.post(
        "/api/v1/videos/upload",
        files={"file": ("pool.mp4", b"\x00\x00\x00\x18ftypmp42", "text/plain")},
    )

    assert response.status_code == 415
    assert not upload_directory.exists()


def test_rejects_invalid_signature_and_removes_partial_file(
    client: TestClient, upload_directory: Path
) -> None:
    response = client.post(
        "/api/v1/videos/upload",
        files={"file": ("fake.mp4", b"this is not an mp4", "video/mp4")},
    )

    assert response.status_code == 415
    assert list(upload_directory.iterdir()) == []


def test_rejects_file_above_configured_limit(
    client: TestClient, upload_directory: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "max_upload_size_mb", 1)
    oversized_mp4 = b"\x00\x00\x00\x18ftypmp42" + b"x" * (1024 * 1024)

    response = client.post(
        "/api/v1/videos/upload",
        files={"file": ("large.mp4", oversized_mp4, "video/mp4")},
    )

    assert response.status_code == 413
    assert list(upload_directory.iterdir()) == []
