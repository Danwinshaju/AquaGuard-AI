"""Risk contribution from rapid downward image movement."""

from app.vision.risk.types import RiskContext, SignalResult


class SuddenDownwardSignal:
    name = "sudden_downward_movement"

    def __init__(self, threshold_pixels: float, weight: float = 25.0) -> None:
        self.threshold_pixels = threshold_pixels
        self.weight = weight

    def evaluate(self, context: RiskContext) -> SignalResult:
        downward = max(context.movement.delta_y_pixels, 0.0)
        confidence = min(downward / (self.threshold_pixels * 2), 1.0)
        triggered = downward >= self.threshold_pixels
        return SignalResult(
            name=self.name,
            triggered=triggered,
            confidence=confidence,
            risk_contribution=self.weight * confidence if triggered else 0.0,
            explanation=f"Downward centre movement was {downward:.1f} pixels.",
        )
