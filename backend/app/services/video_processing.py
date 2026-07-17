"""OpenCV video pipeline through Stage 9 incident evidence generation."""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import cv2
import numpy as np
from fastapi import HTTPException, status
from numpy.typing import NDArray

from app.core.config import get_settings
from app.models import IncidentDocument
from app.services.incident_evidence import incident_evidence_service
from app.services.media_encoding import media_encoding_service
from app.vision.aquatic_behavior import AquaticBehavior, AquaticBehaviorAnalyzer
from app.vision.detectors import create_person_detector
from app.vision.detectors.base import Detection
from app.vision.movement import MovementAnalyzer, MovementMetrics
from app.vision.pose import PersonPose, YoloPoseAnalyzer
from app.vision.risk import RiskAssessment, RiskEngine, RiskStatus
from app.vision.temporal import TemporalDrowningClassifier
from app.vision.tracking import CentroidTracker, TrackedPerson


@dataclass(frozen=True)
class ProcessedVideo:
    """Metadata calculated while producing an output video."""

    id: str
    processed_filename: str
    frame_count: int
    width: int
    height: int
    fps: float
    duration_seconds: float
    detection_mode: str
    total_person_detections: int
    frames_with_people: int
    unique_people_tracked: int
    maximum_inactivity_seconds: float
    maximum_risk_score: float
    danger_frame_count: int
    pose_mode: str
    pose_frames_analyzed: int
    incidents: tuple[IncidentDocument, ...]
    path: Path


