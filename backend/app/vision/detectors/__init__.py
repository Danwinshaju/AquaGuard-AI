"""Person detector implementations and shared interfaces."""

from app.vision.detectors.base import Detection, PersonDetector
from app.vision.detectors.factory import create_person_detector

__all__ = ["Detection", "PersonDetector", "create_person_detector"]
