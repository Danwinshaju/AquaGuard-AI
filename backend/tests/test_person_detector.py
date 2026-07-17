"""Unit tests for the detector-neutral Stage 5 interface."""

import numpy as np

from app.vision.detectors.mock import MockPersonDetector


def test_mock_detector_returns_bounded_person_box() -> None:
    frame = np.zeros((300, 600, 3), dtype=np.uint8)

    detections = MockPersonDetector().detect(frame)

    assert len(detections) == 1
    detection = detections[0]
    assert detection.class_name == "person"
    assert detection.confidence == 0.90
    assert (detection.x1, detection.y1, detection.x2, detection.y2) == (200, 60, 400, 240)