class VideoProcessingService:
    """Decode an uploaded video, annotate its frames, and encode an MP4."""

    def process(
        self,
        video_id: str,
        progress_callback: Callable[[float], None] | None = None,
    ) -> ProcessedVideo:
        """Process one stored upload synchronously.

        A later stage will run this work as a background job and report progress.
        """

        safe_id = self._validate_video_id(video_id)
        input_path = self._find_upload(safe_id)
        settings = get_settings()
        output_directory = settings.storage_root / "processed"
        output_directory.mkdir(parents=True, exist_ok=True)
        output_path = output_directory / f"{safe_id}.mp4"
        opencv_path = output_directory / f"{safe_id}.opencv.mp4"
        temporary_path = output_directory / f"{safe_id}.part.mp4"

        capture = cv2.VideoCapture(str(input_path))
        if not capture.isOpened():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "OpenCV could not open this video. It may be corrupt or use an "
                    "unsupported codec."
                ),
            )

        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        expected_frame_count = max(int(capture.get(cv2.CAP_PROP_FRAME_COUNT)), 1)
        if width <= 0 or height <= 0 or fps <= 0:
            capture.release()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The video has invalid width, height, or frame-rate metadata.",
            )

        writer = cv2.VideoWriter(
            str(opencv_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            capture.release()
            opencv_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenCV could not create the processed video.",
            )

        frame_count = 0
        total_person_detections = 0
        frames_with_people = 0
        detector = create_person_detector()
        last_detections: list[Detection] = []
        tracker = CentroidTracker(
            max_distance=settings.tracker_max_distance_pixels,
            max_missed_frames=max(
                settings.tracker_max_missed_frames,
                int(fps * (settings.danger_persistence_seconds + 2.0)),
            ),
        )
        movement_analyzer = MovementAnalyzer(
            movement_threshold=settings.movement_threshold_pixels,
            inactivity_threshold=settings.inactivity_warning_seconds,
        )
        risk_engine = RiskEngine()
        temporal_classifier = TemporalDrowningClassifier(
            settings.temporal_model_path,
            settings.temporal_sequence_length,
            settings.yolo_device or None,
        )
        aquatic_analyzer = AquaticBehaviorAnalyzer(
            settings.aquatic_model_path,
            settings.aquatic_model_confidence,
            settings.aquatic_model_image_size,
            settings.yolo_device or None,
            settings.aquatic_model_enabled,
        )
        pose_analyzer = (
            YoloPoseAnalyzer(
                settings.pose_model,
                settings.pose_confidence,
                settings.pose_image_size,
                settings.yolo_device or None,
            )
            if settings.pose_enabled and detector.mode == "yolo"
            else None
        )
        latest_poses: dict[int, PersonPose] = {}
        latest_aquatic: dict[int, AquaticBehavior] = {}
        pose_frames_analyzed = 0
        evidence_frames: deque[NDArray[np.uint8]] = deque(
            maxlen=max(int(settings.incident_clip_seconds * settings.incident_clip_fps), 1)
        )
        evidence_sample_interval = max(round(fps / settings.incident_clip_fps), 1)
        incident_track_ids: set[int] = set()
        incidents: list[IncidentDocument] = []
        try:
            while True:
                success, frame = capture.read()
                if not success:
                    break
                frame_count += 1
                should_run_detection = (
                    frame_count == 1
                    or detector.mode == "mock"
                    or frame_count % settings.detection_frame_interval == 0
                )
                if should_run_detection:
                    last_detections = detector.detect(frame)
                detections = last_detections
                total_person_detections += len(detections)
                if detections:
                    frames_with_people += 1
                tracked_people = tracker.update(detections)
                missing_people = tracker.missing_people()
                people_for_risk = tracked_people + missing_people
                if pose_analyzer is not None and (
                    frame_count == 1 or frame_count % settings.pose_frame_interval == 0
                ):
                    latest_poses = pose_analyzer.analyze(frame, tracked_people)
                    pose_frames_analyzed += 1
                if (
                    settings.aquatic_model_enabled
                    and aquatic_analyzer.enabled
                    and (
                        frame_count == 1
                        or frame_count % settings.aquatic_model_frame_interval == 0
                    )
                ):
                    latest_aquatic = aquatic_analyzer.analyze(frame, tracked_people)
                timestamp_seconds = (frame_count - 1) / fps
                movement_metrics = movement_analyzer.update(
                    people_for_risk,
                    timestamp_seconds,
                )
                temporal_probabilities = temporal_classifier.update(
                    people_for_risk,
                    movement_metrics,
                    latest_poses,
                )
                aquatic_probabilities = {
                    track_id: behavior.drowning_probability
                    for track_id, behavior in latest_aquatic.items()
                }
                risk_assessments = risk_engine.evaluate(
                    people_for_risk,
                    movement_metrics,
                    timestamp_seconds,
                    latest_poses,
                    temporal_probabilities=temporal_probabilities,
                    aquatic_probabilities=aquatic_probabilities,
                )
                self._draw_poses(frame, latest_poses)
                self._draw_tracks(
                    frame,
                    tracked_people,
                    movement_metrics,
                    risk_assessments,
                )
                self._draw_aquatic_behaviors(frame, tracked_people, latest_aquatic)
                self._draw_stage_four_overlay(frame, frame_count)
                self._draw_risk_alert(frame, risk_assessments)
                if frame_count % evidence_sample_interval == 0:
                    evidence_frames.append(frame.copy())
                for tracked_person in people_for_risk:
                    assessment = risk_assessments[tracked_person.track_id]
                    if (
                        assessment.status is RiskStatus.DANGER
                        and tracked_person.track_id not in incident_track_ids
                    ):
                        clip_frames = list(evidence_frames)
                        if not clip_frames or frame_count % evidence_sample_interval != 0:
                            clip_frames.append(frame.copy())
                        incident = incident_evidence_service.create(
                            video_id=safe_id,
                            track_id=tracked_person.track_id,
                            assessment=assessment,
                            timestamp_seconds=timestamp_seconds,
                            snapshot_frame=frame,
                            clip_frames=clip_frames,
                            clip_fps=settings.incident_clip_fps,
                            storage_root=settings.storage_root,
                        )
                        incidents.append(incident)
                        incident_track_ids.add(tracked_person.track_id)
                writer.write(frame)
                if progress_callback is not None:
                    progress_callback(min((frame_count / expected_frame_count) * 95.0, 95.0))
        except Exception:
            temporary_path.unlink(missing_ok=True)
            opencv_path.unlink(missing_ok=True)
            raise
        finally:
            capture.release()
            writer.release()

        if frame_count == 0:
            temporary_path.unlink(missing_ok=True)
            opencv_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="OpenCV did not find any readable frames in this video.",
            )

        try:
            if progress_callback is not None:
                progress_callback(97.0)
            media_encoding_service.convert_to_browser_mp4(opencv_path, temporary_path)
            output_path.unlink(missing_ok=True)
            temporary_path.replace(output_path)
        finally:
            opencv_path.unlink(missing_ok=True)
            temporary_path.unlink(missing_ok=True)
        if progress_callback is not None:
            progress_callback(100.0)
        return ProcessedVideo(
            id=safe_id,
            processed_filename=output_path.name,
            frame_count=frame_count,
            width=width,
            height=height,
            fps=round(fps, 3),
            duration_seconds=round(frame_count / fps, 3),
            detection_mode=detector.mode,
            total_person_detections=total_person_detections,
            frames_with_people=frames_with_people,
            unique_people_tracked=len(tracker.created_track_ids),
            maximum_inactivity_seconds=round(
                movement_analyzer.maximum_inactivity_seconds,
                3,
            ),
            maximum_risk_score=risk_engine.maximum_score,
            danger_frame_count=risk_engine.danger_frame_count,
            pose_mode="yolo" if pose_analyzer is not None else "disabled",
            pose_frames_analyzed=pose_frames_analyzed,
            incidents=tuple(incidents),
            path=output_path,
        )

    def get_processed_path(self, video_id: str) -> Path:
        """Resolve an output path safely and report a friendly 404 when absent."""

        safe_id = self._validate_video_id(video_id)
        path = get_settings().storage_root / "processed" / f"{safe_id}.mp4"
        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processed video was not found. Process the upload first.",
            )
        return path

    def find_upload(self, video_id: str) -> Path:
        """Validate an external ID and return its uploaded file path."""

        return self._find_upload(self._validate_video_id(video_id))

    @staticmethod
    def _validate_video_id(video_id: str) -> str:
        try:
            return str(UUID(video_id))
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video ID must be a valid UUID.",
            ) from error

    @staticmethod
    def _find_upload(video_id: str) -> Path:
        upload_directory = get_settings().storage_root / "uploads"
        matches = [
            path
            for extension in (".mp4", ".avi", ".mov")
            if (path := upload_directory / f"{video_id}{extension}").is_file()
        ]
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded video was not found.",
            )
        return matches[0]

    @staticmethod
    def _draw_stage_four_overlay(frame: object, frame_number: int) -> None:
        """Draw visible proof that every frame passed through the pipeline."""

        cv2.rectangle(frame, (0, 0), (640, 72), (15, 23, 42), thickness=-1)
        cv2.putText(
            frame,
            "AquaGuard AI - Educational Preview",
            (14, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Frame {frame_number} | Not a replacement for lifeguards",
            (14, 56),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (80, 210, 255),
            1,
            cv2.LINE_AA,
        )

    @staticmethod
    def _draw_tracks(
        frame: object,
        tracked_people: list[TrackedPerson],
        movement_metrics: dict[int, MovementMetrics],
        risk_assessments: dict[int, RiskAssessment],
    ) -> None:
        """Draw persistent ID plus movement and inactivity measurements."""

        for tracked_person in tracked_people:
            detection = tracked_person.detection
            metrics = movement_metrics[tracked_person.track_id]
            assessment = risk_assessments[tracked_person.track_id]
            colors = {
                RiskStatus.SAFE: (60, 179, 113),
                RiskStatus.WARNING: (0, 165, 255),
                RiskStatus.DANGER: (45, 45, 220),
            }
            box_color = colors[assessment.status]
            cv2.rectangle(
                frame,
                (detection.x1, detection.y1),
                (detection.x2, detection.y2),
                box_color,
                thickness=2,
            )
            label = (
                f"ID {tracked_person.track_id} | {assessment.status} | "
                f"RISK {assessment.score:.0f} | {detection.confidence:.0%}"
            )
            label_y = max(detection.y1 - 8, 82)
            cv2.putText(
                frame,
                label,
                (detection.x1, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                box_color,
                2,
                cv2.LINE_AA,
            )
            movement_label = (
                f"Move {metrics.displacement_pixels:.1f}px | "
                f"Inactive {metrics.inactivity_seconds:.1f}s"
            )
            cv2.putText(
                frame,
                movement_label,
                (detection.x1, min(detection.y2 + 20, frame.shape[0] - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                box_color,
                2,
                cv2.LINE_AA,
            )

    @staticmethod
    def _draw_risk_alert(
        frame: object,
        assessments: dict[int, RiskAssessment],
    ) -> None:
        """Draw an unmistakable frame-level warning for verified danger."""

        dangers = [
            assessment
            for assessment in assessments.values()
            if assessment.status is RiskStatus.DANGER
        ]
        if not dangers:
            return
        most_urgent = max(dangers, key=lambda assessment: assessment.score)
        height, width = frame.shape[:2]
        banner_top = max(height - 92, 0)
        cv2.rectangle(frame, (0, banner_top), (width, height), (20, 20, 210), thickness=-1)
        cv2.putText(
            frame,
            "POSSIBLE DROWNING - VERIFY NOW",
            (18, banner_top + 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            min(max(width / 900, 0.65), 1.15),
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"PERSON ID {most_urgent.track_id} | RISK {most_urgent.score:.0f} | ALERT LIFEGUARD",
            (18, banner_top + 72),
            cv2.FONT_HERSHEY_SIMPLEX,
            min(max(width / 1300, 0.46), 0.78),
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    @staticmethod
    def _draw_aquatic_behaviors(
        frame: object,
        tracked_people: list[TrackedPerson],
        behaviors: dict[int, AquaticBehavior],
    ) -> None:
        """Show the latest custom dataset label associated with each person."""

        for person in tracked_people:
            behavior = behaviors.get(person.track_id)
            if behavior is None:
                continue
            detection = person.detection
            is_drowning = behavior.label.strip().lower() == "drowning"
            color = (30, 30, 230) if is_drowning else (220, 180, 40)
            label = f"AQUATIC: {behavior.label.upper()} {behavior.confidence:.0%}"
            cv2.putText(
                frame,
                label,
                (detection.x1, max(detection.y1 - 31, 18)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
                cv2.LINE_AA,
            )

    @staticmethod
    def _draw_poses(frame: object, poses: dict[int, PersonPose]) -> None:
        """Draw visible head, arm, shoulder, and hip landmarks."""

        skeleton_edges = ((5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12))
        for pose in poses.values():
            for start_index, end_index in skeleton_edges:
                start = pose.keypoints.get(start_index)
                end = pose.keypoints.get(end_index)
                if start and end and start[2] >= 0.35 and end[2] >= 0.35:
                    cv2.line(frame, start[:2], end[:2], (255, 210, 60), 2, cv2.LINE_AA)
            for x, y, confidence in pose.keypoints.values():
                if confidence >= 0.35:
                    cv2.circle(frame, (x, y), 3, (255, 255, 255), thickness=-1)


video_processing_service = VideoProcessingService()
