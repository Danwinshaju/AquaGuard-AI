"""MongoDB persistence for incident documents."""

from datetime import UTC, datetime

from app.db.mongodb import mongo_database
from app.models import IncidentDocument


class IncidentRepository:
    """Keep database query details outside API and vision services."""

    async def save_many(
        self,
        incidents: tuple[IncidentDocument, ...],
        owner_id: str,
    ) -> None:
        """Insert new incidents; do nothing when processing found no danger."""

        if not incidents:
            return
        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        documents = []
        for incident in incidents:
            document = incident.model_dump()
            document["owner_id"] = owner_id
            document["_id"] = document.pop("id")
            documents.append(document)
        await mongo_database.database.incidents.insert_many(documents)

    async def get(self, incident_id: str, owner_id: str) -> IncidentDocument | None:
        """Find one incident by its generated string identifier."""

        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        document = await mongo_database.database.incidents.find_one(
            {"_id": incident_id, "owner_id": owner_id}
        )
        if document is None:
            return None
        document["id"] = document.pop("_id")
        return IncidentDocument.model_validate(document)

    async def acknowledge(self, incident_id: str, owner_id: str) -> IncidentDocument | None:
        """Mark an unresolved incident as seen by the current operator."""

        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        now = datetime.now(UTC)
        document = await mongo_database.database.incidents.find_one_and_update(
            {"_id": incident_id, "owner_id": owner_id, "status": "unresolved"},
            {
                "$set": {
                    "status": "acknowledged",
                    "acknowledged_at": now,
                    "updated_at": now,
                }
            },
            return_document=True,
        )
        if document is None:
            return await self.get(incident_id, owner_id)
        document["id"] = document.pop("_id")
        return IncidentDocument.model_validate(document)

    async def list_recent(
        self,
        *,
        owner_id: str,
        limit: int = 100,
        status_filter: str | None = None,
        source_filter: str | None = None,
        minimum_risk: float | None = None,
        search: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> list[IncidentDocument]:
        """Return newest incidents with an optional lifecycle-status filter."""

        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        query: dict[str, object] = {"owner_id": owner_id}
        if status_filter:
            query["status"] = status_filter
        if source_filter:
            query["source"] = source_filter
        if minimum_risk is not None:
            query["risk_score"] = {"$gte": minimum_risk}
        if search:
            query["$or"] = [
                {"source_name": {"$regex": search, "$options": "i"}},
                {"video_id": {"$regex": search, "$options": "i"}},
            ]
        created_query: dict[str, datetime] = {}
        if created_after:
            created_query["$gte"] = created_after
        if created_before:
            created_query["$lte"] = created_before
        if created_query:
            query["created_at"] = created_query
        cursor = mongo_database.database.incidents.find(query).sort("created_at", -1).limit(limit)
        documents = await cursor.to_list(length=limit)
        incidents: list[IncidentDocument] = []
        for document in documents:
            document["id"] = document.pop("_id")
            incidents.append(IncidentDocument.model_validate(document))
        return incidents

    async def update_notes(
        self,
        incident_id: str,
        owner_id: str,
        notes: str,
    ) -> IncidentDocument | None:
        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        document = await mongo_database.database.incidents.find_one_and_update(
            {"_id": incident_id, "owner_id": owner_id},
            {"$set": {"notes": notes, "updated_at": datetime.now(UTC)}},
            return_document=True,
        )
        if document is None:
            return None
        document["id"] = document.pop("_id")
        return IncidentDocument.model_validate(document)

    async def list_created_before(
        self,
        cutoff: datetime,
        *,
        limit: int = 1000,
    ) -> list[IncidentDocument]:
        """Return incidents whose complete evidence has passed retention."""

        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        cursor = (
            mongo_database.database.incidents.find({"created_at": {"$lt": cutoff}})
            .sort("created_at", 1)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        incidents: list[IncidentDocument] = []
        for document in documents:
            document["id"] = document.pop("_id")
            incidents.append(IncidentDocument.model_validate(document))
        return incidents

    async def delete(self, incident_id: str, owner_id: str) -> bool:
        """Permanently remove one incident document from MongoDB."""

        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        result = await mongo_database.database.incidents.delete_one(
            {"_id": incident_id, "owner_id": owner_id}
        )
        return result.deleted_count == 1

    async def delete_system(self, incident_id: str) -> bool:
        """Delete an incident without owner filtering for automatic retention only."""

        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        result = await mongo_database.database.incidents.delete_one({"_id": incident_id})
        return result.deleted_count == 1

    async def list_unescalated_before(
        self,
        cutoff: datetime,
        *,
        limit: int = 100,
    ) -> list[IncidentDocument]:
        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        query = {
            "created_at": {"$lt": cutoff},
            "status": "unresolved",
            "escalated_at": None,
        }
        documents = await mongo_database.database.incidents.find(query).limit(limit).to_list(limit)
        incidents = []
        for document in documents:
            document["id"] = document.pop("_id")
            incidents.append(IncidentDocument.model_validate(document))
        return incidents

    async def mark_escalated(self, incident_id: str) -> None:
        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        await mongo_database.database.incidents.update_one(
            {"_id": incident_id},
            {"$set": {"escalated_at": datetime.now(UTC), "updated_at": datetime.now(UTC)}},
        )

    async def set_status(
        self,
        incident_id: str,
        owner_id: str,
        new_status: str,
    ) -> IncidentDocument | None:
        """Resolve or mark an incident as a false alarm."""

        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        now = datetime.now(UTC)
        update: dict[str, object] = {"status": new_status, "updated_at": now}
        if new_status in {"resolved", "false_alarm"}:
            update["resolved_at"] = now
        document = await mongo_database.database.incidents.find_one_and_update(
            {"_id": incident_id, "owner_id": owner_id},
            {"$set": update},
            return_document=True,
        )
        if document is None:
            return None
        document["id"] = document.pop("_id")
        return IncidentDocument.model_validate(document)


incident_repository = IncidentRepository()
