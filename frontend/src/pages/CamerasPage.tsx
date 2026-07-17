import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Camera, Plus, RefreshCw, Trash2 } from "lucide-react";
import { useState } from "react";
import { addCamera, deleteCamera, fetchCameras } from "../api/cameras";
import { AppShell } from "../components/AppShell";

export function CamerasPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const { data = [] } = useQuery({
    queryKey: ["cameras"],
    queryFn: fetchCameras,
    refetchInterval: 3000,
  });
  const createCamera = useMutation({
    mutationFn: () => addCamera(name, sourceUrl),
    onSuccess: async () => {
      setName("");
      setSourceUrl("");
      await queryClient.invalidateQueries({ queryKey: ["cameras"] });
    },
  });
  const removeCamera = useMutation({
    mutationFn: deleteCamera,
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: ["cameras"] }),
  });
  return <AppShell>
    <div className="flex items-end justify-between gap-4"><div><h1 className="text-3xl font-black">Network cameras</h1><p className="mt-2 text-slate-500">Connect multiple RTSP or HTTP pool cameras with automatic reconnection.</p></div><Camera size={34} className="text-ocean-600" /></div>
    <form className="mt-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 md:grid-cols-[0.5fr_1fr_auto]" onSubmit={(event) => { event.preventDefault(); createCamera.mutate(); }}>
      <input className="rounded-xl border border-slate-300 px-4 py-3" placeholder="Camera name" value={name} onChange={(event) => setName(event.target.value)} required />
      <input className="rounded-xl border border-slate-300 px-4 py-3" placeholder="rtsp://camera-address/stream" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} required />
      <button className="flex items-center justify-center gap-2 rounded-xl bg-ocean-600 px-5 py-3 font-black text-white" type="submit" disabled={createCamera.isPending}><Plus size={19} /> Add camera</button>
    </form>
    {createCamera.error && <p className="mt-3 rounded-xl bg-red-50 p-3 text-red-800">{createCamera.error.message}</p>}
    {data.length === 0 && <div className="mt-7 rounded-2xl border border-dashed border-slate-300 p-12 text-center text-slate-500">No network cameras added. Browser live camera remains available under Live.</div>}
    <div className="mt-7 grid gap-6 lg:grid-cols-2">
      {data.map((camera) => <article key={camera.id} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <img className="aspect-video w-full bg-slate-950 object-contain" src={camera.stream_url} alt={`${camera.name} annotated stream`} />
        <div className="p-5"><div className="flex items-start justify-between gap-3"><div><h2 className="text-xl font-black">{camera.name}</h2><p className="mt-1 flex items-center gap-2 text-sm text-slate-500"><RefreshCw size={14} /> Reconnects: {camera.reconnect_count}</p></div><span className={`rounded-full px-3 py-1 text-xs font-black uppercase ${camera.status === "online" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-900"}`}>{camera.status}</span></div>
          <div className="mt-4 grid grid-cols-2 gap-3"><div className="rounded-xl bg-slate-50 p-3"><p className="text-xs font-bold text-slate-500">People</p><p className="text-2xl font-black">{camera.people}</p></div><div className="rounded-xl bg-slate-50 p-3"><p className="text-xs font-bold text-slate-500">Highest risk</p><p className="text-2xl font-black">{camera.highest_risk.toFixed(0)}</p></div></div>
          {camera.error && <p className="mt-3 text-sm font-semibold text-red-700">{camera.error}</p>}
          <button className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-red-700 px-4 py-3 font-black text-white" onClick={() => removeCamera.mutate(camera.id)}><Trash2 size={18} /> Remove camera</button>
        </div>
      </article>)}
    </div>
  </AppShell>;
}
