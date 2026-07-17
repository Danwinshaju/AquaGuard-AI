import type { CameraStatus } from "../types/camera";

async function expectJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Camera request failed." }));
    throw new Error(body.detail ?? `Camera request failed (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export async function fetchCameras(): Promise<CameraStatus[]> {
  return expectJson(await fetch("/api/v1/cameras"));
}

export async function addCamera(name: string, sourceUrl: string): Promise<CameraStatus> {
  return expectJson(await fetch("/api/v1/cameras", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, source_url: sourceUrl }),
  }));
}

export async function deleteCamera(cameraId: string): Promise<void> {
  const response = await fetch(`/api/v1/cameras/${cameraId}`, { method: "DELETE" });
  if (!response.ok) throw new Error(`Camera deletion failed (${response.status}).`);
}
