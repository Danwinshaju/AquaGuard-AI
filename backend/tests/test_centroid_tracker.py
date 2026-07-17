"""Unit tests for persistent Stage 6 tracking IDs."""

from app.vision.detectors import Detection
from app.vision.tracking import CentroidTracker


def person_box(x: int, y: int) -> Detection:
    return Detection(x1=x, y1=y, x2=x + 40, y2=y + 80, confidence=0.9)


def test_keeps_id_for_nearby_person_across_frames() -> None:
    tracker = CentroidTracker(max_distance=50, max_missed_frames=2)

    first = tracker.update([person_box(10, 20)])
    second = tracker.update([person_box(18, 25)])

    assert first[0].track_id == 1
    assert second[0].track_id == 1
    assert tracker.created_track_ids == {1}


def test_assigns_separate_ids_to_two_people() -> None:
    tracker = CentroidTracker(max_distance=50, max_missed_frames=2)

    tracked = tracker.update([person_box(10, 20), person_box(300, 20)])

    assert [person.track_id for person in tracked] == [1, 2]


def test_retains_track_during_short_disappearance() -> None:
    tracker = CentroidTracker(max_distance=50, max_missed_frames=2)

    tracker.update([person_box(10, 20)])
    tracker.update([])
    tracker.update([])
    returned = tracker.update([person_box(15, 20)])

    assert returned[0].track_id == 1


def test_creates_new_id_after_track_expires() -> None:
    tracker = CentroidTracker(max_distance=50, max_missed_frames=1)

    tracker.update([person_box(10, 20)])
    tracker.update([])
    tracker.update([])
    returned = tracker.update([person_box(10, 20)])

    assert returned[0].track_id == 2
    assert tracker.created_track_ids == {1, 2}


def test_far_detection_gets_new_id() -> None:
    tracker = CentroidTracker(max_distance=50, max_missed_frames=2)

    tracker.update([person_box(10, 20)])
    returned = tracker.update([person_box(500, 20)])

    assert returned[0].track_id == 2


def test_reports_established_person_while_temporarily_missing() -> None:
    tracker = CentroidTracker(max_distance=50, max_missed_frames=10)

    for _ in range(5):
        tracker.update([person_box(10, 20)])
    tracker.update([])

    missing = tracker.missing_people()
    assert len(missing) == 1
    assert missing[0].track_id == 1
    assert missing[0].missing_frames == 1
