"""Ultralytics ByteTrack adapter returning AquaGuard tracking objects."""

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from app.vision.detectors import Detection
from app.vision.tracking.centroid import TrackedPerson


@dataclass
class _TrackMemory:
    detection: Detection
    missed_frames: int = 0
    hits: int = 1


class YoloByteTracker:
    """Use YOLO and ByteTrack together for persistent identities through overlap."""

    mode = "yolo-bytetrack"

    def __init__(
        self,
        model_name: str,
        confidence: float,
        image_size: int,
        max_missed_frames: int,
        device: str | None = None,
    ) -> None:
        from ultralytics import YOLO

        self.model: Any = YOLO(model_name)
        self.confidence = confidence
        self.image_size = image_size
        self.max_missed_frames = max_missed_frames
        self.device = device
        self._tracks: dict[int, _TrackMemory] = {}
        self.created_track_ids: set[int] = set()

    def update(self, frame: NDArray[np.uint8]) -> list[TrackedPerson]:
        predictions: dict[str, object] = {
            "source": frame,
            "persist": True,
            "tracker": "bytetrack.yaml",
            "classes": [0],
            "conf": self.confidence,
            "imgsz": self.image_size,
            "verbose": False,
        }
        if self.device:
            predictions["device"] = self.device
        results = self.model.track(**predictions)
        visible: list[TrackedPerson] = []
        visible_ids: set[int] = set()
        for result in results:
            for box in result.boxes:
                if box.id is None:
                    continue
                track_id = int(box.id[0])
                x1, y1, x2, y2 = (int(value) for value in box.xyxy[0].tolist())
                detection = Detection(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=float(box.conf[0]),
                )
                memory = self._tracks.get(track_id)
                if memory is None:
                    self._tracks[track_id] = _TrackMemory(detection=detection)
                    self.created_track_ids.add(track_id)
                else:
                    memory.detection = detection
                    memory.missed_frames = 0
                    memory.hits += 1
                visible_ids.add(track_id)
                visible.append(TrackedPerson(track_id=track_id, detection=detection))
        for track_id in list(self._tracks):
            if track_id in visible_ids:
                continue
            memory = self._tracks[track_id]
            memory.missed_frames += 1
            if memory.missed_frames > self.max_missed_frames:
                del self._tracks[track_id]
        return visible

    def missing_people(self, minimum_hits: int = 5) -> list[TrackedPerson]:
        return [
            TrackedPerson(
                track_id=track_id,
                detection=memory.detection,
                missing_frames=memory.missed_frames,
            )
            for track_id, memory in self._tracks.items()
            if memory.missed_frames > 0 and memory.hits >= minimum_hits
        ]
