"""MongoDB persistence for user accounts and opaque login sessions."""

import asyncio
from datetime import UTC, datetime

from pymongo.errors import DuplicateKeyError

from app.db.mongodb import mongo_database
from app.models import UserDocument


class EmailAlreadyRegisteredError(ValueError):
    """Raised when signup attempts to reuse an existing email address."""


class AuthRepository:
    def __init__(self) -> None:
        self._indexes_ready = False
        self._index_lock = asyncio.Lock()

    @staticmethod
    def _database():
        if mongo_database.database is None:
            raise RuntimeError("MongoDB is not connected.")
        return mongo_database.database

    async def ensure_indexes(self) -> None:
        if self._indexes_ready:
            return
        async with self._index_lock:
            if self._indexes_ready:
                return
            database = self._database()
            await database.users.create_index("email", unique=True)
            await database.sessions.create_index("user_id")
            await database.sessions.create_index("expires_at", expireAfterSeconds=0)
            self._indexes_ready = True

    async def create_user(self, user: UserDocument) -> UserDocument:
        await self.ensure_indexes()
        document = user.model_dump()
        document["_id"] = document.pop("id")
        try:
            await self._database().users.insert_one(document)
        except DuplicateKeyError as error:
            raise EmailAlreadyRegisteredError("An account already uses this email.") from error
        return user

    async def get_user_by_email(self, email: str) -> UserDocument | None:
        await self.ensure_indexes()
        document = await self._database().users.find_one({"email": email})
        return self._user(document)

    async def get_user(self, user_id: str) -> UserDocument | None:
        document = await self._database().users.find_one({"_id": user_id})
        return self._user(document)

    async def create_session(
        self,
        *,
        token_hash: str,
        user_id: str,
        expires_at: datetime,
    ) -> None:
        await self.ensure_indexes()
        await self._database().sessions.insert_one(
            {
                "_id": token_hash,
                "user_id": user_id,
                "created_at": datetime.now(UTC),
                "expires_at": expires_at,
            }
        )

    async def user_for_session(self, token_hash: str) -> UserDocument | None:
        session = await self._database().sessions.find_one(
            {"_id": token_hash, "expires_at": {"$gt": datetime.now(UTC)}}
        )
        if session is None:
            return None
        return await self.get_user(str(session["user_id"]))

    async def delete_session(self, token_hash: str) -> None:
        await self._database().sessions.delete_one({"_id": token_hash})

    @staticmethod
    def _user(document: dict[str, object] | None) -> UserDocument | None:
        if document is None:
            return None
        document["id"] = document.pop("_id")
        return UserDocument.model_validate(document)


auth_repository = AuthRepository()
