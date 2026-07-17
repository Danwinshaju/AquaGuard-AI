"""Risk context from time spent inside a configured deep-water polygon."""

from app.vision.risk.types import RiskContext, SignalResult


class DeepWaterSignal:
    name = "deep_water_zone_time"

    def __init__(self, threshold_seconds: float = 15.0, weight: float = 10.0) -> None:
        self.threshold_seconds = threshold_seconds
        self.weight = weight

    def evaluate(self, context: RiskContext) -> SignalResult:
        triggered = context.in_deep_zone and context.deep_zone_seconds >= self.threshold_seconds
        confidence = (
            min(context.deep_zone_seconds / self.threshold_seconds, 1.0)
            if context.in_deep_zone
            else 0.0
        )
        return SignalResult(
            name=self.name,
            triggered=triggered,
            confidence=confidence,
            risk_contribution=self.weight * confidence if triggered else 0.0,
            explanation=(
                f"Deep-zone time is {context.deep_zone_seconds:.1f} seconds."
                if context.in_deep_zone
                else "Person is not inside a configured deep-water zone."
            ),
        )
