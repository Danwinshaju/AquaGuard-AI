"""Unit tests for Stage 8 risk scoring and temporal verification."""

from app.core.config import get_settings
from app.vision.detectors import Detection
from app.vision.movement import MovementMetrics
from app.vision.risk import RiskEngine, RiskStatus
from app.vision.risk.signals.disappearance import DisappearanceSignal
from app.vision.risk.signals.inactivity import InactivitySignal
from app.vision.risk.signals.sudden_downward import SuddenDownwardSignal
from app.vision.risk.types import RiskContext
from app.vision.tracking import TrackedPerson


def values(inactive: float = 0, delta_y: float = 0, speed: float = 0) -> MovementMetrics:
    return MovementMetrics(
        track_id=1,
        center=(50, 50),
        displacement_pixels=abs(delta_y),
        delta_x_pixels=0,
        delta_y_pixels=delta_y,
        speed_pixels_per_second=speed,
        total_distance_pixels=abs(delta_y),
        inactivity_seconds=inactive,
        is_inactive=inactive >= 5,
    )


def context(movement: MovementMetrics) -> RiskContext:
    return RiskContext(
        track_id=1,
        timestamp_seconds=0,
        detection=Detection(30, 10, 70, 90, 0.9),
        movement=movement,
    )


def person() -> TrackedPerson:
    return TrackedPerson(1, Detection(30, 10, 70, 90, 0.9))


def test_inactivity_signal_has_standard_explainable_result() -> None:
    result = InactivitySignal(threshold_seconds=5, weight=80).evaluate(context(values(inactive=6)))

    assert result.triggered is True
    assert result.confidence == 1
    assert result.risk_contribution == 80
    assert "6.0 seconds" in result.explanation


def test_downward_signal_ignores_upward_motion() -> None:
    result = SuddenDownwardSignal(threshold_pixels=20).evaluate(context(values(delta_y=-30)))

    assert result.triggered is False
    assert result.risk_contribution == 0


def test_danger_requires_continuous_persistence(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "risk_smoothing_alpha", 1.0)
    monkeypatch.setattr(settings, "danger_persistence_seconds", 3.0)
    engine = RiskEngine()
    # Replace the normal signals with two deterministic high-risk inactivity signals.
    engine.signals = (InactivitySignal(1, weight=50), InactivitySignal(1, weight=50))
    moving = values(inactive=5)

    early = engine.evaluate([person()], {1: moving}, timestamp_seconds=0)[1]
    middle = engine.evaluate([person()], {1: moving}, timestamp_seconds=2.9)[1]
    confirmed = engine.evaluate([person()], {1: moving}, timestamp_seconds=3.0)[1]

    assert early.status is RiskStatus.WARNING
    assert middle.status is RiskStatus.WARNING
    assert confirmed.status is RiskStatus.DANGER


def test_danger_timer_resets_when_score_falls(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "risk_smoothing_alpha", 1.0)
    engine = RiskEngine()
    engine.signals = (InactivitySignal(1, weight=100),)

    engine.evaluate([person()], {1: values(inactive=5)}, timestamp_seconds=0)
    safe = engine.evaluate([person()], {1: values(inactive=0)}, timestamp_seconds=1)[1]
    restarted = engine.evaluate([person()], {1: values(inactive=5)}, timestamp_seconds=4)[1]

    assert safe.status is RiskStatus.SAFE
    assert restarted.status is RiskStatus.WARNING
    assert restarted.danger_persistence_seconds == 0


def test_established_missing_track_contributes_high_risk(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "risk_smoothing_alpha", 1.0)
    engine = RiskEngine()
    engine.signals = (DisappearanceSignal(threshold_frames=5, weight=80),)
    missing_person = TrackedPerson(
        track_id=1,
        detection=Detection(30, 10, 70, 90, 0.9),
        missing_frames=5,
    )

    assessment = engine.evaluate(
        [missing_person],
        {1: values(inactive=1)},
        timestamp_seconds=1,
    )[1]

    assert assessment.raw_score == 80
    assert assessment.status is RiskStatus.WARNING
