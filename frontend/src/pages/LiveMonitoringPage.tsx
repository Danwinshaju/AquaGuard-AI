import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Camera, CameraOff, Radio, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { useAuth } from "../auth/AuthContext";
import { moveIncidentEvidenceToDevice } from "../storage/userMediaStorage";

interface LiveIncident {
  id: string;
  track_id: number;
  risk_score: number;
  snapshot_url: string;
  clip_url: string;
  created_at: string;
}

interface PoolZone {
  left: number;
  top: number;
  right: number;
  bottom: number;
  deep_water_top: number;
}

type PerformanceMode = "fast" | "balanced" | "accurate";

interface LiveMetadata {
  type: "frame";
  frame: number;
  people: number;
  status: "SAFE" | "WARNING" | "DANGER";
  highest_risk: number;
  danger: boolean;
  detection_mode: "mock" | "yolo" | "yolo-bytetrack";
  effective_fps: number;
  processing_ms: number;
  performance_mode: PerformanceMode;
  aquatic_model: "active" | "not-trained";
  incidents: LiveIncident[];
}

export function LiveMonitoringPage() {
  const { user } = useAuth();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<number | null>(null);
  const responseTimeoutRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const resultUrlRef = useRef<string | null>(null);
  const awaitingResultRef = useRef(false);
  const dangerSoundedRef = useRef(false);
  const connectionErrorRef = useRef<string | null>(null);
  const evidenceObjectUrlsRef = useRef<string[]>([]);
  const zoneDrawStartRef = useRef<{ x: number; y: number } | null>(null);
  const [running, setRunning] = useState(false);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<LiveMetadata | null>(null);
  const [liveIncidents, setLiveIncidents] = useState<LiveIncident[]>([]);
  const [message, setMessage] = useState("Camera is stopped");
  const [editingZone, setEditingZone] = useState(false);
  const [performanceMode, setPerformanceMode] = useState<PerformanceMode>(() => {
    const saved = window.localStorage.getItem("aquaguard-performance-mode");
    return saved === "fast" || saved === "balanced" || saved === "accurate"
      ? saved
      : "balanced";
  });
  const [zone, setZone] = useState<PoolZone>(() => {
    const saved = window.localStorage.getItem("aquaguard-pool-zone");
    try {
      return saved
        ? normalizeZone(JSON.parse(saved) as PoolZone)
        : { left: 0.05, top: 0.1, right: 0.95, bottom: 0.95, deep_water_top: 0.55 };
    } catch {
      return { left: 0.05, top: 0.1, right: 0.95, bottom: 0.95, deep_water_top: 0.55 };
    }
  });

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
      if (responseTimeoutRef.current !== null) window.clearTimeout(responseTimeoutRef.current);
      socketRef.current?.close();
      streamRef.current?.getTracks().forEach((track) => track.stop());
      void audioContextRef.current?.close();
      if (resultUrlRef.current) URL.revokeObjectURL(resultUrlRef.current);
      for (const url of evidenceObjectUrlsRef.current) URL.revokeObjectURL(url);
    };
  }, []);

  async function startCamera() {
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("This browser does not provide camera access.");
      }
      setRunning(true);
      for (const url of evidenceObjectUrlsRef.current) URL.revokeObjectURL(url);
      evidenceObjectUrlsRef.current = [];
      setLiveIncidents([]);
      connectionErrorRef.current = null;
      try {
        audioContextRef.current = new window.AudioContext();
        void audioContextRef.current.resume();
      } catch {
        audioContextRef.current = null;
      }
      setMessage("Requesting camera permission…");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 },
          facingMode: { ideal: "environment" },
        },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      const scheme = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(`${scheme}://${window.location.host}/api/v1/live/ws`);
      socket.binaryType = "blob";
      socketRef.current = socket;
      socket.onopen = () => {
        setMessage("Loading YOLO, ByteTrack and pose models...");
        responseTimeoutRef.current = window.setTimeout(() => {
          responseTimeoutRef.current = null;
          socketRef.current = null;
          socket.close();
          streamRef.current?.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
          if (videoRef.current) videoRef.current.srcObject = null;
          setRunning(false);
          setMessage("AI models did not start within 60 seconds. Stop unused cameras and try again.");
        }, 60000);
      };
      socket.onmessage = (event) => {
        if (typeof event.data === "string") {
          const payload = JSON.parse(event.data) as { type: string; message?: string } | LiveMetadata;
          if (payload.type === "ready") {
            if (responseTimeoutRef.current !== null) window.clearTimeout(responseTimeoutRef.current);
            responseTimeoutRef.current = null;
            setMessage("High-sensitivity live YOLO tracking is active");
            socket.send(JSON.stringify({ type: "configure_zone", zone }));
            socket.send(JSON.stringify({ type: "configure_performance", mode: performanceMode }));
            scheduleNextFrame(0);
          } else if (payload.type === "frame") {
            const frameData = payload as LiveMetadata;
            setMetadata(frameData);
            if (frameData.incidents.length > 0) {
              setLiveIncidents((current) => [
                ...frameData.incidents,
                ...current.filter(
                  (existing) =>
                    !frameData.incidents.some((created) => created.id === existing.id),
                ),
              ]);
              setMessage("Live incident report and evidence saved");
              if (user) {
                for (const incident of frameData.incidents) {
                  void moveIncidentEvidenceToDevice(user.id, incident)
                    .then((local) => {
                      evidenceObjectUrlsRef.current.push(local.snapshotUrl, local.clipUrl);
                      setLiveIncidents((current) => current.map((item) => item.id === incident.id ? { ...item, snapshot_url: local.snapshotUrl, clip_url: local.clipUrl } : item));
                      setMessage("Live evidence saved in your browser; server copy removed");
                    })
                    .catch(() => setMessage("Live evidence is temporarily on the server; open Incidents to retry device storage"));
                }
              }
            }
            if (frameData.danger && !dangerSoundedRef.current) {
              dangerSoundedRef.current = true;
              playTripleBeep(audioContextRef.current);
              navigator.vibrate?.([300, 150, 300]);
            } else if (!frameData.danger) {
              dangerSoundedRef.current = false;
            }
          } else if (payload.type === "error") {
            connectionErrorRef.current = payload.message ?? "Live analysis failed.";
            setMessage(connectionErrorRef.current);
          }
        } else {
          if (resultUrlRef.current) URL.revokeObjectURL(resultUrlRef.current);
          const nextUrl = URL.createObjectURL(event.data as Blob);
          resultUrlRef.current = nextUrl;
          setResultUrl(nextUrl);
          awaitingResultRef.current = false;
          if (responseTimeoutRef.current !== null) window.clearTimeout(responseTimeoutRef.current);
          responseTimeoutRef.current = null;
          scheduleNextFrame(80);
        }
      };
      socket.onerror = () => {
        connectionErrorRef.current = "Could not connect to live analysis.";
        setMessage(connectionErrorRef.current);
      };
      socket.onclose = () => {
        if (socketRef.current !== socket) return;
        socketRef.current = null;
        awaitingResultRef.current = false;
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        if (videoRef.current) videoRef.current.srcObject = null;
        setRunning(false);
        setMessage(connectionErrorRef.current ?? "Live AI disconnected. Press Start camera to reconnect.");
      };
    } catch (error) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;
      setRunning(false);
      const errorName = error instanceof DOMException ? error.name : "";
      if (errorName === "NotAllowedError") {
        setMessage("Camera is blocked. Click the camera icon beside the address bar, choose Allow, then retry.");
      } else if (errorName === "NotReadableError") {
        setMessage("Camera is busy. Close Camera, Zoom, Teams or other video apps, then retry.");
      } else if (errorName === "NotFoundError") {
        setMessage("No camera was found on this computer.");
      } else {
        setMessage(error instanceof Error ? error.message : "Camera could not be started.");
      }
    }
  }

  function sendFrame() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const socket = socketRef.current;
    if (!video || !canvas || !socket || socket.readyState !== WebSocket.OPEN || awaitingResultRef.current) return;
    const sourceWidth = video.videoWidth || 1280;
    const sourceHeight = video.videoHeight || 720;
    const maximumWidth = performanceMode === "fast" ? 720 : performanceMode === "accurate" ? 1280 : 960;
    canvas.width = Math.min(sourceWidth, maximumWidth);
    canvas.height = Math.round(sourceHeight * (canvas.width / sourceWidth));
    canvas.getContext("2d")?.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob || socket.readyState !== WebSocket.OPEN) {
        awaitingResultRef.current = false;
        scheduleNextFrame(250);
        return;
      }
      awaitingResultRef.current = true;
      socket.send(blob);
      responseTimeoutRef.current = window.setTimeout(() => {
        responseTimeoutRef.current = null;
        awaitingResultRef.current = false;
        socketRef.current = null;
        socket.close();
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        setRunning(false);
        if (videoRef.current) videoRef.current.srcObject = null;
        setMessage("AI processing timed out. Close unused camera streams and start again.");
      }, 60000);
    }, "image/jpeg", 0.85);
  }

  function scheduleNextFrame(delayMilliseconds: number) {
    if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => {
      timerRef.current = null;
      sendFrame();
    }, delayMilliseconds);
  }

  function updateZone(name: keyof PoolZone, value: number) {
    const nextZone = normalizeZone({ ...zone, [name]: value });
    setZone(nextZone);
    window.localStorage.setItem("aquaguard-pool-zone", JSON.stringify(nextZone));
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "configure_zone", zone: nextZone }));
    }
  }

  function saveZone(nextZone: PoolZone) {
    const normalized = normalizeZone(nextZone);
    setZone(normalized);
    window.localStorage.setItem("aquaguard-pool-zone", JSON.stringify(normalized));
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "configure_zone", zone: normalized }));
    }
  }

  function zonePoint(event: React.PointerEvent<HTMLDivElement>) {
    const bounds = event.currentTarget.getBoundingClientRect();
    return {
      x: Math.min(Math.max((event.clientX - bounds.left) / bounds.width, 0), 1),
      y: Math.min(Math.max((event.clientY - bounds.top) / bounds.height, 0), 1),
    };
  }

  function startZoneDrawing(event: React.PointerEvent<HTMLDivElement>) {
    if (!editingZone) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    zoneDrawStartRef.current = zonePoint(event);
  }

  function continueZoneDrawing(event: React.PointerEvent<HTMLDivElement>) {
    const start = zoneDrawStartRef.current;
    if (!editingZone || !start) return;
    const current = zonePoint(event);
    const left = Math.min(start.x, current.x);
    const right = Math.max(start.x, current.x);
    const top = Math.min(start.y, current.y);
    const bottom = Math.max(start.y, current.y);
    if (right - left >= 0.05 && bottom - top >= 0.05) {
      setZone(normalizeZone({ ...zone, left, right, top, bottom }));
    }
  }

  function finishZoneDrawing(event: React.PointerEvent<HTMLDivElement>) {
    const start = zoneDrawStartRef.current;
    if (!start) return;
    const current = zonePoint(event);
    zoneDrawStartRef.current = null;
    saveZone({
      ...zone,
      left: Math.min(start.x, current.x),
      right: Math.max(start.x, current.x),
      top: Math.min(start.y, current.y),
      bottom: Math.max(start.y, current.y),
    });
    setEditingZone(false);
  }

  function resetZone() {
    saveZone({ left: 0.05, top: 0.05, right: 0.95, bottom: 0.95, deep_water_top: 0.55 });
  }

  function changePerformanceMode(mode: PerformanceMode) {
    setPerformanceMode(mode);
    window.localStorage.setItem("aquaguard-performance-mode", mode);
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "configure_performance", mode }));
    }
  }

  function stopCamera() {
    if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    if (responseTimeoutRef.current !== null) window.clearTimeout(responseTimeoutRef.current);
    timerRef.current = null;
    responseTimeoutRef.current = null;
    socketRef.current?.close();
    socketRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    void audioContextRef.current?.close();
    audioContextRef.current = null;
    awaitingResultRef.current = false;
    if (resultUrlRef.current) URL.revokeObjectURL(resultUrlRef.current);
    resultUrlRef.current = null;
    setResultUrl(null);
    setMetadata(null);
    setRunning(false);
    setMessage("Camera is stopped");
  }

  const danger = metadata?.danger ?? false;
  const warning = metadata?.status === "WARNING";
  return (
    <AppShell>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div><h1 className="text-3xl font-black">Live camera monitoring</h1><p className="mt-2 text-slate-500">Track people and risk from this device's camera.</p></div>
        <button className={`flex items-center gap-2 rounded-xl px-5 py-3 font-black text-white ${running ? "bg-slate-700" : "bg-ocean-600"}`} onClick={running ? stopCamera : startCamera}>{running ? <CameraOff size={20} /> : <Camera size={20} />}{running ? "Stop camera" : "Start camera"}</button>
      </div>
      <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950"><strong>Assistance only:</strong> keep direct visual supervision. Live AI alerts can be wrong or delayed.</div>
      <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-4"><h2 className="font-black">Live performance</h2><p className="mt-1 text-sm text-slate-500">Choose Fast if tracking freezes, Balanced for normal use, or Accurate with a strong GPU.</p><div className="mt-3 grid gap-2 sm:grid-cols-3">{(["fast", "balanced", "accurate"] as PerformanceMode[]).map((mode) => <button key={mode} className={`rounded-xl px-4 py-3 text-left font-black capitalize ${performanceMode === mode ? "bg-ocean-600 text-white" : "bg-slate-100 text-slate-700"}`} type="button" onClick={() => changePerformanceMode(mode)}>{mode}<span className="mt-1 block text-xs font-medium opacity-80">{mode === "fast" ? "Best for CPU" : mode === "balanced" ? "Recommended" : "Best detail / GPU"}</span></button>)}</div></section>
      <details className="mt-5 rounded-2xl border border-slate-200 bg-white p-4">
        <summary className="cursor-pointer font-black text-slate-900">Calibrate pool and deep-water zone</summary>
        <p className="mt-2 text-sm text-slate-500">Adjust these boundaries until the blue box covers only the pool. The purple line marks where deep water begins.</p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <ZoneSlider label="Left" value={zone.left} min={0} max={zone.right - 0.05} onChange={(value) => updateZone("left", value)} />
          <ZoneSlider label="Top" value={zone.top} min={0} max={zone.bottom - 0.05} onChange={(value) => updateZone("top", value)} />
          <ZoneSlider label="Right" value={zone.right} min={zone.left + 0.05} max={1} onChange={(value) => updateZone("right", value)} />
          <ZoneSlider label="Bottom" value={zone.bottom} min={zone.top + 0.05} max={1} onChange={(value) => updateZone("bottom", value)} />
          <ZoneSlider label="Deep water" value={zone.deep_water_top} min={zone.top} max={zone.bottom} onChange={(value) => updateZone("deep_water_top", value)} />
        </div>
        <div className="mt-4 flex flex-wrap gap-3"><button className={`rounded-xl px-4 py-2 font-black text-white ${editingZone ? "bg-amber-600" : "bg-ocean-600"}`} type="button" onClick={() => setEditingZone((current) => !current)}>{editingZone ? "Drawing enabled - drag on camera" : "Draw pool zone on camera"}</button><button className="rounded-xl bg-slate-200 px-4 py-2 font-black text-slate-800" type="button" onClick={resetZone}>Reset full zone</button></div>
      </details>
      {danger && <div className="animate-alert mt-5 flex items-center gap-3 rounded-2xl bg-red-600 p-5 text-white"><AlertTriangle size={30} /><div><p className="text-xl font-black">POSSIBLE DROWNING — VERIFY NOW</p><p>Alert a trained lifeguard and follow the emergency plan.</p></div></div>}
      {warning && !danger && <div className="mt-5 flex items-center gap-3 rounded-2xl border-2 border-amber-400 bg-amber-100 p-5 text-amber-950"><AlertTriangle size={28} /><div><p className="text-lg font-black">Early warning - check this person</p><p>Movement or posture needs immediate visual verification.</p></div></div>}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-4"><h2 className="mb-3 flex items-center gap-2 font-black"><Camera size={19} /> Camera input</h2><div className={`relative aspect-video overflow-hidden rounded-xl bg-slate-950 ${editingZone ? "cursor-crosshair ring-4 ring-amber-400" : ""}`} onPointerDown={startZoneDrawing} onPointerMove={continueZoneDrawing} onPointerUp={finishZoneDrawing}><video ref={videoRef} className="h-full w-full object-contain" muted playsInline /><div className="pointer-events-none absolute border-2 border-cyan-400 bg-cyan-400/10" style={{ left: `${zone.left * 100}%`, top: `${zone.top * 100}%`, width: `${(zone.right - zone.left) * 100}%`, height: `${(zone.bottom - zone.top) * 100}%` }}><span className="absolute left-1 top-1 rounded bg-cyan-700 px-2 py-1 text-[10px] font-black text-white">POOL ZONE</span></div><div className="pointer-events-none absolute h-0.5 bg-fuchsia-500" style={{ left: `${zone.left * 100}%`, top: `${zone.deep_water_top * 100}%`, width: `${(zone.right - zone.left) * 100}%` }} /></div><canvas ref={canvasRef} className="hidden" /></section>
        <section className="rounded-2xl border border-slate-200 bg-white p-4"><h2 className="mb-3 flex items-center gap-2 font-black"><Radio size={19} /> AI tracking output</h2>{resultUrl ? <img className="aspect-video w-full rounded-xl bg-slate-950 object-contain" src={resultUrl} alt="Live AI tracking output" /> : <div className="flex aspect-video flex-col items-center justify-center gap-4 rounded-xl bg-slate-950 px-6 text-center text-slate-300"><p>{message}</p>{!running && <button className="rounded-xl bg-ocean-600 px-5 py-3 font-black text-white hover:bg-ocean-700" onClick={startCamera}><Camera size={19} className="mr-2 inline" />Retry live camera</button>}</div>}</section>
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-4"><LiveStat label="Status" value={metadata?.status ?? "OFFLINE"} danger={danger} /><LiveStat label="People" value={String(metadata?.people ?? 0)} /><LiveStat label="Highest risk" value={`${(metadata?.highest_risk ?? 0).toFixed(0)}`} danger={danger} /><LiveStat label="Mode" value={metadata?.detection_mode?.toUpperCase() ?? "—"} /></div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2"><div className="rounded-xl border border-slate-200 bg-white p-4"><p className="text-xs font-bold uppercase text-slate-500">Live AI processing speed</p><p className="mt-1 text-xl font-black text-slate-950">{(metadata?.effective_fps ?? 0).toFixed(1)} FPS</p></div><div className="rounded-xl border border-slate-200 bg-white p-4"><p className="text-xs font-bold uppercase text-slate-500">Custom aquatic dataset model</p><p className={`mt-1 text-xl font-black ${metadata?.aquatic_model === "active" ? "text-emerald-700" : "text-amber-700"}`}>{metadata?.aquatic_model === "active" ? "ACTIVE" : "NOT TRAINED"}</p></div></div>
      <p className="mt-2 text-xs font-semibold text-slate-500">Latest AI frame: {metadata?.processing_ms ?? 0} ms. For best speed, stop unused network cameras and close other video applications.</p>
      {liveIncidents.length > 0 && (
        <section className="mt-6 rounded-2xl border-2 border-red-400 bg-red-50 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div><h2 className="text-xl font-black text-red-800">Saved live incident evidence</h2><p className="text-sm text-red-700">The report stays in MongoDB while screenshots and clips move into this browser's private storage.</p></div>
            <Link className="rounded-xl bg-red-700 px-4 py-2 font-black text-white" to="/incidents">View all incident reports</Link>
          </div>
          <div className="mt-5 grid gap-5 lg:grid-cols-2">
            {liveIncidents.slice(0, 4).map((incident) => (
              <article key={incident.id} className="overflow-hidden rounded-xl border border-red-200 bg-white p-3">
                <p className="font-black text-red-800">Live camera - Person {incident.track_id} - Risk {incident.risk_score.toFixed(0)}</p>
                <p className="mb-3 text-xs text-slate-500">{new Date(incident.created_at).toLocaleString()}</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <img className="aspect-video w-full rounded-lg bg-black object-contain" src={incident.snapshot_url} alt="Live incident evidence snapshot" />
                  <video className="aspect-video w-full rounded-lg bg-black" controls preload="metadata" src={incident.clip_url} />
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
      <p className="mt-4 flex items-center gap-2 text-sm text-slate-500"><ShieldCheck size={17} /> {message}</p>
    </AppShell>
  );
}

function LiveStat({ label, value, danger = false }: { label: string; value: string; danger?: boolean }) {
  return <div className={`rounded-xl border bg-white p-4 ${danger ? "border-red-400" : "border-slate-200"}`}><p className="text-xs font-bold uppercase text-slate-500">{label}</p><p className={`mt-1 text-2xl font-black ${danger ? "text-red-700" : "text-slate-950"}`}>{value}</p></div>;
}

function ZoneSlider({ label, value, min, max, onChange }: { label: string; value: number; min: number; max: number; onChange: (value: number) => void }) {
  return <label className="text-xs font-bold text-slate-600">{label}: {Math.round(value * 100)}%<input className="mt-2 w-full accent-cyan-600" type="range" min={min} max={max} step={0.01} value={value} onChange={(event) => onChange(Number(event.target.value))} /></label>;
}

function normalizeZone(zone: PoolZone): PoolZone {
  const left = Math.min(Math.max(zone.left, 0), 0.95);
  const right = Math.min(Math.max(zone.right, left + 0.05), 1);
  const top = Math.min(Math.max(zone.top, 0), 0.95);
  const bottom = Math.min(Math.max(zone.bottom, top + 0.05), 1);
  const deep_water_top = Math.min(Math.max(zone.deep_water_top, top), bottom);
  return { left, top, right, bottom, deep_water_top };
}

function playTripleBeep(context: AudioContext | null) {
  try {
    if (!context) return;
    for (let index = 0; index < 3; index += 1) {
      const start = context.currentTime + index * 0.48;
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = "square";
      oscillator.frequency.setValueAtTime(880, start);
      gain.gain.setValueAtTime(0.14, start);
      gain.gain.exponentialRampToValueAtTime(0.001, start + 0.24);
      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.start(start);
      oscillator.stop(start + 0.24);
    }
  } catch { /* Visual alert remains available. */ }
}
