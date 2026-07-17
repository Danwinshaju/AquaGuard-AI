"""Typed responses returned by the health endpoints."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Basic application liveness information."""

    status: Literal["ok"]
    application: str
    environment: str


class DatabaseHealthResponse(BaseModel):
    """MongoDB connectivity information."""

    status: Literal["connected", "disconnected"]
    database: str
    detail: str
