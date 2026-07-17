"""Persistent network-camera configuration."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class CameraDocument(BaseModel):
    id: str
    owner_id: str | None = None
    name: str = Field(min_length=1, max_length=80)
    source_url: str = Field(min_length=4, max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
