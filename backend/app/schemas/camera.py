"""Multi-camera request and status schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CameraCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    source_url: str = Field(min_length=4, max_length=1000)


class CameraStatus(BaseModel):
    id: str
    name: str
    status: Literal["starting", "online", "reconnecting", "stopped", "error"]
    people: int = Field(ge=0)
    highest_risk: float = Field(ge=0, le=100)
    last_frame_at: datetime | None
    reconnect_count: int = Field(ge=0)
    error: str | None
    stream_url: str
