"""Irregular-arm signal with an explicit pre-pose unavailable state."""

from app.vision.risk.types import RiskContext, SignalResult


class IrregularArmMovementSignal:
    name = "irregular_arm_movement"

    def __init__(self, trigger_confidence: float = 0.65, weight: float = 15.0) -> None:
        self.trigger_confidence = trigger_confidence
        self.weight = weight

    def evaluate(self, context: RiskContext) -> SignalResult:
        confidence = context.irregular_arm_confidence
        if confidence is None:
            return SignalResult(
                name=self.name,
                triggered=False,
                confidence=0.0,
                risk_contribution=0.0,
                explanation="Arm movement awaits the Stage 13 pose model.",
            )
        bounded_confidence = min(max(confidence, 0.0), 1.0)
        triggered = bounded_confidence >= self.trigger_confidence
        return SignalResult(
            name=self.name,
            triggered=triggered,
            confidence=bounded_confidence,
            risk_contribution=self.weight * bounded_confidence if triggered else 0.0,
            explanation=f"Irregular arm-motion confidence is {bounded_confidence:.0%}.",
        )
