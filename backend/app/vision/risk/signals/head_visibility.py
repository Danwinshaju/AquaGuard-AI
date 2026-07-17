"""Head-visibility signal with an explicit pre-pose unavailable state."""

from app.vision.risk.types import RiskContext, SignalResult


class HeadVisibilitySignal:
    name = "head_visibility"

    def __init__(self, weight: float = 15.0) -> None:
        self.weight = weight

    def evaluate(self, context: RiskContext) -> SignalResult:
        if context.head_visible is None:
            return SignalResult(
                name=self.name,
                triggered=False,
                confidence=0.0,
                risk_contribution=0.0,
                explanation="Head visibility awaits the Stage 13 pose model.",
            )
        triggered = not context.head_visible
        return SignalResult(
            name=self.name,
            triggered=triggered,
            confidence=1.0,
            risk_contribution=self.weight if triggered else 0.0,
            explanation=(
                "Head landmark is not visible." if triggered else "Head landmark is visible."
            ),
        )
