"""Tests for trained temporal-model risk contribution."""

from app.vision.detectors import Detection
from app.vision.movement import MovementMetrics
from app.vision.risk.signals.temporal_classifier import TemporalClassifierSignal
from app.vision.risk.types import RiskContext


def test_temporal_probability_triggers_only_above_threshold() -> None:
    movement = MovementMetrics(1, (50, 50), 0, 0, 0, 0, 0, 0, False)
    context = RiskContext(
        track_id=1,
        timestamp_seconds=1,
        detection=Detection(20, 20, 80, 80, 0.9),
        movement=movement,
        temporal_drowning_probability=0.8,
    )

    result = TemporalClassifierSignal(threshold=0.65, weight=45).evaluate(context)

    assert result.triggered
    assert result.risk_contribution == 36
