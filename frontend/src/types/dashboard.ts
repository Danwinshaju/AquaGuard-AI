export interface DailyAlertPoint {
  date: string;
  alerts: number;
}

export interface DashboardSummary {
  active_cameras: number;
  people_detected: number;
  warning_count: number;
  critical_alert_count: number;
  unresolved_incidents: number;
  average_acknowledgement_seconds: number;
  false_positive_rate: number;
  alerts_by_day: DailyAlertPoint[];
}

export interface IncidentListItem {
  id: string;
  video_id: string;
  source: "uploaded_video" | "live_camera";
  source_name: string | null;
  track_id: number;
  severity: string;
  status: "unresolved" | "acknowledged" | "resolved" | "false_alarm";
  risk_score: number;
  occurred_at_seconds: number;
  triggered_signals: string[];
  snapshot_url: string;
  clip_url: string;
  created_at: string;
  notes: string;
}

export interface SystemHealth {
  status: "ok" | "degraded";
  mongodb: boolean;
  cuda_available: boolean;
  gpu_name: string | null;
  configured_device: string;
  temporal_model_ready: boolean;
  online_cameras: number;
  total_cameras: number;
  storage_free_gb: number;
}
