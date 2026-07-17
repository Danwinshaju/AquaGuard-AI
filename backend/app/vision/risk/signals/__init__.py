"""Independent, explainable risk-signal modules."""

from app.vision.risk.signals.aquatic_model import AquaticModelSignal
from app.vision.risk.signals.deep_water import DeepWaterSignal
from app.vision.risk.signals.disappearance import DisappearanceSignal
from app.vision.risk.signals.head_visibility import HeadVisibilitySignal
from app.vision.risk.signals.inactivity import InactivitySignal
from app.vision.risk.signals.irregular_arms import IrregularArmMovementSignal
from app.vision.risk.signals.low_after_intense import LowMovementAfterIntenseSignal
from app.vision.risk.signals.sudden_downward import SuddenDownwardSignal
from app.vision.risk.signals.temporal_classifier import TemporalClassifierSignal
from app.vision.risk.signals.vertical_orientation import VerticalOrientationSignal

__all__ = [
    "AquaticModelSignal",
    "DeepWaterSignal",
    "DisappearanceSignal",
    "HeadVisibilitySignal",
    "InactivitySignal",
    "IrregularArmMovementSignal",
    "LowMovementAfterIntenseSignal",
    "SuddenDownwardSignal",
    "TemporalClassifierSignal",
    "VerticalOrientationSignal",
]
