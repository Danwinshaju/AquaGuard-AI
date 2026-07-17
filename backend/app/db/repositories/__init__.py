"""MongoDB repository implementations."""

from app.db.repositories.cameras import camera_repository
from app.db.repositories.incidents import incident_repository

__all__ = ["camera_repository", "incident_repository"]
