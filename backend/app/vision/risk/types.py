"""Shared values passed between independent risk signals and the engine."""

from dataclasses import dataclass
from enum import StrEnum

from app.vision.detectors import Detection
from app.vision.movement import MovementMetrics


class RiskStatus(StrEnum):
    SAFE = "SAFE"
    WARNING = "WARNING"
    DANGER = "DANGER"


@dataclass(frozen=True)
class SignalResult:
    """Standard result returned by every risk signal."""

    name: str
    triggered: bool
    confidence: float
    risk_contribution: float
    explanation: str


@dataclass(frozen=True)
class RiskContext:
    """All measurements a signal may inspect for one person and frame."""

    track_id: int
    timestamp_seconds: float
    detection: Detection
    movement: MovementMetrics
    missing_frames: int = 0
    head_visible: bool | None = None
    irregular_arm_confidence: float | None = None
    pose_vertical_confidence: float | None = None
    in_deep_zone: bool = False
    deep_zone_seconds: float = 0.0
    recent_peak_speed: float = 0.0
    seconds_since_intense_movement: float | None = None
    temporal_drowning_probability: float | None = None
    aquatic_drowning_probability: float | None = None


@dataclass(frozen=True)
class RiskAssessment:
    """Smoothed score, status, and explainable signal details."""

    track_id: int
    raw_score: float
    score: float
    status: RiskStatus
    danger_persistence_seconds: float
    signals: tuple[SignalResult, ...]
