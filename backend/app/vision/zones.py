"""Normalized pool and deep-water zone calibration."""

from dataclasses import dataclass

import cv2
from numpy.typing import NDArray

from app.vision.tracking import TrackedPerson


@dataclass(frozen=True)
class PoolZone:
    """A camera-independent rectangular pool region with a deep-water boundary."""

    left: float = 0.0
    top: float = 0.0
    right: float = 1.0
    bottom: float = 1.0
    deep_water_top: float = 0.55

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> "PoolZone":
        left = min(max(float(values.get("left", 0.0)), 0.0), 0.95)
        right = min(max(float(values.get("right", 1.0)), left + 0.05), 1.0)
        top = min(max(float(values.get("top", 0.0)), 0.0), 0.95)
        bottom = min(max(float(values.get("bottom", 1.0)), top + 0.05), 1.0)
        deep_water_top = min(
            max(float(values.get("deep_water_top", 0.55)), top),
            bottom,
        )
        return cls(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            deep_water_top=deep_water_top,
        )

    def contains(self, person: TrackedPerson, width: int, height: int) -> bool:
        center_x, center_y = person.center
        return (
            self.left <= center_x / max(width, 1) <= self.right
            and self.top <= center_y / max(height, 1) <= self.bottom
        )

    def is_deep(self, person: TrackedPerson, height: int) -> bool:
        return person.center[1] / max(height, 1) >= self.deep_water_top

    def draw(self, frame: NDArray) -> None:
        height, width = frame.shape[:2]
        start = (int(self.left * width), int(self.top * height))
        end = (int(self.right * width), int(self.bottom * height))
        cv2.rectangle(frame, start, end, (255, 190, 30), 2)
        deep_y = int(self.deep_water_top * height)
        cv2.line(frame, (start[0], deep_y), (end[0], deep_y), (180, 70, 255), 2)
        cv2.putText(
            frame,
            "POOL MONITORING ZONE",
            (start[0] + 8, min(start[1] + 24, height - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 190, 30),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "DEEP WATER",
            (start[0] + 8, min(deep_y + 22, height - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 70, 255),
            2,
            cv2.LINE_AA,
        )
