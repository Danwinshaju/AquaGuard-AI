"""Dashboard summary and chart endpoints."""

from collections import Counter

from fastapi import APIRouter

from app.core.auth import CurrentUser
from app.db.repositories import incident_repository
from app.schemas.dashboard import DailyAlertPoint, DashboardResponse
from app.services.camera_manager import camera_manager

router = APIRouter()


@router.get("/summary", response_model=DashboardResponse)
async def dashboard_summary(user: CurrentUser) -> DashboardResponse:
    incidents = await incident_repository.list_recent(owner_id=user.id, limit=500)
    user_cameras = [
        camera for camera in camera_manager.cameras.values() if camera.owner_id == user.id
    ]
    unresolved = [item for item in incidents if item.status in {"unresolved", "acknowledged"}]
    acknowledged_durations = [
        (item.acknowledged_at - item.created_at).total_seconds()
        for item in incidents
        if item.acknowledged_at is not None
    ]
    false_alarms = sum(item.status == "false_alarm" for item in incidents)
    daily_counts = Counter(item.created_at.date().isoformat() for item in incidents)
    return DashboardResponse(
        active_cameras=sum(camera.status == "online" for camera in user_cameras),
        people_detected=sum(camera.people for camera in user_cameras),
        warning_count=sum(camera.highest_risk >= 40 for camera in user_cameras),
        critical_alert_count=len(incidents),
        unresolved_incidents=len(unresolved),
        average_acknowledgement_seconds=(
            round(sum(acknowledged_durations) / len(acknowledged_durations), 1)
            if acknowledged_durations
            else 0.0
        ),
        false_positive_rate=(round(false_alarms / len(incidents) * 100, 1) if incidents else 0.0),
        alerts_by_day=[
            DailyAlertPoint(date=date, alerts=count)
            for date, count in sorted(daily_counts.items())[-14:]
        ],
    )
