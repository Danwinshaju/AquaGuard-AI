"""Detector-neutral types used by the video pipeline."""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Detection:
    """One person bounding box in pixel coordinates."""

    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_name: str = "person"


class PersonDetector(Protocol):
    """Contract shared by mock and YOLO detectors."""

    mode: str

    def detect(self, frame: NDArray[np.uint8]) -> list[Detection]:
        """Return all people found in one BGR OpenCV frame."""
