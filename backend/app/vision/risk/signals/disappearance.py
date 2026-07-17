"""Risk contribution when an established track temporarily disappears."""

from app.vision.risk.types import RiskContext, SignalResult


class DisappearanceSignal:
    name = "person_disappearance"

    def __init__(self, threshold_frames: int = 5, weight: float = 80.0) -> None:
        self.threshold_frames = threshold_frames
        self.weight = weight

    def evaluate(self, context: RiskContext) -> SignalResult:
        confidence = min(context.missing_frames / max(self.threshold_frames, 1), 1.0)
        triggered = context.missing_frames >= self.threshold_frames
        return SignalResult(
            name=self.name,
            triggered=triggered,
            confidence=confidence,
            risk_contribution=self.weight * confidence if triggered else 0.0,
            explanation=f"Track has been missing for {context.missing_frames} frames.",
        )
