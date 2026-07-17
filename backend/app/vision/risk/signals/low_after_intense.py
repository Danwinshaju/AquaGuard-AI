"""Detect a low-motion period soon after intense movement."""

from app.vision.risk.types import RiskContext, SignalResult


class LowMovementAfterIntenseSignal:
    name = "low_movement_after_intense_movement"

    def __init__(
        self,
        intense_speed: float,
        low_speed: float,
        window_seconds: float = 10.0,
        weight: float = 25.0,
    ) -> None:
        self.intense_speed = intense_speed
        self.low_speed = low_speed
        self.window_seconds = window_seconds
        self.weight = weight

    def evaluate(self, context: RiskContext) -> SignalResult:
        since_intense = context.seconds_since_intense_movement
        triggered = (
            context.recent_peak_speed >= self.intense_speed
            and context.movement.speed_pixels_per_second <= self.low_speed
            and since_intense is not None
            and since_intense <= self.window_seconds
        )
        confidence = (
            min(context.recent_peak_speed / (self.intense_speed * 1.5), 1.0) if triggered else 0.0
        )
        return SignalResult(
            name=self.name,
            triggered=triggered,
            confidence=confidence,
            risk_contribution=self.weight * confidence if triggered else 0.0,
            explanation=(
                f"Current speed {context.movement.speed_pixels_per_second:.1f}px/s; "
                f"recent peak {context.recent_peak_speed:.1f}px/s."
            ),
        )
