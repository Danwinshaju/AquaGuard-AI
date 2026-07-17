export type TrainingState = "queued" | "training" | "completed" | "failed";

export interface ModelStatus {
  model_ready: boolean;
  model_path: string;
  aquatic_model_ready: boolean;
  aquatic_model_path: string;
  sequence_length: number;
  notice: string;
}

export interface TrainingJob {
  id: string;
  status: TrainingState;
  metrics: Record<string, number>;
  output: string[];
  error: string | null;
}

async function expectJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export async function fetchModelStatus(): Promise<ModelStatus> {
  return expectJson(await fetch("/api/v1/model/status"));
}

export async function startModelTraining(file: File, epochs: number): Promise<TrainingJob> {
  const body = new FormData();
  body.append("file", file);
  body.append("epochs", String(epochs));
  return expectJson(
    await fetch("/api/v1/model/train", {
      method: "POST",
      body,
    }),
  );
}

export async function fetchTrainingJob(jobId: string): Promise<TrainingJob> {
  return expectJson(await fetch(`/api/v1/model/jobs/${jobId}`));
}
