"""Beginner-friendly centroid-based multi-person tracker."""

from dataclasses import dataclass
from math import hypot

from app.vision.detectors import Detection


@dataclass(frozen=True)
class TrackedPerson:
    """A current detection associated with a persistent tracking ID."""

    track_id: int
    detection: Detection
    missing_frames: int = 0

    @property
    def center(self) -> tuple[float, float]:
        """Return the centre point of the person's bounding box."""

        return (
            (self.detection.x1 + self.detection.x2) / 2,
            (self.detection.y1 + self.detection.y2) / 2,
        )


@dataclass
class _TrackState:
    """Internal mutable history retained between video frames."""

    center: tuple[float, float]
    detection: Detection
    missed_frames: int = 0
    hits: int = 1


class CentroidTracker:
    """Match detections to existing tracks using centre-point distance.

    This lightweight MVP tracker works well when motion between adjacent frames is
    limited. A later production version can replace it with ByteTrack or BoT-SORT
    without changing the rest of the video pipeline.
    """

    def __init__(self, max_distance: float, max_missed_frames: int) -> None:
        self.max_distance = max_distance
        self.max_missed_frames = max_missed_frames
        self._next_track_id = 1
        self._tracks: dict[int, _TrackState] = {}
        self.created_track_ids: set[int] = set()

    def update(self, detections: list[Detection]) -> list[TrackedPerson]:
        """Associate this frame's detections and return visible tracked people."""

        detection_centers = [self._center(detection) for detection in detections]
        candidates = sorted(
            (
                (self._distance(state.center, center), track_id, detection_index)
                for track_id, state in self._tracks.items()
                for detection_index, center in enumerate(detection_centers)
            ),
            key=lambda candidate: candidate[0],
        )

        matched_tracks: set[int] = set()
        matched_detections: set[int] = set()
        assigned_ids: dict[int, int] = {}

        for distance, track_id, detection_index in candidates:
            if distance > self.max_distance:
                break
            if track_id in matched_tracks or detection_index in matched_detections:
                continue
            matched_tracks.add(track_id)
            matched_detections.add(detection_index)
            assigned_ids[detection_index] = track_id
            state = self._tracks[track_id]
            state.center = detection_centers[detection_index]
            state.detection = detections[detection_index]
            state.missed_frames = 0
            state.hits += 1

        for detection_index in range(len(detections)):
            if detection_index in matched_detections:
                continue
            track_id = self._next_track_id
            self._next_track_id += 1
            self._tracks[track_id] = _TrackState(
                center=detection_centers[detection_index],
                detection=detections[detection_index],
            )
            self.created_track_ids.add(track_id)
            assigned_ids[detection_index] = track_id
            matched_tracks.add(track_id)

        for track_id in list(self._tracks):
            if track_id in matched_tracks:
                continue
            state = self._tracks[track_id]
            state.missed_frames += 1
            if state.missed_frames > self.max_missed_frames:
                del self._tracks[track_id]

        return [
            TrackedPerson(track_id=assigned_ids[index], detection=detection)
            for index, detection in enumerate(detections)
        ]

    def missing_people(self, minimum_hits: int = 5) -> list[TrackedPerson]:
        """Return established tracks currently absent from the frame."""

        return [
            TrackedPerson(
                track_id=track_id,
                detection=state.detection,
                missing_frames=state.missed_frames,
            )
            for track_id, state in self._tracks.items()
            if state.missed_frames > 0 and state.hits >= minimum_hits
        ]

    @staticmethod
    def _center(detection: Detection) -> tuple[float, float]:
        return (
            (detection.x1 + detection.x2) / 2,
            (detection.y1 + detection.y2) / 2,
        )

    @staticmethod
    def _distance(first: tuple[float, float], second: tuple[float, float]) -> float:
        return hypot(first[0] - second[0], first[1] - second[1])
