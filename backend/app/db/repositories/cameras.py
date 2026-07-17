"""MongoDB persistence for network-camera configurations."""

from app.db.mongodb import mongo_database
from app.models import CameraDocument


class CameraRepository:
    async def save(self, camera: CameraDocument) -> None:
        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        document = camera.model_dump()
        camera_id = document.pop("id")
        await mongo_database.database.cameras.update_one(
            {"_id": camera_id},
            {"$set": document},
            upsert=True,
        )

    async def list_all(self) -> list[CameraDocument]:
        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        documents = (
            await mongo_database.database.cameras.find({}).sort("created_at", 1).to_list(length=100)
        )
        cameras: list[CameraDocument] = []
        for document in documents:
            document["id"] = document.pop("_id")
            cameras.append(CameraDocument.model_validate(document))
        return cameras

    async def delete(self, camera_id: str, owner_id: str) -> None:
        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        await mongo_database.database.cameras.delete_one(
            {"_id": camera_id, "owner_id": owner_id}
        )


camera_repository = CameraRepository()
