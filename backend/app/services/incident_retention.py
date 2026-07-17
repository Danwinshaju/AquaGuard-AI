"""Coordinated deletion of expired MongoDB incidents and evidence files."""

from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.db.repositories import incident_repository
from app.models import IncidentDocument


class IncidentRetentionService:
    """Delete evidence files before permanently removing their database record."""

    async def delete(self, incident_id: str, owner_id: str) -> bool:
        incident = await incident_repository.get(incident_id, owner_id)
        if incident is None:
            return False
        self._delete_evidence_files(incident)
        return await incident_repository.delete(incident.id, owner_id)

    async def release_evidence(self, incident_id: str, owner_id: str) -> bool:
        """Delete server evidence after its owner confirms browser storage succeeded."""

        incident = await incident_repository.get(incident_id, owner_id)
        if incident is None:
            return False
        self._delete_evidence_files(incident)
        return True

    async def cleanup_expired(self) -> int:
        """Delete every incident older than the configured retention period."""

        settings = get_settings()
        cutoff = datetime.now(UTC) - timedelta(hours=settings.incident_retention_hours)
        incidents = await incident_repository.list_created_before(cutoff)
        deleted_count = 0
        for incident in incidents:
            try:
                self._delete_evidence_files(incident)
                if await incident_repository.delete_system(incident.id):
                    deleted_count += 1
            except (OSError, ValueError):
                # Keep the MongoDB record so the next hourly pass can retry safely.
                continue
        return deleted_count

    async def delete_all(self, owner_id: str) -> int:
        """Permanently delete one user's incident evidence and documents."""

        incidents = await incident_repository.list_recent(owner_id=owner_id, limit=10000)
        deleted_count = 0
        for incident in incidents:
            self._delete_evidence_files(incident)
            if await incident_repository.delete(incident.id, owner_id):
                deleted_count += 1
        return deleted_count

    @staticmethod
    def _delete_evidence_files(incident: IncidentDocument) -> None:
        storage_root = get_settings().storage_root.resolve()
        evidence_files = (
            storage_root / "incidents" / "snapshots" / incident.snapshot_filename,
            storage_root / "incidents" / "clips" / incident.clip_filename,
        )
        for evidence_file in evidence_files:
            resolved_file = evidence_file.resolve()
            if storage_root not in resolved_file.parents:
                raise ValueError("Incident evidence path is outside the storage directory.")
            resolved_file.unlink(missing_ok=True)


incident_retention_service = IncidentRetentionService()
