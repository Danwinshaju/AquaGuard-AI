export interface CameraStatus {
  id: string;
  name: string;
  status: "starting" | "online" | "reconnecting" | "stopped" | "error";
  people: number;
  highest_risk: number;
  last_frame_at: string | null;
  reconnect_count: number;
  error: string | null;
  stream_url: string;
}
