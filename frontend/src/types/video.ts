export interface VideoUploadResponse {
  id: string;
  original_filename: string;
  stored_filename: string;
  content_type: string;
  size_bytes: number;
  status: "uploaded";
  safety_notice: string;
}

export interface VideoProcessingResponse {
  id: string;
  status: "completed";
  processed_filename: string;
  frame_count: number;
  width: number;
  height: number;
  fps: number;
  duration_seconds: number;
  detection_mode: "mock" | "yolo";
  total_person_detections: number;
  frames_with_people: number;
  unique_people_tracked: number;
  maximum_inactivity_seconds: number;
  maximum_risk_score: number;
  danger_frame_count: number;
  pose_mode: "disabled" | "yolo";
  pose_frames_analyzed: number;
  incident_count: number;
  incidents: IncidentSummary[];
  download_url: string;
}

export interface IncidentSummary {
  id: string;
  track_id: number;
  risk_score: number;
  occurred_at_seconds: number;
  status: string;
  snapshot_url: string;
  clip_url: string;
}

export interface ApiErrorBody {
  detail?: string;
}

export interface ProcessingJobCreated {
  job_id: string;
  video_id: string;
  status: "queued" | "processing";
}

export interface ProcessingProgressMessage {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  error: string | null;
  result: VideoProcessingResponse | null;
}
