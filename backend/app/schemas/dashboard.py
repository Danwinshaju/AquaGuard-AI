"""Dashboard analytics response schemas."""

from pydantic import BaseModel, Field


class DailyAlertPoint(BaseModel):
    date: str
    alerts: int = Field(ge=0)


class DashboardResponse(BaseModel):
    active_cameras: int = Field(ge=0)
    people_detected: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    critical_alert_count: int = Field(ge=0)
    unresolved_incidents: int = Field(ge=0)
    average_acknowledgement_seconds: float = Field(ge=0)
    false_positive_rate: float = Field(ge=0, le=100)
    alerts_by_day: list[DailyAlertPoint]
