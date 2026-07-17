"""Validated MongoDB document models."""

from app.models.camera import CameraDocument
from app.models.incident import IncidentDocument
from app.models.user import UserDocument

__all__ = ["CameraDocument", "IncidentDocument", "UserDocument"]
