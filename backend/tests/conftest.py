"""Shared test isolation settings."""

import pytest

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.main import app
from app.models import UserDocument


@pytest.fixture(autouse=True)
def use_fast_mock_detection(monkeypatch: pytest.MonkeyPatch):
    """Keep automated tests deterministic even when local .env enables real YOLO."""

    monkeypatch.setattr(get_settings(), "mock_ai", True)
    monkeypatch.setattr(get_settings(), "pose_enabled", False)
    app.dependency_overrides[get_current_user] = lambda: UserDocument(
        id="test-user",
        name="Test User",
        email="test@example.com",
        password_hash="not-used-in-tests",
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)
