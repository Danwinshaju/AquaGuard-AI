"""Select the configured person detector."""

from app.core.config import get_settings
from app.vision.detectors.base import PersonDetector
from app.vision.detectors.mock import MockPersonDetector
from app.vision.detectors.yolo import YoloPersonDetector


def create_person_detector(
    *,
    confidence: float | None = None,
    image_size: int | None = None,
) -> PersonDetector:
    """Create mock or real YOLO detection from environment settings."""

    settings = get_settings()
    if settings.mock_ai:
        return MockPersonDetector()
    return YoloPersonDetector(
        model_name=settings.yolo_model,
        confidence=(confidence if confidence is not None else settings.detection_confidence),
        image_size=image_size if image_size is not None else settings.yolo_image_size,
        device=settings.yolo_device or None,
    )
