"""Stateful YOLO tracking, risk analysis, and evidence for a live camera."""

from collections import deque
from time import monotonic
from uuid import uuid4

import cv2
import numpy as np
from numpy.typing import NDArray

from app.core.config import get_settings
from app.models import IncidentDocument
from app.services.incident_evidence import incident_evidence_service
from app.services.video_processing import video_processing_service
from app.vision.aquatic_behavior import AquaticBehavior, AquaticBehaviorAnalyzer
from app.vision.detectors import Detection, create_person_detector
from app.vision.movement import MovementAnalyzer
from app.vision.pose import PersonPose, YoloPoseAnalyzer
from app.vision.risk import RiskEngine, RiskStatus
from app.vision.temporal import TemporalDrowningClassifier
from app.vision.tracking import CentroidTracker, YoloByteTracker
from app.vision.zones import PoolZone


class LiveMonitoringSession:
    """Retain detection, tracking, pose, and risk state between camera frames."""

    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.byte_tracker: YoloByteTracker | None = None
        if settings.live_use_bytetrack and not settings.mock_ai:
            self.byte_tracker = YoloByteTracker(
                model_name=settings.yolo_model,
                confidence=settings.live_detection_confidence,
                image_size=settings.live_yolo_image_size,
                max_missed_frames=settings.live_tracker_max_missed_frames,
                device=settings.yolo_device or None,
            )
        self.detector = (
            None
            if self.byte_tracker is not None
            else create_person_detector(
                confidence=settings.live_detection_confidence,
                image_size=settings.live_yolo_image_size,
            )
        )
        self.tracker = CentroidTracker(
            max_distance=settings.live_tracker_max_distance_pixels,
            max_missed_frames=settings.live_tracker_max_missed_frames,
        )
        self.movement = MovementAnalyzer(
            settings.live_movement_threshold_pixels,
            settings.live_inactivity_warning_seconds,
        )
        self.risk = RiskEngine(
            inactivity_warning_seconds=settings.live_inactivity_warning_seconds,
            danger_min=settings.live_risk_danger_min,
            danger_persistence_seconds=settings.live_danger_persistence_seconds,
            smoothing_alpha=settings.live_risk_smoothing_alpha,
        )
        self.pose = (
            YoloPoseAnalyzer(
                settings.pose_model,
                settings.live_pose_confidence,
                settings.live_pose_image_size,
                settings.yolo_device or None,
            )
            if settings.pose_enabled
            and (self.byte_tracker is not None or self.detector.mode == "yolo")
            else None
        )
        self.pool_zone = PoolZone()
        self.performance_mode = "balanced"
        self.pose_frame_interval = settings.live_pose_frame_interval
        self.temporal = TemporalDrowningClassifier(
            settings.temporal_model_path,
            settings.temporal_sequence_length,
            settings.yolo_device or None,
        )
        self.aquatic = AquaticBehaviorAnalyzer(
            settings.aquatic_model_path,
            settings.aquatic_model_confidence,
            settings.aquatic_model_image_size,
            settings.yolo_device or None,
            settings.aquatic_model_enabled,
        )
        self.started_at = monotonic()
        self.session_id = f"live-{uuid4()}"
        self.source_name = "Browser live camera"
        self.frame_count = 0
        self.last_detections: list[Detection] = []
        self.latest_poses: dict[int, PersonPose] = {}
        self.latest_aquatic: dict[int, AquaticBehavior] = {}
        self.evidence_frames: deque[NDArray[np.uint8]] = deque(
            maxlen=max(int(settings.incident_clip_seconds * 10), 10)
        )
        self.last_incident_seconds: dict[int, float] = {}
        self.pending_incidents: list[IncidentDocument] = []

    def process_jpeg(self, jpeg_bytes: bytes) -> tuple[dict[str, object], bytes]:
        """Decode one browser frame and return metadata plus annotated JPEG."""

        processing_started = monotonic()
        encoded = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("The live camera frame could not be decoded.")
        self.frame_count += 1
        if self.byte_tracker is not None:
            try:
                all_tracked = self.byte_tracker.update(frame)
                all_missing = self.byte_tracker.missing_people()
            except Exception:
                self.byte_tracker = None
                self.detector = create_person_detector(
                    confidence=self.settings.live_detection_confidence,
                    image_size=self.settings.live_yolo_image_size,
                )
                self.last_detections = self.detector.detect(frame)
                all_tracked = self.tracker.update(self.last_detections)
                all_missing = self.tracker.missing_people()
        else:
            should_detect = (
                self.frame_count == 1
                or self.detector.mode == "mock"
                or self.frame_count % self.settings.live_detection_frame_interval == 0
            )
            if should_detect:
                self.last_detections = self.detector.detect(frame)
            all_tracked = self.tracker.update(self.last_detections)
            all_missing = self.tracker.missing_people()
        height, width = frame.shape[:2]
        tracked = [
            person for person in all_tracked if self.pool_zone.contains(person, width, height)
        ]
        missing = [
            person for person in all_missing if self.pool_zone.contains(person, width, height)
        ]
        people_for_risk = tracked + missing
        if self.pose is not None and self.frame_count % self.pose_frame_interval == 0:
            self.latest_poses = self.pose.analyze(frame, tracked)
        if (
            self.settings.aquatic_model_enabled
            and self.aquatic.enabled
            and self.frame_count % self.settings.aquatic_model_frame_interval == 0
        ):
            self.latest_aquatic = self.aquatic.analyze(frame, tracked)
        timestamp = monotonic() - self.started_at
        movements = self.movement.update(people_for_risk, timestamp)
        temporal_probabilities = self.temporal.update(
            people_for_risk,
            movements,
            self.latest_poses,
        )
        aquatic_probabilities = {
            track_id: behavior.drowning_probability
            for track_id, behavior in self.latest_aquatic.items()
        }
        deep_zone_track_ids = {
            person.track_id for person in people_for_risk if self.pool_zone.is_deep(person, height)
        }
        assessments = self.risk.evaluate(
            people_for_risk,
            movements,
            timestamp,
            poses=self.latest_poses,
            deep_zone_track_ids=deep_zone_track_ids,
            temporal_probabilities=temporal_probabilities,
            aquatic_probabilities=aquatic_probabilities,
        )
        self.pool_zone.draw(frame)
        video_processing_service._draw_poses(frame, self.latest_poses)
        video_processing_service._draw_tracks(frame, tracked, movements, assessments)
        video_processing_service._draw_aquatic_behaviors(
            frame,
            tracked,
            self.latest_aquatic,
        )
        video_processing_service._draw_risk_alert(frame, assessments)
        cv2.rectangle(frame, (0, 0), (310, 42), (15, 23, 42), thickness=-1)
        cv2.putText(
            frame,
            "AquaGuard LIVE - Verify all alerts",
            (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        self.evidence_frames.append(frame.copy())
        effective_fps = min(max(self.frame_count / max(timestamp, 0.001), 1.0), 10.0)
        for track_id, assessment in assessments.items():
            last_incident = self.last_incident_seconds.get(track_id)
            cooldown_finished = (
                last_incident is None
                or timestamp - last_incident >= self.settings.live_incident_cooldown_seconds
            )
            if assessment.status == RiskStatus.DANGER and cooldown_finished:
                incident = incident_evidence_service.create(
                    video_id=self.session_id,
                    source="live_camera",
                    source_name=self.source_name,
                    track_id=track_id,
                    assessment=assessment,
                    timestamp_seconds=timestamp,
                    snapshot_frame=frame,
                    clip_frames=list(self.evidence_frames),
                    clip_fps=effective_fps,
                    storage_root=self.settings.storage_root,
                )
                self.pending_incidents.append(incident)
                self.last_incident_seconds[track_id] = timestamp
        highest = max(assessments.values(), key=lambda item: item.score, default=None)
        status_value = highest.status if highest is not None else RiskStatus.SAFE
        metadata: dict[str, object] = {
            "frame": self.frame_count,
            "people": len(tracked),
            "status": status_value,
            "highest_risk": highest.score if highest is not None else 0.0,
            "danger": status_value == RiskStatus.DANGER,
            "detection_mode": (
                self.byte_tracker.mode if self.byte_tracker is not None else self.detector.mode
            ),
            "effective_fps": round(effective_fps, 1),
            "temporal_model": "active" if self.temporal.enabled else "not-trained",
            "aquatic_model": "active" if self.aquatic.enabled else "not-trained",
            "processing_ms": round((monotonic() - processing_started) * 1000),
            "performance_mode": self.performance_mode,
        }
        success, output = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
        if not success:
            raise RuntimeError("OpenCV could not encode the live result frame.")
        return metadata, output.tobytes()

    def configure_zone(self, values: dict[str, object]) -> None:
        """Apply normalized calibration values supplied by the camera operator."""

        self.pool_zone = PoolZone.from_dict(values)

    def configure_performance(self, mode: str) -> None:
        """Apply a live inference profile without rebuilding or restarting models."""

        profiles = {
            "fast": (416, 12, 320),
            "balanced": (512, 8, 416),
            "accurate": (640, 4, 512),
        }
        if mode not in profiles:
            raise ValueError("Performance mode must be fast, balanced, or accurate.")
        detection_size, pose_interval, pose_size = profiles[mode]
        self.performance_mode = mode
        self.pose_frame_interval = pose_interval
        if self.byte_tracker is not None:
            self.byte_tracker.image_size = detection_size
        if self.detector is not None and hasattr(self.detector, "image_size"):
            self.detector.image_size = detection_size
        if self.pose is not None:
            self.pose.image_size = pose_size
        self.aquatic.image_size = detection_size

    def drain_pending_incidents(self) -> tuple[IncidentDocument, ...]:
        """Return newly created evidence exactly once for database persistence."""

        incidents = tuple(self.pending_incidents)
        self.pending_incidents.clear()
        return incidents
