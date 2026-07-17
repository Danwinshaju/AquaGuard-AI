"""Risk contribution from a separately trained temporal classifier."""

from app.vision.risk.types import RiskContext, SignalResult


class TemporalClassifierSignal:
    def __init__(self, threshold: float, weight: float) -> None:
        self.threshold = threshold
        self.weight = weight

    def evaluate(self, context: RiskContext) -> SignalResult:
        probability = context.temporal_drowning_probability
        triggered = probability is not None and probability >= self.threshold
        return SignalResult(
            name="temporal_drowning_classifier",
            triggered=triggered,
            confidence=probability or 0.0,
            risk_contribution=self.weight * (probability or 0.0) if triggered else 0.0,
            explanation=(f"Temporal drowning model probability was {(probability or 0.0):.0%}."),
        )
