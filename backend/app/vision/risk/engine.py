"""Rules-based risk scoring with smoothing and temporal danger verification."""

from dataclasses import dataclass

from app.core.config import get_settings
from app.vision.movement import MovementMetrics
from app.vision.pose import PersonPose
from app.vision.risk.signals import (
    AquaticModelSignal,
    DeepWaterSignal,
    DisappearanceSignal,
    HeadVisibilitySignal,
    InactivitySignal,
    IrregularArmMovementSignal,
    LowMovementAfterIntenseSignal,
    SuddenDownwardSignal,
    TemporalClassifierSignal,
    VerticalOrientationSignal,
)
from app.vision.risk.types import RiskAssessment, RiskContext, RiskStatus
from app.vision.tracking import TrackedPerson


@dataclass
class _RiskState:
    smoothed_score: float = 0.0
    danger_started_seconds: float | None = None
    recent_peak_speed: float = 0.0
    intense_movement_seconds: float | None = None
    deep_water_started_seconds: float | None = None


class RiskEngine:
    """Combine explainable signals separately for every tracking ID."""

    def __init__(
        self,
        *,
        inactivity_warning_seconds: float | None = None,
        danger_min: float | None = None,
        danger_persistence_seconds: float | None = None,
        smoothing_alpha: float | None = None,
    ) -> None:
        settings = get_settings()
        self.safe_max = settings.risk_safe_max
        self.danger_min = danger_min if danger_min is not None else settings.risk_danger_min
        self.persistence_required = (
            danger_persistence_seconds
            if danger_persistence_seconds is not None
            else settings.danger_persistence_seconds
        )
        self.alpha = smoothing_alpha or settings.risk_smoothing_alpha
        self.intense_speed = settings.intense_speed_pixels_per_second
        self.signals = (
            InactivitySignal(
                (
                    inactivity_warning_seconds
                    if inactivity_warning_seconds is not None
                    else settings.inactivity_warning_seconds
                ),
                weight=settings.risk_inactivity_weight,
            ),
            SuddenDownwardSignal(settings.sudden_downward_pixels),
            DisappearanceSignal(),
            VerticalOrientationSignal(),
            HeadVisibilitySignal(),
            IrregularArmMovementSignal(),
            LowMovementAfterIntenseSignal(
                settings.intense_speed_pixels_per_second,
                settings.low_speed_pixels_per_second,
            ),
            DeepWaterSignal(),
            TemporalClassifierSignal(
                settings.temporal_alert_threshold,
                settings.temporal_risk_weight,
            ),
            AquaticModelSignal(
                settings.aquatic_model_alert_threshold,
                settings.aquatic_model_risk_weight,
            ),
        )
        self._states: dict[int, _RiskState] = {}
        self.maximum_score = 0.0
        self.danger_frame_count = 0

    def evaluate(
        self,
        tracked_people: list[TrackedPerson],
        movements: dict[int, MovementMetrics],
        timestamp_seconds: float,
        poses: dict[int, PersonPose] | None = None,
        deep_zone_track_ids: set[int] | None = None,
        temporal_probabilities: dict[int, float] | None = None,
        aquatic_probabilities: dict[int, float] | None = None,
    ) -> dict[int, RiskAssessment]:
        """Calculate smoothed and temporally verified status for visible people."""

        assessments: dict[int, RiskAssessment] = {}
        poses = poses or {}
        deep_zone_track_ids = deep_zone_track_ids or set()
        temporal_probabilities = temporal_probabilities or {}
        aquatic_probabilities = aquatic_probabilities or {}
        for person in tracked_people:
            state = self._states.setdefault(person.track_id, _RiskState())
            movement = movements[person.track_id]
            if movement.speed_pixels_per_second >= self.intense_speed:
                state.recent_peak_speed = movement.speed_pixels_per_second
                state.intense_movement_seconds = timestamp_seconds
            seconds_since_intense = (
                timestamp_seconds - state.intense_movement_seconds
                if state.intense_movement_seconds is not None
                else None
            )
            pose = poses.get(person.track_id)
            in_deep_zone = person.track_id in deep_zone_track_ids
            if in_deep_zone and state.deep_water_started_seconds is None:
                state.deep_water_started_seconds = timestamp_seconds
            if not in_deep_zone:
                state.deep_water_started_seconds = None
            deep_zone_seconds = (
                timestamp_seconds - state.deep_water_started_seconds
                if state.deep_water_started_seconds is not None
                else 0.0
            )
            context = RiskContext(
                track_id=person.track_id,
                timestamp_seconds=timestamp_seconds,
                detection=person.detection,
                movement=movement,
                missing_frames=person.missing_frames,
                recent_peak_speed=state.recent_peak_speed,
                seconds_since_intense_movement=seconds_since_intense,
                head_visible=pose.head_visible if pose is not None else None,
                irregular_arm_confidence=(
                    pose.irregular_arm_confidence if pose is not None else None
                ),
                pose_vertical_confidence=(
                    pose.vertical_orientation_confidence if pose is not None else None
                ),
                in_deep_zone=in_deep_zone,
                deep_zone_seconds=deep_zone_seconds,
                temporal_drowning_probability=temporal_probabilities.get(person.track_id),
                aquatic_drowning_probability=aquatic_probabilities.get(person.track_id),
            )
            signal_results = tuple(signal.evaluate(context) for signal in self.signals)
            raw_score = min(sum(result.risk_contribution for result in signal_results), 100.0)
            state.smoothed_score = self.alpha * raw_score + (1 - self.alpha) * state.smoothed_score
            status, persistence = self._status(state, timestamp_seconds)
            score = round(state.smoothed_score, 1)
            self.maximum_score = max(self.maximum_score, score)
            if status is RiskStatus.DANGER:
                self.danger_frame_count += 1
            assessments[person.track_id] = RiskAssessment(
                track_id=person.track_id,
                raw_score=round(raw_score, 1),
                score=score,
                status=status,
                danger_persistence_seconds=round(persistence, 2),
                signals=signal_results,
            )
        return assessments

    def _status(
        self,
        state: _RiskState,
        timestamp_seconds: float,
    ) -> tuple[RiskStatus, float]:
        if state.smoothed_score >= self.danger_min:
            if state.danger_started_seconds is None:
                state.danger_started_seconds = timestamp_seconds
            persistence = timestamp_seconds - state.danger_started_seconds
            if persistence >= self.persistence_required:
                return RiskStatus.DANGER, persistence
            return RiskStatus.WARNING, persistence
        state.danger_started_seconds = None
        if state.smoothed_score >= self.safe_max:
            return RiskStatus.WARNING, 0.0
        return RiskStatus.SAFE, 0.0
