"""MongoDB client lifecycle management."""

from typing import Any

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import get_settings


class MongoDatabase:
    """Own the shared asynchronous MongoDB client and selected database."""

    def __init__(self) -> None:
        self.client: AsyncMongoClient[Any] | None = None
        self.database: AsyncDatabase[Any] | None = None

    def connect(self) -> None:
        """Create a lazy client; the first command establishes the network connection."""

        settings = get_settings()
        self.client = AsyncMongoClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=2000,
        )
        self.database = self.client[settings.mongodb_database]

    async def ping(self) -> tuple[bool, str]:
        """Return a friendly result instead of crashing when MongoDB is unavailable."""

        if self.client is None:
            return False, "MongoDB client has not been started."

        try:
            await self.client.admin.command("ping")
        except Exception as error:  # The health endpoint must report outages safely.
            return False, f"MongoDB ping failed: {error}"
        return True, "MongoDB responded successfully."

    async def close(self) -> None:
        """Release the MongoDB client's sockets during application shutdown."""

        if self.client is not None:
            await self.client.close()
        self.client = None
        self.database = None


mongo_database = MongoDatabase()
