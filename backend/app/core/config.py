"""Environment-based application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
PROJECT_DIRECTORY = BACKEND_DIRECTORY.parent


class Settings(BaseSettings):
    """Validated settings loaded from ``backend/.env`` when it exists."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AquaGuard AI"
    app_env: str = "development"
    debug: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    frontend_origin: str = "http://localhost:5173"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "aquaguard"
    storage_root: Path = PROJECT_DIRECTORY / "storage"
    max_upload_size_mb: int = Field(default=500, ge=1, le=5000)
    mock_ai: bool = True
    yolo_model: str = "yolo11n.pt"
    detection_confidence: float = Field(default=0.35, ge=0.0, le=1.0)
    detection_frame_interval: int = Field(default=3, ge=1, le=10)
    yolo_image_size: int = Field(default=416, ge=256, le=1280)
    tracker_max_distance_pixels: float = Field(default=120.0, gt=0)
    tracker_max_missed_frames: int = Field(default=15, ge=0, le=300)
    movement_threshold_pixels: float = Field(default=8.0, ge=0)
    inactivity_warning_seconds: float = Field(default=5.0, gt=0)
    risk_safe_max: float = Field(default=40.0, ge=0, le=100)
    risk_danger_min: float = Field(default=70.0, ge=0, le=100)
    danger_persistence_seconds: float = Field(default=3.0, gt=0)
    risk_smoothing_alpha: float = Field(default=0.35, gt=0, le=1)
    risk_inactivity_weight: float = Field(default=80.0, ge=0, le=100)
    sudden_downward_pixels: float = Field(default=20.0, gt=0)
    intense_speed_pixels_per_second: float = Field(default=180.0, gt=0)
    low_speed_pixels_per_second: float = Field(default=15.0, ge=0)
    incident_clip_seconds: float = Field(default=3.0, gt=0, le=15)
    incident_clip_fps: float = Field(default=5.0, gt=0, le=30)
    pose_enabled: bool = True
    pose_model: str = "yolo11n-pose.pt"
    pose_frame_interval: int = Field(default=6, ge=1, le=30)
    pose_confidence: float = Field(default=0.35, ge=0, le=1)
    pose_image_size: int = Field(default=416, ge=256, le=1280)
    live_detection_confidence: float = Field(default=0.25, ge=0.05, le=1)
    live_yolo_image_size: int = Field(default=512, ge=256, le=1280)
    live_detection_frame_interval: int = Field(default=1, ge=1, le=5)
    live_tracker_max_distance_pixels: float = Field(default=160.0, gt=0)
    live_tracker_max_missed_frames: int = Field(default=24, ge=1, le=300)
    live_movement_threshold_pixels: float = Field(default=5.0, ge=0)
    live_inactivity_warning_seconds: float = Field(default=3.0, gt=0)
    live_risk_danger_min: float = Field(default=60.0, ge=0, le=100)
    live_danger_persistence_seconds: float = Field(default=1.5, gt=0)
    live_risk_smoothing_alpha: float = Field(default=0.55, gt=0, le=1)
    live_pose_frame_interval: int = Field(default=8, ge=1, le=30)
    live_pose_confidence: float = Field(default=0.25, ge=0, le=1)
    live_pose_image_size: int = Field(default=416, ge=256, le=1280)
    live_incident_cooldown_seconds: float = Field(default=30.0, gt=0, le=600)
    live_use_bytetrack: bool = True
    yolo_device: str = ""
    temporal_model_path: Path = BACKEND_DIRECTORY / "models" / "drowning_temporal.ts"
    temporal_sequence_length: int = Field(default=16, ge=4, le=300)
    temporal_alert_threshold: float = Field(default=0.65, ge=0, le=1)
    temporal_risk_weight: float = Field(default=45.0, ge=0, le=100)
    aquatic_model_enabled: bool = True
    aquatic_model_path: Path = BACKEND_DIRECTORY / "models" / "aquaguard_aquatic_best.pt"
    aquatic_model_confidence: float = Field(default=0.25, ge=0.05, le=1)
    aquatic_model_image_size: int = Field(default=416, ge=256, le=1280)
    aquatic_model_frame_interval: int = Field(default=6, ge=1, le=30)
    aquatic_model_alert_threshold: float = Field(default=0.60, ge=0, le=1)
    aquatic_model_risk_weight: float = Field(default=55.0, ge=0, le=100)
    alert_webhook_url: str = ""
    alert_email_to: str = ""
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    alert_escalation_seconds: float = Field(default=60.0, ge=10, le=3600)
    incident_retention_hours: float = Field(default=24.0, gt=0, le=8760)
    incident_cleanup_interval_seconds: float = Field(default=300.0, ge=60, le=86400)


@lru_cache
def get_settings() -> Settings:
    """Create settings once and reuse them for the lifetime of the process."""

    return Settings()
