"""Unit tests for per-person movement and inactivity calculations."""

import pytest

from app.vision.detectors import Detection
from app.vision.movement import MovementAnalyzer
from app.vision.tracking import TrackedPerson


def tracked_person(track_id: int, center_x: int, center_y: int) -> TrackedPerson:
    return TrackedPerson(
        track_id=track_id,
        detection=Detection(
            x1=center_x - 10,
            y1=center_y - 20,
            x2=center_x + 10,
            y2=center_y + 20,
            confidence=0.9,
        ),
    )


def test_calculates_displacement_speed_and_distance() -> None:
    analyzer = MovementAnalyzer(movement_threshold=2, inactivity_threshold=5)

    analyzer.update([tracked_person(1, 10, 10)], timestamp_seconds=0)
    metrics = analyzer.update([tracked_person(1, 13, 14)], timestamp_seconds=0.5)[1]

    assert metrics.displacement_pixels == 5
    assert metrics.speed_pixels_per_second == 10
    assert metrics.total_distance_pixels == 5
    assert metrics.inactivity_seconds == 0


def test_marks_person_inactive_after_threshold() -> None:
    analyzer = MovementAnalyzer(movement_threshold=5, inactivity_threshold=3)

    analyzer.update([tracked_person(1, 10, 10)], timestamp_seconds=0)
    metrics = analyzer.update([tracked_person(1, 11, 10)], timestamp_seconds=3)[1]

    assert metrics.inactivity_seconds == 3
    assert metrics.is_inactive is True


def test_significant_movement_resets_inactivity_timer() -> None:
    analyzer = MovementAnalyzer(movement_threshold=5, inactivity_threshold=3)

    analyzer.update([tracked_person(1, 10, 10)], timestamp_seconds=0)
    analyzer.update([tracked_person(1, 10, 10)], timestamp_seconds=2)
    metrics = analyzer.update([tracked_person(1, 20, 10)], timestamp_seconds=2.5)[1]

    assert metrics.inactivity_seconds == 0
    assert metrics.is_inactive is False


def test_keeps_inactivity_independent_for_each_person() -> None:
    analyzer = MovementAnalyzer(movement_threshold=5, inactivity_threshold=3)

    analyzer.update(
        [tracked_person(1, 10, 10), tracked_person(2, 100, 10)],
        timestamp_seconds=0,
    )
    metrics = analyzer.update(
        [tracked_person(1, 10, 10), tracked_person(2, 120, 10)],
        timestamp_seconds=4,
    )

    assert metrics[1].is_inactive is True
    assert metrics[1].inactivity_seconds == 4
    assert metrics[2].is_inactive is False
    assert metrics[2].inactivity_seconds == 0


def test_records_maximum_inactivity_seen() -> None:
    analyzer = MovementAnalyzer(movement_threshold=5, inactivity_threshold=3)

    analyzer.update([tracked_person(1, 10, 10)], timestamp_seconds=0)
    analyzer.update([tracked_person(1, 10, 10)], timestamp_seconds=4.25)

    assert analyzer.maximum_inactivity_seconds == pytest.approx(4.25)
