"""Risk contribution from the optional custom aquatic-behaviour YOLO model."""

from app.vision.risk.types import RiskContext, SignalResult


class AquaticModelSignal:
    name = "aquatic_model"

    def __init__(self, threshold: float, weight: float) -> None:
        self.threshold = threshold
        self.weight = weight

    def evaluate(self, context: RiskContext) -> SignalResult:
        probability = context.aquatic_drowning_probability
        if probability is None:
            return SignalResult(
                name=self.name,
                triggered=False,
                confidence=0.0,
                risk_contribution=0.0,
                explanation="Custom aquatic behaviour model is unavailable for this frame.",
            )
        triggered = probability >= self.threshold
        return SignalResult(
            name=self.name,
            triggered=triggered,
            confidence=probability,
            risk_contribution=self.weight * probability if triggered else 0.0,
            explanation=(
                f"Custom aquatic model detected drowning-like appearance ({probability:.0%})."
                if triggered
                else f"Custom aquatic model drowning confidence is low ({probability:.0%})."
            ),
        )
