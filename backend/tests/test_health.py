"""Tests for application and database health endpoints."""

from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Start and stop the application around each test."""

    with TestClient(app) as test_client:
        yield test_client


def test_application_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "application": "AquaGuard AI",
        "environment": "development",
    }


def test_database_health(client: TestClient) -> None:
    with patch(
        "app.api.health.mongo_database.ping",
        new=AsyncMock(return_value=(True, "MongoDB responded successfully.")),
    ):
        response = client.get("/api/v1/health/database")

    assert response.status_code == 200
    assert response.json()["status"] == "connected"
    assert response.json()["database"] == "aquaguard"
