"""Incident evidence retrieval endpoints."""

import csv
from datetime import datetime
from io import StringIO
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import FileResponse

from app.core.auth import CurrentUser
from app.core.config import get_settings
from app.db.repositories import incident_repository
from app.models import IncidentDocument
from app.schemas.incident import IncidentListItem, IncidentNotesUpdate
from app.schemas.video import IncidentActionResponse
from app.services.incident_retention import incident_retention_service

router = APIRouter()


def _list_item(incident: IncidentDocument) -> IncidentListItem:
    return IncidentListItem(
        id=incident.id,
        video_id=incident.video_id,
        source=incident.source,
        source_name=incident.source_name,
        track_id=incident.track_id,
        severity=incident.severity,
        status=incident.status,
        risk_score=incident.risk_score,
        occurred_at_seconds=incident.occurred_at_seconds,
        triggered_signals=incident.triggered_signals,
        snapshot_url=f"/api/v1/incidents/{incident.id}/snapshot",
        clip_url=f"/api/v1/incidents/{incident.id}/clip",
        created_at=incident.created_at,
        notes=incident.notes,
    )


@router.get("", response_model=list[IncidentListItem])
async def list_incidents(
    user: CurrentUser,
    status_filter: str | None = Query(default=None, alias="status"),
    source: str | None = None,
    minimum_risk: float | None = Query(default=None, ge=0, le=100),
    search: str | None = Query(default=None, max_length=100),
    created_after: datetime | None = None,
    created_before: datetime | None = None,
) -> list[IncidentListItem]:
    incidents = await incident_repository.list_recent(
        owner_id=user.id,
        status_filter=status_filter,
        source_filter=source,
        minimum_risk=minimum_risk,
        search=search,
        created_after=created_after,
        created_before=created_before,
    )
    return [_list_item(incident) for incident in incidents]


@router.get("/export.csv")
async def export_incidents_csv(user: CurrentUser) -> Response:
    incidents = await incident_repository.list_recent(owner_id=user.id, limit=10000)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["created_at", "source", "source_name", "person_id", "risk", "status", "notes"])
    for incident in incidents:
        writer.writerow(
            [
                incident.created_at.isoformat(),
                incident.source,
                incident.source_name or "",
                incident.track_id,
                incident.risk_score,
                incident.status,
                incident.notes,
            ]
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aquaguard-incidents.csv"},
    )


async def _incident_file(incident_id: str, owner_id: str, kind: str) -> Path:
    incident = await incident_repository.get(incident_id, owner_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    filename = incident.snapshot_filename if kind == "snapshot" else incident.clip_filename
    folder = "snapshots" if kind == "snapshot" else "clips"
    path = get_settings().storage_root / "incidents" / folder / filename
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {kind} file not found.",
        )
    return path


@router.get("/{incident_id}/snapshot", response_class=FileResponse)
async def incident_snapshot(incident_id: str, user: CurrentUser) -> FileResponse:
    path = await _incident_file(incident_id, user.id, "snapshot")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/{incident_id}/clip", response_class=FileResponse)
async def incident_clip(incident_id: str, user: CurrentUser) -> FileResponse:
    path = await _incident_file(incident_id, user.id, "clip")
    return FileResponse(path, media_type="video/mp4")


@router.patch("/{incident_id}/acknowledge", response_model=IncidentActionResponse)
async def acknowledge_incident(incident_id: str, user: CurrentUser) -> IncidentActionResponse:
    """Record that an operator has seen and started responding to an alert."""

    incident = await incident_repository.acknowledge(incident_id, user.id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return IncidentActionResponse(id=incident.id, status=incident.status)


@router.patch("/{incident_id}/resolve", response_model=IncidentActionResponse)
async def resolve_incident(incident_id: str, user: CurrentUser) -> IncidentActionResponse:
    incident = await incident_repository.set_status(incident_id, user.id, "resolved")
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return IncidentActionResponse(id=incident.id, status=incident.status)


@router.patch("/{incident_id}/false-alarm", response_model=IncidentActionResponse)
async def mark_false_alarm(incident_id: str, user: CurrentUser) -> IncidentActionResponse:
    incident = await incident_repository.set_status(incident_id, user.id, "false_alarm")
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return IncidentActionResponse(id=incident.id, status=incident.status)


@router.patch("/{incident_id}/notes", response_model=IncidentListItem)
async def update_incident_notes(
    incident_id: str,
    payload: IncidentNotesUpdate,
    user: CurrentUser,
) -> IncidentListItem:
    incident = await incident_repository.update_notes(incident_id, user.id, payload.notes)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return _list_item(incident)


@router.delete("")
async def delete_all_incidents(user: CurrentUser) -> dict[str, int]:
    """Delete only the current user's reports, screenshots, and evidence clips."""

    deleted_count = await incident_retention_service.delete_all(user.id)
    return {"deleted": deleted_count}


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(incident_id: str, user: CurrentUser) -> Response:
    """Delete the MongoDB report, snapshot, and evidence clip permanently."""

    deleted = await incident_retention_service.delete(incident_id, user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
