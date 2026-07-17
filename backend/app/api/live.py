"""WebSocket endpoint for browser-camera monitoring."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool

from app.core.auth import CurrentUser
from app.db.repositories import incident_repository
from app.services.alert_delivery import alert_delivery_service
from app.services.live_monitoring import LiveMonitoringSession

router = APIRouter()


@router.websocket("/ws")
async def live_camera(websocket: WebSocket, user: CurrentUser) -> None:
    """Receive JPEG frames and return metadata followed by annotated JPEG bytes."""

    await websocket.accept()
    try:
        session = await run_in_threadpool(LiveMonitoringSession)
        await websocket.send_json({"type": "ready"})
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                raise WebSocketDisconnect
            if message.get("text") is not None:
                payload = json.loads(message["text"])
                if payload.get("type") == "configure_zone":
                    session.configure_zone(payload.get("zone", {}))
                    await websocket.send_json({"type": "zone_configured"})
                elif payload.get("type") == "configure_performance":
                    session.configure_performance(str(payload.get("mode", "balanced")))
                    await websocket.send_json({"type": "performance_configured"})
                continue
            jpeg_bytes = message.get("bytes")
            if jpeg_bytes is None:
                continue
            metadata, annotated = await run_in_threadpool(session.process_jpeg, jpeg_bytes)
            incidents = session.drain_pending_incidents()
            await incident_repository.save_many(incidents, user.id)
            await alert_delivery_service.dispatch_many(incidents)
            metadata["incidents"] = [
                {
                    "id": incident.id,
                    "track_id": incident.track_id,
                    "risk_score": incident.risk_score,
                    "snapshot_url": f"/api/v1/incidents/{incident.id}/snapshot",
                    "clip_url": f"/api/v1/incidents/{incident.id}/clip",
                    "created_at": incident.created_at.isoformat(),
                }
                for incident in incidents
            ]
            await websocket.send_json({"type": "frame", **metadata})
            await websocket.send_bytes(annotated)
    except WebSocketDisconnect:
        return
    except Exception as error:
        await websocket.send_json({"type": "error", "message": str(error)})
        await websocket.close(code=1011)
