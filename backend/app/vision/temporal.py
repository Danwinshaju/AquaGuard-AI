"""Optional sequence-based drowning classifier backed by a trained TorchScript model."""

from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from app.vision.movement import MovementMetrics
from app.vision.pose import PersonPose
from app.vision.tracking import TrackedPerson


class TemporalDrowningClassifier:
    """Accumulate motion/pose sequences and run a trained temporal model when available."""

    feature_count = 7

    def __init__(self, model_path: Path, sequence_length: int, device: str | None) -> None:
        self.sequence_length = sequence_length
        self.device = device or "cpu"
        self.histories: dict[int, deque[list[float]]] = defaultdict(
            lambda: deque(maxlen=sequence_length)
        )
        self.model: Any | None = None
        if model_path.is_file():
            import torch

            self.model = torch.jit.load(str(model_path), map_location=self.device)
            self.model.eval()

    @property
    def enabled(self) -> bool:
        return self.model is not None

    def update(
        self,
        people: list[TrackedPerson],
        movements: dict[int, MovementMetrics],
        poses: dict[int, PersonPose],
    ) -> dict[int, float]:
        probabilities: dict[int, float] = {}
        for person in people:
            movement = movements[person.track_id]
            pose = poses.get(person.track_id)
            self.histories[person.track_id].append(
                [
                    min(movement.speed_pixels_per_second / 300.0, 2.0),
                    min(movement.inactivity_seconds / 10.0, 2.0),
                    max(min(movement.delta_y_pixels / 100.0, 2.0), -2.0),
                    min(person.missing_frames / 15.0, 2.0),
                    pose.vertical_orientation_confidence if pose else 0.0,
                    pose.irregular_arm_confidence if pose else 0.0,
                    0.0 if pose is None or pose.head_visible else 1.0,
                ]
            )
            history = self.histories[person.track_id]
            if self.model is not None and len(history) == self.sequence_length:
                probabilities[person.track_id] = self._predict(list(history))
        return probabilities

    def _predict(self, features: list[list[float]]) -> float:
        import torch

        tensor = torch.tensor([features], dtype=torch.float32, device=self.device)
        with torch.inference_mode():
            probability = float(self.model(tensor).reshape(-1)[0].item())
        return min(max(probability, 0.0), 1.0)
