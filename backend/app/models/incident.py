"""MongoDB incident document created from a verified danger event."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class IncidentDocument(BaseModel):
    """Persistent evidence and lifecycle information for one danger incident."""

    id: str
    owner_id: str | None = None
    video_id: str
    source: Literal["uploaded_video", "live_camera"] = "uploaded_video"
    source_name: str | None = None
    track_id: int = Field(ge=1)
    severity: Literal["danger"] = "danger"
    status: Literal["unresolved", "acknowledged", "resolved", "false_alarm"] = "unresolved"
    risk_score: float = Field(ge=0, le=100)
    occurred_at_seconds: float = Field(ge=0)
    triggered_signals: list[str]
    snapshot_filename: str
    clip_filename: str
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    escalated_at: datetime | None = None
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
