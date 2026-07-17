"""Optional custom YOLO classifier/detector for aquatic behaviour labels."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from app.core.config import BACKEND_DIRECTORY
from app.vision.tracking import TrackedPerson


@dataclass(frozen=True)
class AquaticBehavior:
    track_id: int
    label: str
    confidence: float
    drowning_probability: float


class AquaticBehaviorAnalyzer:
    """Associate custom Drowning/Swimming detections with tracked people."""

    def __init__(
        self,
        model_path: Path,
        confidence: float,
        image_size: int,
        device: str | None = None,
        enabled: bool = True,
    ) -> None:
        if not model_path.is_absolute():
            model_path = BACKEND_DIRECTORY / model_path
        self.enabled = enabled and model_path.is_file()
        self.confidence = confidence
        self.image_size = image_size
        self.device = device
        self.model: Any | None = None
        if self.enabled:
            from ultralytics import YOLO

            self.model = YOLO(str(model_path))

    def analyze(
        self,
        frame: NDArray[np.uint8],
        tracked_people: list[TrackedPerson],
    ) -> dict[int, AquaticBehavior]:
        if not self.enabled or self.model is None or not tracked_people:
            return {}
        arguments: dict[str, object] = {
            "source": frame,
            "conf": self.confidence,
            "imgsz": self.image_size,
            "verbose": False,
        }
        if self.device:
            arguments["device"] = self.device
        results = self.model.predict(**arguments)
        candidates: list[tuple[tuple[int, int, int, int], str, float]] = []
        for result in results:
            names = result.names
            for box in result.boxes:
                class_id = int(box.cls[0])
                label = str(names[class_id])
                confidence = float(box.conf[0])
                coordinates = tuple(int(value) for value in box.xyxy[0].tolist())
                candidates.append((coordinates, label, confidence))

        matched: dict[int, AquaticBehavior] = {}
        used_candidates: set[int] = set()
        for person in tracked_people:
            person_box = (
                person.detection.x1,
                person.detection.y1,
                person.detection.x2,
                person.detection.y2,
            )
            best_index = -1
            best_overlap = 0.0
            for index, (candidate_box, _, _) in enumerate(candidates):
                if index in used_candidates:
                    continue
                overlap = _intersection_over_union(person_box, candidate_box)
                if overlap > best_overlap:
                    best_index = index
                    best_overlap = overlap
            if best_index < 0 or best_overlap < 0.15:
                continue
            used_candidates.add(best_index)
            _, label, confidence = candidates[best_index]
            normalized_label = label.strip().lower()
            matched[person.track_id] = AquaticBehavior(
                track_id=person.track_id,
                label=label,
                confidence=confidence,
                drowning_probability=(confidence if normalized_label == "drowning" else 0.0),
            )
        return matched


def _intersection_over_union(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> float:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    intersection = max(right - left, 0) * max(bottom - top, 0)
    first_area = max(first[2] - first[0], 0) * max(first[3] - first[1], 0)
    second_area = max(second[2] - second[0], 0) * max(second[3] - second[1], 0)
    return intersection / max(first_area + second_area - intersection, 1)
