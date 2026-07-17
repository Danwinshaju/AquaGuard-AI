"""Account document used to isolate each user's AquaGuard data."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class UserDocument(BaseModel):
    """Private MongoDB representation of an AquaGuard account."""

    id: str
    name: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
