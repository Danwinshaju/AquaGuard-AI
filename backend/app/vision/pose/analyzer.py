"""Associate YOLO pose landmarks with existing person tracking IDs."""

from dataclasses import dataclass
from math import hypot
from typing import Any

import numpy as np
from numpy.typing import NDArray

from app.vision.tracking import TrackedPerson


@dataclass(frozen=True)
class PersonPose:
    """Pose-derived risk measurements and visible COCO keypoints."""

    track_id: int
    head_visible: bool
    vertical_orientation_confidence: float
    irregular_arm_confidence: float
    keypoints: dict[int, tuple[int, int, float]]


@dataclass(frozen=True)
class _PoseObservation:
    box: tuple[int, int, int, int]
    keypoints: dict[int, tuple[int, int, float]]


class YoloPoseAnalyzer:
    """Run a small YOLO pose model and calculate explainable pose signals."""

    def __init__(
        self,
        model_name: str,
        confidence: float,
        image_size: int,
        device: str | None = None,
    ) -> None:
        from ultralytics import YOLO

        self.model: Any = YOLO(model_name)
        self.confidence = confidence
        self.image_size = image_size
        self.device = device
        self._previous_wrists: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {}

    def analyze(
        self,
        frame: NDArray[np.uint8],
        tracked_people: list[TrackedPerson],
    ) -> dict[int, PersonPose]:
        """Return pose metrics matched to visible tracking boxes."""

        observations = self._predict(frame)
        poses: dict[int, PersonPose] = {}
        used_observations: set[int] = set()
        for person in tracked_people:
            person_box = (
                person.detection.x1,
                person.detection.y1,
                person.detection.x2,
                person.detection.y2,
            )
            candidates = sorted(
                (
                    (self._intersection_over_union(person_box, observation.box), index)
                    for index, observation in enumerate(observations)
                    if index not in used_observations
                ),
                reverse=True,
            )
            if not candidates or candidates[0][0] < 0.1:
                continue
            _, observation_index = candidates[0]
            used_observations.add(observation_index)
            observation = observations[observation_index]
            poses[person.track_id] = self._metrics(person, observation.keypoints)
        return poses

    def _predict(self, frame: NDArray[np.uint8]) -> list[_PoseObservation]:
        arguments: dict[str, Any] = {
            "source": frame,
            "conf": self.confidence,
            "imgsz": self.image_size,
            "verbose": False,
        }
        if self.device:
            arguments["device"] = self.device
        results = self.model.predict(**arguments)
        observations: list[_PoseObservation] = []
        for result in results:
            if result.keypoints is None:
                continue
            for index, box in enumerate(result.boxes):
                x1, y1, x2, y2 = (int(value) for value in box.xyxy[0].tolist())
                points = result.keypoints.data[index].tolist()
                keypoints = {
                    point_index: (int(point[0]), int(point[1]), float(point[2]))
                    for point_index, point in enumerate(points)
                }
                observations.append(_PoseObservation((x1, y1, x2, y2), keypoints))
        return observations

    def _metrics(
        self,
        person: TrackedPerson,
        keypoints: dict[int, tuple[int, int, float]],
    ) -> PersonPose:
        nose = keypoints.get(0, (0, 0, 0.0))
        head_visible = nose[2] >= self.confidence
        vertical_confidence = self._vertical_confidence(keypoints)
        irregular_arm_confidence = self._arm_confidence(person, keypoints)
        return PersonPose(
            track_id=person.track_id,
            head_visible=head_visible,
            vertical_orientation_confidence=vertical_confidence,
            irregular_arm_confidence=irregular_arm_confidence,
            keypoints=keypoints,
        )

    def _arm_confidence(
        self,
        person: TrackedPerson,
        keypoints: dict[int, tuple[int, int, float]],
    ) -> float:
        left = keypoints.get(9, (0, 0, 0.0))
        right = keypoints.get(10, (0, 0, 0.0))
        if left[2] < self.confidence or right[2] < self.confidence:
            return 0.0
        current = ((left[0], left[1]), (right[0], right[1]))
        previous = self._previous_wrists.get(person.track_id)
        self._previous_wrists[person.track_id] = current
        if previous is None:
            return 0.0
        movement = (
            hypot(current[0][0] - previous[0][0], current[0][1] - previous[0][1])
            + hypot(current[1][0] - previous[1][0], current[1][1] - previous[1][1])
        ) / 2
        box_width = person.detection.x2 - person.detection.x1
        box_height = person.detection.y2 - person.detection.y1
        diagonal = max(hypot(box_width, box_height), 1.0)
        return min((movement / diagonal) * 5.0, 1.0)

    def _vertical_confidence(
        self,
        keypoints: dict[int, tuple[int, int, float]],
    ) -> float:
        required = [keypoints.get(index, (0, 0, 0.0)) for index in (5, 6, 11, 12)]
        if any(point[2] < self.confidence for point in required):
            return 0.0
        shoulder_x = (required[0][0] + required[1][0]) / 2
        shoulder_y = (required[0][1] + required[1][1]) / 2
        hip_x = (required[2][0] + required[3][0]) / 2
        hip_y = (required[2][1] + required[3][1]) / 2
        horizontal = abs(hip_x - shoulder_x)
        vertical = abs(hip_y - shoulder_y)
        return vertical / max(hypot(horizontal, vertical), 1.0)

    @staticmethod
    def _intersection_over_union(
        first: tuple[int, int, int, int],
        second: tuple[int, int, int, int],
    ) -> float:
        intersection_width = max(min(first[2], second[2]) - max(first[0], second[0]), 0)
        intersection_height = max(min(first[3], second[3]) - max(first[1], second[1]), 0)
        intersection = intersection_width * intersection_height
        first_area = max(first[2] - first[0], 0) * max(first[3] - first[1], 0)
        second_area = max(second[2] - second[0], 0) * max(second[3] - second[1], 0)
        return intersection / max(first_area + second_area - intersection, 1)
