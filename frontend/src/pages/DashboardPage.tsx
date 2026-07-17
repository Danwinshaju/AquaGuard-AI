import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Camera, CheckCircle2, Clock3, ShieldAlert } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchDashboard, fetchSystemHealth } from "../api/dashboard";
import { AppShell } from "../components/AppShell";

export function DashboardPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });
  const { data: system } = useQuery({ queryKey: ["system-health"], queryFn: fetchSystemHealth, refetchInterval: 10000 });
  return (
    <AppShell>
      <h1 className="text-3xl font-black">Safety dashboard</h1>
      <p className="mt-2 text-slate-500">Incident activity recorded by your local AquaGuard system.</p>
      {isLoading && <p className="mt-8">Loading dashboard…</p>}
      {error && <p className="mt-8 text-red-700">Could not load dashboard.</p>}
      {system && <section className="mt-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm sm:grid-cols-2 lg:grid-cols-5"><HealthItem label="MongoDB" value={system.mongodb ? "Connected" : "Disconnected"} good={system.mongodb} /><HealthItem label="AI device" value={system.cuda_available ? system.gpu_name ?? "CUDA GPU" : "CPU"} good /><HealthItem label="Temporal model" value={system.temporal_model_ready ? "Trained" : "Not trained"} good={system.temporal_model_ready} /><HealthItem label="Network cameras" value={`${system.online_cameras}/${system.total_cameras} online`} good={system.online_cameras === system.total_cameras} /><HealthItem label="Free storage" value={`${system.storage_free_gb} GB`} good={system.storage_free_gb >= 2} /></section>}
      {data && (
        <>
          <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat icon={<Camera />} label="Active cameras" value={data.active_cameras} />
            <Stat icon={<ShieldAlert />} label="Critical alerts" value={data.critical_alert_count} danger />
            <Stat icon={<AlertTriangle />} label="Unresolved" value={data.unresolved_incidents} danger />
            <Stat icon={<Clock3 />} label="Average acknowledgement" value={`${data.average_acknowledgement_seconds}s`} />
          </div>
          <div className="mt-6 grid gap-6 lg:grid-cols-[1.5fr_0.5fr]">
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="font-black">Alerts by day</h2>
              <div className="mt-5 h-72">
                {data.alerts_by_day.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.alerts_by_day}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="alerts" fill="#0786a5" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : <div className="grid h-full place-items-center text-slate-400">No incidents recorded yet</div>}
              </div>
            </section>
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <CheckCircle2 className="text-emerald-600" />
              <p className="mt-4 text-3xl font-black">{data.false_positive_rate}%</p>
              <p className="text-sm text-slate-500">False-positive rate</p>
            </section>
          </div>
        </>
      )}
    </AppShell>
  );
}

function Stat({ icon, label, value, danger = false }: { icon: React.ReactNode; label: string; value: number | string; danger?: boolean }) {
  return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><span className={danger ? "text-red-600" : "text-ocean-600"}>{icon}</span><p className="mt-4 text-3xl font-black">{value}</p><p className="text-sm text-slate-500">{label}</p></div>;
}

function HealthItem({ label, value, good }: { label: string; value: string; good: boolean }) {
  return <div className="rounded-xl bg-slate-50 p-3"><p className="text-xs font-bold uppercase text-slate-500">{label}</p><p className={`mt-1 font-black ${good ? "text-emerald-700" : "text-amber-700"}`}>{value}</p></div>;
}
