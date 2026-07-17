import type { DashboardSummary, IncidentListItem, SystemHealth } from "../types/dashboard";

async function expectJson<T>(response: Response): Promise<T> {
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return (await response.json()) as T;
}

export async function fetchDashboard(): Promise<DashboardSummary> {
  return expectJson(await fetch("/api/v1/dashboard/summary"));
}

export async function fetchSystemHealth(): Promise<SystemHealth> {
  return expectJson(await fetch("/api/v1/health/system"));
}

export interface IncidentFilters {
  search?: string;
  status?: string;
  source?: string;
  minimumRisk?: number;
  createdAfter?: string;
  createdBefore?: string;
}

export async function fetchIncidents(filters: IncidentFilters = {}): Promise<IncidentListItem[]> {
  const parameters = new URLSearchParams();
  if (filters.search) parameters.set("search", filters.search);
  if (filters.status) parameters.set("status", filters.status);
  if (filters.source) parameters.set("source", filters.source);
  if (filters.minimumRisk) parameters.set("minimum_risk", String(filters.minimumRisk));
  if (filters.createdAfter) parameters.set("created_after", filters.createdAfter);
  if (filters.createdBefore) parameters.set("created_before", filters.createdBefore);
  const query = parameters.toString();
  return expectJson(await fetch(`/api/v1/incidents${query ? `?${query}` : ""}`));
}

export async function updateIncident(
  incidentId: string,
  action: "acknowledge" | "resolve" | "false-alarm",
): Promise<void> {
  await expectJson(
    await fetch(`/api/v1/incidents/${incidentId}/${action}`, { method: "PATCH" }),
  );
}

export async function deleteIncident(incidentId: string): Promise<void> {
  const response = await fetch(`/api/v1/incidents/${incidentId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error(`Delete failed (${response.status})`);
}

export async function deleteAllIncidents(): Promise<void> {
  const response = await fetch("/api/v1/incidents", { method: "DELETE" });
  if (!response.ok) throw new Error(`Delete all failed (${response.status})`);
}

export async function updateIncidentNotes(incidentId: string, notes: string): Promise<void> {
  const response = await fetch(`/api/v1/incidents/${incidentId}/notes`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notes }),
  });
  if (!response.ok) throw new Error(`Saving notes failed (${response.status})`);
}
