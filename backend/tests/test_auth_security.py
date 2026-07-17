"""Focused tests for password protection and account-gated routes."""

from fastapi.testclient import TestClient

from app.core.auth import get_current_user, hash_password, verify_password
from app.main import app


def test_password_hash_is_salted_and_verifiable() -> None:
    first = hash_password("correct-horse-battery-staple")
    second = hash_password("correct-horse-battery-staple")

    assert first != second
    assert "correct-horse-battery-staple" not in first
    assert verify_password("correct-horse-battery-staple", first)
    assert not verify_password("wrong-password", first)


def test_incidents_require_login() -> None:
    override = app.dependency_overrides.pop(get_current_user, None)
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/incidents")
    finally:
        if override is not None:
            app.dependency_overrides[get_current_user] = override

    assert response.status_code == 401
