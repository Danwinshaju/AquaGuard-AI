"""Deterministic detector for learning, demos, and automated tests."""

import numpy as np
from numpy.typing import NDArray

from app.vision.detectors.base import Detection


class MockPersonDetector:
    """Return one predictable central person box without running a model."""

    mode = "mock"

    def detect(self, frame: NDArray[np.uint8]) -> list[Detection]:
        height, width = frame.shape[:2]
        return [
            Detection(
                x1=width // 3,
                y1=height // 5,
                x2=(width * 2) // 3,
                y2=(height * 4) // 5,
                confidence=0.90,
            )
        ]
