"""Optional webhook/email notification and unacknowledged-alert escalation."""

import asyncio
import json
import logging
import smtplib
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.db.repositories import incident_repository
from app.models import IncidentDocument

logger = logging.getLogger(__name__)


class AlertDeliveryService:
    async def dispatch_many(
        self,
        incidents: tuple[IncidentDocument, ...],
        *,
        escalated: bool = False,
    ) -> None:
        for incident in incidents:
            await self.dispatch(incident, escalated=escalated)

    async def dispatch(self, incident: IncidentDocument, *, escalated: bool = False) -> None:
        settings = get_settings()
        label = "ESCALATED" if escalated else "NEW"
        payload = {
            "event": "aquaguard_danger",
            "level": label,
            "incident_id": incident.id,
            "source": incident.source,
            "person_id": incident.track_id,
            "risk_score": incident.risk_score,
            "created_at": incident.created_at.isoformat(),
            "message": "Possible drowning behavior - verify immediately and alert a lifeguard.",
        }
        tasks = []
        if settings.alert_webhook_url:
            tasks.append(asyncio.to_thread(self._send_webhook, settings.alert_webhook_url, payload))
        if settings.smtp_host and settings.alert_email_to:
            tasks.append(asyncio.to_thread(self._send_email, payload))
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error("Alert delivery failed: %s", result)

    @staticmethod
    def _send_webhook(url: str, payload: dict[str, object]) -> None:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=8) as response:
            if response.status >= 400:
                raise RuntimeError(f"Webhook returned HTTP {response.status}.")

    @staticmethod
    def _send_email(payload: dict[str, object]) -> None:
        settings = get_settings()
        message = EmailMessage()
        message["Subject"] = f"AquaGuard {payload['level']} danger alert"
        message["From"] = settings.smtp_username or "aquaguard@localhost"
        message["To"] = settings.alert_email_to
        message.set_content("\n".join(f"{key}: {value}" for key, value in payload.items()))
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=8) as client:
            if settings.smtp_use_tls:
                client.starttls()
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)

    async def escalate_due_incidents(self) -> int:
        settings = get_settings()
        cutoff = datetime.now(UTC) - timedelta(seconds=settings.alert_escalation_seconds)
        incidents = await incident_repository.list_unescalated_before(cutoff)
        for incident in incidents:
            await self.dispatch(incident, escalated=True)
            await incident_repository.mark_escalated(incident.id)
        return len(incidents)


alert_delivery_service = AlertDeliveryService()
