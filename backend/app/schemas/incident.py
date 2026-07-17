"""Incident list and action schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class IncidentListItem(BaseModel):
    id: str
    video_id: str
    source: Literal["uploaded_video", "live_camera"] = "uploaded_video"
    source_name: str | None = None
    track_id: int
    severity: str
    status: Literal["unresolved", "acknowledged", "resolved", "false_alarm"]
    risk_score: float = Field(ge=0, le=100)
    occurred_at_seconds: float
    triggered_signals: list[str]
    snapshot_url: str
    clip_url: str
    created_at: datetime
    notes: str = ""


class IncidentNotesUpdate(BaseModel):
    notes: str = Field(default="", max_length=1000)
