"""Ultralytics YOLO implementation of person detection."""

from typing import Any

import numpy as np
from numpy.typing import NDArray

from app.vision.detectors.base import Detection


class YoloPersonDetector:
    """Use a pretrained YOLO model and retain only COCO class 0 (person)."""

    mode = "yolo"

    def __init__(
        self,
        model_name: str,
        confidence: float,
        image_size: int,
        device: str | None = None,
    ) -> None:
        # Import lazily so MOCK_AI works even on machines without AI dependencies.
        from ultralytics import YOLO

        self.model: Any = YOLO(model_name)
        self.confidence = confidence
        self.image_size = image_size
        self.device = device

    def detect(self, frame: NDArray[np.uint8]) -> list[Detection]:
        arguments: dict[str, Any] = {
            "source": frame,
            "classes": [0],
            "conf": self.confidence,
            "imgsz": self.image_size,
            "verbose": False,
        }
        if self.device:
            arguments["device"] = self.device
        results = self.model.predict(**arguments)
        detections: list[Detection] = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = (int(value) for value in box.xyxy[0].tolist())
                detections.append(
                    Detection(
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        confidence=float(box.conf[0]),
                    )
                )
        return detections
