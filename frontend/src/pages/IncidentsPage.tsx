import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Download, Printer, ShieldAlert, Trash2, XCircle } from "lucide-react";
import { useState } from "react";
import { deleteAllIncidents, deleteIncident, fetchIncidents, updateIncident, updateIncidentNotes } from "../api/dashboard";
import { AppShell } from "../components/AppShell";
import type { IncidentListItem } from "../types/dashboard";

export function IncidentsPage() {
  const queryClient = useQueryClient();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [minimumRisk, setMinimumRisk] = useState(0);
  const [createdAfter, setCreatedAfter] = useState("");
  const [createdBefore, setCreatedBefore] = useState("");
  const filters = {
    search,
    status: statusFilter,
    source: sourceFilter,
    minimumRisk,
    createdAfter: createdAfter ? new Date(`${createdAfter}T00:00:00`).toISOString() : "",
    createdBefore: createdBefore ? new Date(`${createdBefore}T23:59:59`).toISOString() : "",
  };
  const { data = [], isLoading } = useQuery({ queryKey: ["incidents", filters], queryFn: () => fetchIncidents(filters) });
  const action = useMutation({
    mutationFn: ({ id, name }: { id: string; name: "acknowledge" | "resolve" | "false-alarm" | "delete" }) => name === "delete" ? deleteIncident(id) : updateIncident(id, name),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["incidents"] }); },
  });
  const bulkDelete = useMutation({
    mutationFn: async (mode: "selected" | "all") => {
      if (mode === "all") await deleteAllIncidents();
      else await Promise.all([...selectedIds].map(deleteIncident));
    },
    onSuccess: async () => {
      setSelectedIds(new Set());
      await queryClient.invalidateQueries({ queryKey: ["incidents"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  return (
    <AppShell>
      <h1 className="text-3xl font-black">Incidents</h1>
      <p className="mt-2 text-slate-500">Review evidence and record the outcome of every alert.</p>
      <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-950">Privacy protection: every incident report, screenshot and evidence clip is permanently deleted 24 hours after it is created.</div>
      <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-4 print:hidden"><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"><input className="rounded-xl border border-slate-300 px-3 py-2" placeholder="Search camera or video" value={search} onChange={(event) => setSearch(event.target.value)} /><select className="rounded-xl border border-slate-300 px-3 py-2" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="">All statuses</option><option value="unresolved">Unresolved</option><option value="acknowledged">Acknowledged</option><option value="resolved">Resolved</option><option value="false_alarm">False alarm</option></select><select className="rounded-xl border border-slate-300 px-3 py-2" value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}><option value="">All sources</option><option value="live_camera">Live camera</option><option value="uploaded_video">Uploaded video</option></select><label className="text-xs font-bold text-slate-600">Minimum risk: {minimumRisk}<input className="mt-2 w-full accent-red-700" type="range" min="0" max="100" step="5" value={minimumRisk} onChange={(event) => setMinimumRisk(Number(event.target.value))} /></label><label className="text-xs font-bold text-slate-600">From date<input className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" type="date" value={createdAfter} onChange={(event) => setCreatedAfter(event.target.value)} /></label><label className="text-xs font-bold text-slate-600">To date<input className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" type="date" value={createdBefore} onChange={(event) => setCreatedBefore(event.target.value)} /></label></div><div className="mt-4 flex flex-wrap gap-3"><a className="flex items-center gap-2 rounded-xl bg-emerald-700 px-4 py-2 font-black text-white" href="/api/v1/incidents/export.csv"><Download size={18} /> Export CSV</a><button className="flex items-center gap-2 rounded-xl bg-slate-800 px-4 py-2 font-black text-white" onClick={() => window.print()}><Printer size={18} /> Print / Save PDF</button><button className="rounded-xl bg-slate-100 px-4 py-2 font-bold" onClick={() => { setSearch(""); setStatusFilter(""); setSourceFilter(""); setMinimumRisk(0); setCreatedAfter(""); setCreatedBefore(""); }}>Clear filters</button></div></section>
      {data.length > 0 && <div className="mt-5 flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4">
        <button className="rounded-xl bg-slate-100 px-4 py-2 font-bold text-slate-800" onClick={() => setSelectedIds(selectedIds.size === data.length ? new Set() : new Set(data.map((incident) => incident.id)))}>{selectedIds.size === data.length ? "Clear selection" : "Select all"}</button>
        <span className="text-sm font-semibold text-slate-500">{selectedIds.size} selected</span>
        <button className="rounded-xl bg-red-600 px-4 py-2 font-black text-white disabled:bg-slate-300" disabled={selectedIds.size === 0 || bulkDelete.isPending} onClick={() => { if (window.confirm(`Permanently delete ${selectedIds.size} selected incident(s) and all their evidence?`)) bulkDelete.mutate("selected"); }}>Delete selected</button>
        <button className="ml-auto rounded-xl bg-red-900 px-4 py-2 font-black text-white disabled:bg-slate-300" disabled={bulkDelete.isPending} onClick={() => { if (window.confirm("Permanently delete ALL incident reports, screenshots and evidence videos? This cannot be undone.")) bulkDelete.mutate("all"); }}>Delete all incidents</button>
      </div>}
      {isLoading && <p className="mt-8">Loading incidents…</p>}
      {!isLoading && data.length === 0 && <div className="mt-8 rounded-2xl border border-dashed border-slate-300 p-12 text-center text-slate-500">No incidents have been recorded.</div>}
      <div className="mt-7 grid gap-6 lg:grid-cols-2">
        {data.map((incident) => (
          <article key={incident.id} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <label className="flex cursor-pointer items-center gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 font-bold text-slate-700"><input className="h-5 w-5 accent-red-700" type="checkbox" checked={selectedIds.has(incident.id)} onChange={() => setSelectedIds((current) => { const next = new Set(current); if (next.has(incident.id)) next.delete(incident.id); else next.add(incident.id); return next; })} /> Select this incident</label>
            <img className="aspect-video w-full bg-slate-950 object-contain" src={incident.snapshot_url} alt={`Incident for person ${incident.track_id}`} />
            <div className="p-5">
              <span className={`mb-3 inline-flex rounded-full px-3 py-1 text-xs font-black uppercase ${incident.source === "live_camera" ? "bg-red-100 text-red-800" : "bg-ocean-100 text-ocean-800"}`}>{incident.source === "live_camera" ? "Live camera" : "Uploaded video"}</span>
              <p className="mb-3 text-sm font-bold text-slate-700">{incident.source_name ?? incident.video_id}</p>
              <div className="flex items-start justify-between gap-3"><div><p className="font-black text-red-700">Person ID {incident.track_id} · Risk {incident.risk_score.toFixed(0)}</p><p className="mt-1 text-sm text-slate-500">{new Date(incident.created_at).toLocaleString()}</p></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold uppercase">{incident.status.replace("_", " ")}</span></div>
              <video className="mt-4 aspect-video w-full rounded-xl bg-black" controls src={incident.clip_url} />
              {incident.triggered_signals.length > 0 && (
                <div className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-900">
                  <p className="font-black">Why this alert was created</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5">
                    {incident.triggered_signals.map((signal) => <li key={signal}>{signal}</li>)}
                  </ul>
                </div>
              )}
              <IncidentNotesEditor incident={incident} />
              <p className="mt-2 text-xs font-semibold text-slate-500">Automatic deletion: {new Date(new Date(incident.created_at).getTime() + 24 * 60 * 60 * 1000).toLocaleString()}</p>
              <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
                <button className="rounded-xl bg-amber-100 px-2 py-2 text-xs font-bold text-amber-900" onClick={() => action.mutate({ id: incident.id, name: "acknowledge" })}><ShieldAlert className="mx-auto mb-1" size={17} />Acknowledge</button>
                <button className="rounded-xl bg-emerald-100 px-2 py-2 text-xs font-bold text-emerald-900" onClick={() => action.mutate({ id: incident.id, name: "resolve" })}><CheckCircle2 className="mx-auto mb-1" size={17} />Resolve</button>
                <button className="rounded-xl bg-slate-100 px-2 py-2 text-xs font-bold text-slate-700" onClick={() => action.mutate({ id: incident.id, name: "false-alarm" })}><XCircle className="mx-auto mb-1" size={17} />False alarm</button>
                <button className="rounded-xl bg-red-700 px-2 py-2 text-xs font-bold text-white" onClick={() => { if (window.confirm("Permanently delete this incident report, screenshot and video evidence?")) action.mutate({ id: incident.id, name: "delete" }); }}><Trash2 className="mx-auto mb-1" size={17} />Delete</button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </AppShell>
  );
}

function IncidentNotesEditor({ incident }: { incident: IncidentListItem }) {
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState(incident.notes);
  const save = useMutation({
    mutationFn: () => updateIncidentNotes(incident.id, notes),
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: ["incidents"] }),
  });
  return <div className="mt-4 rounded-xl bg-slate-50 p-3"><label className="text-sm font-black text-slate-800">Operator notes<textarea className="mt-2 min-h-20 w-full rounded-lg border border-slate-300 bg-white p-3 font-normal" maxLength={1000} placeholder="Record observations or response details" value={notes} onChange={(event) => setNotes(event.target.value)} /></label><button className="mt-2 rounded-lg bg-ocean-600 px-4 py-2 text-sm font-black text-white disabled:bg-slate-300" disabled={save.isPending} onClick={() => save.mutate()}>{save.isPending ? "Saving..." : "Save notes"}</button></div>;
}
