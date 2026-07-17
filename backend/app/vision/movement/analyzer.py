"""Track centre-point movement and inactivity separately for every person."""

from dataclasses import dataclass
from math import hypot

from app.vision.tracking import TrackedPerson


@dataclass(frozen=True)
class MovementMetrics:
    """Movement values calculated for one person in the current frame."""

    track_id: int
    center: tuple[float, float]
    displacement_pixels: float
    delta_x_pixels: float
    delta_y_pixels: float
    speed_pixels_per_second: float
    total_distance_pixels: float
    inactivity_seconds: float
    is_inactive: bool


@dataclass
class _MovementState:
    """Mutable time-series state retained for one tracking ID."""

    last_center: tuple[float, float]
    last_seen_seconds: float
    last_significant_movement_seconds: float
    total_distance_pixels: float = 0.0


class MovementAnalyzer:
    """Calculate frame-to-frame movement without mixing different people."""

    def __init__(self, movement_threshold: float, inactivity_threshold: float) -> None:
        self.movement_threshold = movement_threshold
        self.inactivity_threshold = inactivity_threshold
        self._states: dict[int, _MovementState] = {}
        self.maximum_inactivity_seconds = 0.0

    def update(
        self,
        tracked_people: list[TrackedPerson],
        timestamp_seconds: float,
    ) -> dict[int, MovementMetrics]:
        """Update visible tracks and return metrics keyed by tracking ID."""

        metrics_by_track: dict[int, MovementMetrics] = {}
        for tracked_person in tracked_people:
            track_id = tracked_person.track_id
            center = tracked_person.center
            state = self._states.get(track_id)

            if state is None:
                state = _MovementState(
                    last_center=center,
                    last_seen_seconds=timestamp_seconds,
                    last_significant_movement_seconds=timestamp_seconds,
                )
                self._states[track_id] = state
                displacement = 0.0
                delta_x = 0.0
                delta_y = 0.0
                elapsed_seconds = 0.0
            else:
                delta_x = center[0] - state.last_center[0]
                delta_y = center[1] - state.last_center[1]
                displacement = hypot(
                    delta_x,
                    delta_y,
                )
                elapsed_seconds = max(timestamp_seconds - state.last_seen_seconds, 0.0)
                state.total_distance_pixels += displacement
                if displacement >= self.movement_threshold:
                    state.last_significant_movement_seconds = timestamp_seconds
                state.last_center = center
                state.last_seen_seconds = timestamp_seconds

            inactivity_seconds = max(
                timestamp_seconds - state.last_significant_movement_seconds,
                0.0,
            )
            speed = displacement / elapsed_seconds if elapsed_seconds > 0 else 0.0
            self.maximum_inactivity_seconds = max(
                self.maximum_inactivity_seconds,
                inactivity_seconds,
            )
            metrics_by_track[track_id] = MovementMetrics(
                track_id=track_id,
                center=center,
                displacement_pixels=displacement,
                delta_x_pixels=delta_x,
                delta_y_pixels=delta_y,
                speed_pixels_per_second=speed,
                total_distance_pixels=state.total_distance_pixels,
                inactivity_seconds=inactivity_seconds,
                is_inactive=inactivity_seconds >= self.inactivity_threshold,
            )

        return metrics_by_track
