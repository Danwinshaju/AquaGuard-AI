import type {
  ApiErrorBody,
  ProcessingJobCreated,
  ProcessingProgressMessage,
  VideoProcessingResponse,
  VideoUploadResponse,
} from "../types/video";

async function readError(response: Response): Promise<string> {
  const fallback = `Request failed (${response.status})`;
  try {
    const body = (await response.json()) as ApiErrorBody;
    return body.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export async function uploadVideo(file: File): Promise<VideoUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/v1/videos/upload", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as VideoUploadResponse;
}

export async function startVideoProcessing(videoId: string): Promise<ProcessingJobCreated> {
  const response = await fetch(`/api/v1/videos/${videoId}/process-background`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as ProcessingJobCreated;
}

export function watchVideoProcessing(
  jobId: string,
  onProgress: (progress: number) => void,
): Promise<VideoProcessingResponse> {
  return new Promise((resolve, reject) => {
    const scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(
      `${scheme}://${window.location.host}/api/v1/videos/ws/processing/${jobId}`,
    );
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data as string) as ProcessingProgressMessage;
      onProgress(message.progress);
      if (message.status === "completed" && message.result) {
        resolve(message.result);
      } else if (message.status === "failed") {
        reject(new Error(message.error ?? "Video analysis failed."));
      }
    };
    socket.onerror = () => reject(new Error("Lost the live progress connection."));
  });
}

export async function acknowledgeIncident(incidentId: string): Promise<void> {
  const response = await fetch(`/api/v1/incidents/${incidentId}/acknowledge`, {
    method: "PATCH",
  });
  if (!response.ok) throw new Error(await readError(response));
}
