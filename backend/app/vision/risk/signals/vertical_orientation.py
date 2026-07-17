"""Bounding-box proxy for vertical body orientation before pose is available."""

from app.vision.risk.types import RiskContext, SignalResult


class VerticalOrientationSignal:
    name = "vertical_body_orientation"

    def __init__(self, ratio_threshold: float = 1.8, weight: float = 10.0) -> None:
        self.ratio_threshold = ratio_threshold
        self.weight = weight

    def evaluate(self, context: RiskContext) -> SignalResult:
        if context.pose_vertical_confidence is not None:
            confidence = min(max(context.pose_vertical_confidence, 0.0), 1.0)
            triggered = confidence >= 0.75
            return SignalResult(
                name=self.name,
                triggered=triggered,
                confidence=confidence,
                risk_contribution=self.weight * confidence if triggered else 0.0,
                explanation=f"Pose torso vertical-orientation confidence is {confidence:.0%}.",
            )
        width = max(context.detection.x2 - context.detection.x1, 1)
        height = max(context.detection.y2 - context.detection.y1, 1)
        ratio = height / width
        triggered = ratio >= self.ratio_threshold
        confidence = min(ratio / (self.ratio_threshold * 1.5), 1.0)
        return SignalResult(
            name=self.name,
            triggered=triggered,
            confidence=confidence,
            risk_contribution=self.weight * confidence if triggered else 0.0,
            explanation=f"Bounding-box height-to-width ratio is {ratio:.2f}.",
        )
