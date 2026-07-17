"""Risk contribution from prolonged lack of significant movement."""

from app.vision.risk.types import RiskContext, SignalResult


class InactivitySignal:
    name = "inactivity"

    def __init__(self, threshold_seconds: float, weight: float = 35.0) -> None:
        self.threshold_seconds = threshold_seconds
        self.weight = weight

    def evaluate(self, context: RiskContext) -> SignalResult:
        confidence = min(context.movement.inactivity_seconds / self.threshold_seconds, 1.0)
        triggered = context.movement.inactivity_seconds >= self.threshold_seconds
        return SignalResult(
            name=self.name,
            triggered=triggered,
            confidence=confidence,
            risk_contribution=self.weight * confidence if triggered else 0.0,
            explanation=(
                f"Person inactive for {context.movement.inactivity_seconds:.1f} seconds "
                f"(threshold {self.threshold_seconds:.1f})."
            ),
        )
