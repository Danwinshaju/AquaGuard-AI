"""Tests for normalized pool and deep-water calibration."""

from app.vision.detectors import Detection
from app.vision.tracking import TrackedPerson
from app.vision.zones import PoolZone


def test_pool_zone_filters_people_and_marks_deep_water() -> None:
    zone = PoolZone(left=0.1, top=0.1, right=0.9, bottom=0.9, deep_water_top=0.6)
    inside = TrackedPerson(1, Detection(40, 60, 60, 80, 0.9))
    outside = TrackedPerson(2, Detection(0, 0, 10, 10, 0.9))

    assert zone.contains(inside, width=100, height=100)
    assert zone.is_deep(inside, height=100)
    assert not zone.contains(outside, width=100, height=100)


def test_invalid_pool_zone_is_normalized_safely() -> None:
    zone = PoolZone.from_dict(
        {"left": 0.8, "right": 0.2, "top": 0.6, "bottom": 0.7, "deep_water_top": 0.3}
    )

    assert zone.right > zone.left
    assert zone.top <= zone.deep_water_top <= zone.bottom
