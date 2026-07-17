import { useEffect, useRef, useState, type ReactNode } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  BellRing,
  BookOpen,
  BrainCircuit,
  Camera,
  CheckCircle2,
  Cctv,
  FileVideo2,
  LifeBuoy,
  LoaderCircle,
  LogOut,
  RotateCcw,
  ShieldCheck,
  UploadCloud,
  Users,
} from "lucide-react";
import {
  acknowledgeIncident,
  startVideoProcessing,
  uploadVideo,
  watchVideoProcessing,
} from "./api/videos";
import type { VideoProcessingResponse } from "./types/video";
import { DashboardPage } from "./pages/DashboardPage";
import { IncidentsPage } from "./pages/IncidentsPage";
import { LiveMonitoringPage } from "./pages/LiveMonitoringPage";
import { CamerasPage } from "./pages/CamerasPage";
import { ModelTrainingPage } from "./pages/ModelTrainingPage";
import { DocumentationPage } from "./pages/DocumentationPage";
import { ProjectFooter } from "./components/ProjectFooter";
import { AuthPage } from "./pages/AuthPage";
import { useAuth } from "./auth/AuthContext";
import { moveIncidentEvidenceToDevice, moveProcessedVideoToDevice } from "./storage/userMediaStorage";

type Phase = "choose" | "uploading" | "analysing" | "complete" | "error";

const acceptedTypes = ".mp4,.avi,.mov,video/mp4,video/quicktime,video/x-msvideo";

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function AnalyzePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const playedAlertIdsRef = useRef<Set<string>>(new Set());
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("choose");
  const [error, setError] = useState("");
  const [result, setResult] = useState<VideoProcessingResponse | null>(null);
  const [dragging, setDragging] = useState(false);
  const [acknowledgedIds, setAcknowledgedIds] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
  const [storageStatus, setStorageStatus] = useState<"idle" | "moving" | "device" | "partial">("idle");
  const savedObjectUrlsRef = useRef<string[]>([]);

  useEffect(() => () => releaseSavedObjectUrls(), []);

  const analysis = useMutation({
    mutationFn: async (selectedFile: File) => {
      setPhase("uploading");
      setProgress(5);
      const uploaded = await uploadVideo(selectedFile);
      setPhase("analysing");
      setProgress(10);
      const job = await startVideoProcessing(uploaded.id);
      return watchVideoProcessing(job.job_id, (value) => {
        setProgress(10 + value * 0.9);
      });
    },
    onSuccess: (processed) => {
      setResult(processed);
      setPhase("complete");
      setStorageStatus("moving");
      if (!user) return;
      void (async () => {
        let complete = true;
        let processedUrl = processed.download_url;
        try {
          processedUrl = await moveProcessedVideoToDevice(user.id, processed.id, processed.download_url);
          savedObjectUrlsRef.current.push(processedUrl);
        } catch {
          complete = false;
        }
        const incidents = await Promise.all(processed.incidents.map(async (incident) => {
          try {
            const local = await moveIncidentEvidenceToDevice(user.id, incident);
            savedObjectUrlsRef.current.push(local.snapshotUrl, local.clipUrl);
            return { ...incident, snapshot_url: local.snapshotUrl, clip_url: local.clipUrl };
          } catch {
            complete = false;
            return incident;
          }
        }));
        setResult((current) => current?.id === processed.id
          ? { ...current, download_url: processedUrl, incidents }
          : current);
        setStorageStatus(complete ? "device" : "partial");
      })();
    },
    onError: (reason) => {
      setError(reason instanceof Error ? reason.message : "Something went wrong.");
      setPhase("error");
    },
  });

  function selectFile(selected: File | undefined) {
    if (!selected) return;
    const extension = selected.name.split(".").pop()?.toLowerCase();
    if (!extension || !["mp4", "avi", "mov"].includes(extension)) {
      setError("Please choose an MP4, AVI, or MOV video.");
      setPhase("error");
      return;
    }
    setFile(selected);
    setError("");
    setResult(null);
    setPhase("choose");
  }

  function startAnalysis() {
    if (!file) {
      inputRef.current?.click();
      return;
    }
    setError("");
    analysis.mutate(file);
  }

  function reset() {
    releaseSavedObjectUrls();
    analysis.reset();
    setFile(null);
    setResult(null);
    setError("");
    setPhase("choose");
    setAcknowledgedIds([]);
    setProgress(0);
    setStorageStatus("idle");
    playedAlertIdsRef.current.clear();
    if (inputRef.current) inputRef.current.value = "";
  }

  function releaseSavedObjectUrls() {
    for (const url of savedObjectUrlsRef.current) URL.revokeObjectURL(url);
    savedObjectUrlsRef.current = [];
  }

  const busy = phase === "uploading" || phase === "analysing";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white/95">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <div className="flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-ocean-600 text-white shadow-soft">
              <LifeBuoy aria-hidden="true" size={24} />
            </span>
            <div>
              <p className="text-lg font-bold tracking-tight">AquaGuard AI</p>
              <p className="text-xs font-medium text-slate-500">Pool video safety assistant</p>
            </div>
          </div>
          <nav className="flex max-w-full flex-wrap items-center gap-1 text-sm font-bold" aria-label="Main navigation">
            <Link className="rounded-lg bg-ocean-100 px-3 py-2 text-ocean-800" to="/analyze">Analyse</Link>
            <Link className="flex items-center gap-2 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100" to="/live"><Camera size={17} /> Live Camera</Link>
            <Link className="flex items-center gap-2 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100" to="/cameras"><Cctv size={17} /> Cameras</Link>
            <Link className="rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100" to="/dashboard">Dashboard</Link>
            <Link className="rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100" to="/incidents">Incidents</Link>
            <Link className="flex items-center gap-2 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100" to="/model"><BrainCircuit size={17} /> Train AI</Link>
            <Link className="flex items-center gap-2 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100" to="/documentation"><BookOpen size={17} /> Documentation</Link>
            <button className="flex items-center gap-2 rounded-lg px-3 py-2 text-red-700 hover:bg-red-50" type="button" title={user?.email} onClick={async () => { await logout(); navigate("/login"); }}><LogOut size={17} /> Log out</button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8 sm:py-12">
        <section className="mb-7 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3.5 text-sm text-amber-950 sm:flex sm:items-center sm:gap-3">
          <AlertTriangle className="mb-2 shrink-0 text-amber-600 sm:mb-0" size={21} />
          <p>
            <strong>Educational assistance only.</strong> AquaGuard AI is not a certified
            safety device and must never replace trained lifeguards or active supervision.
          </p>
        </section>

        <section className="mb-7 grid gap-4 sm:grid-cols-2" aria-label="Choose analysis mode">
          <div className="flex items-center gap-4 rounded-2xl border-2 border-ocean-500 bg-ocean-50 p-5">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-ocean-600 text-white"><UploadCloud size={25} /></span>
            <div><p className="font-black text-ocean-950">Uploaded video</p><p className="text-sm text-ocean-700">You are currently using video-file analysis.</p></div>
          </div>
          <Link className="flex items-center gap-4 rounded-2xl bg-emerald-600 p-5 text-white shadow-lg shadow-emerald-600/20 hover:bg-emerald-700" to="/live">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-white/20"><Camera size={25} /></span>
            <div><p className="text-lg font-black">Open Live Camera</p><p className="text-sm text-emerald-50">Start real-time person tracking and alerts.</p></div>
          </Link>
        </section>

        <div className="grid items-start gap-8 lg:grid-cols-[0.82fr_1.18fr]">
          <section className="pt-2">
            <p className="mb-3 text-sm font-bold uppercase tracking-[0.18em] text-ocean-600">
              Simple video check
            </p>
            <h1 className="max-w-xl text-4xl font-black leading-tight tracking-tight text-slate-950 sm:text-5xl">
              Check a pool video in three easy steps.
            </h1>
            <p className="mt-5 max-w-lg text-base leading-7 text-slate-600">
              Choose a video, let AquaGuard analyse each person, then review the labelled
              result. Your original file stays on this computer.
            </p>

            <ol className="mt-8 space-y-4" aria-label="How AquaGuard works">
              {[
                ["1", "Choose your video", "MP4, AVI or MOV"],
                ["2", "Wait while we analyse", "People, movement and inactivity"],
                ["3", "Review the result", "Watch the labelled video"],
              ].map(([number, title, text]) => (
                <li key={number} className="flex gap-4">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ocean-100 text-sm font-black text-ocean-700">
                    {number}
                  </span>
                  <div>
                    <p className="font-bold text-slate-900">{title}</p>
                    <p className="text-sm text-slate-500">{text}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
            {phase !== "complete" ? (
              <div className="p-5 sm:p-8">
                <div
                  className={`relative grid min-h-64 place-items-center rounded-2xl border-2 border-dashed p-6 text-center transition ${
                    dragging
                      ? "border-ocean-500 bg-ocean-50"
                      : file
                        ? "border-emerald-300 bg-emerald-50/60"
                        : "border-slate-300 bg-slate-50 hover:border-ocean-400 hover:bg-ocean-50/50"
                  }`}
                  onDragEnter={(event) => {
                    event.preventDefault();
                    setDragging(true);
                  }}
                  onDragOver={(event) => event.preventDefault()}
                  onDragLeave={() => setDragging(false)}
                  onDrop={(event) => {
                    event.preventDefault();
                    setDragging(false);
                    selectFile(event.dataTransfer.files[0]);
                  }}
                >
                  <input
                    ref={inputRef}
                    className="sr-only"
                    type="file"
                    accept={acceptedTypes}
                    onChange={(event) => selectFile(event.target.files?.[0])}
                  />
                  {file ? (
                    <div>
                      <span className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-emerald-100 text-emerald-700">
                        <FileVideo2 size={32} />
                      </span>
                      <p className="mt-4 max-w-sm truncate text-lg font-bold text-slate-900">
                        {file.name}
                      </p>
                      <p className="mt-1 text-sm text-slate-500">{formatBytes(file.size)}</p>
                      {!busy && (
                        <button
                          className="mt-4 text-sm font-bold text-ocean-700 underline decoration-ocean-300 underline-offset-4"
                          type="button"
                          onClick={() => inputRef.current?.click()}
                        >
                          Choose a different video
                        </button>
                      )}
                    </div>
                  ) : (
                    <div>
                      <span className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-ocean-100 text-ocean-700">
                        <UploadCloud size={32} />
                      </span>
                      <p className="mt-4 text-xl font-bold">Choose a pool video</p>
                      <p className="mt-2 text-sm leading-6 text-slate-500">
                        Drag it here, or use the button below<br />MP4, AVI or MOV · up to 500 MB
                      </p>
                      <button
                        className="mt-5 rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-bold shadow-sm hover:border-ocean-400 hover:text-ocean-700"
                        type="button"
                        onClick={() => inputRef.current?.click()}
                      >
                        Browse videos
                      </button>
                    </div>
                  )}
                </div>

                {busy && (
                  <div className="mt-5 rounded-2xl bg-ocean-50 p-4" role="status">
                    <div className="flex items-center gap-3">
                      <LoaderCircle className="animate-spin text-ocean-600" size={22} />
                      <div>
                        <p className="font-bold text-ocean-900">
                          {phase === "uploading" ? "Uploading your video…" : "Analysing every frame…"}
                        </p>
                        <p className="text-sm text-ocean-700">
                          Fast Mode is enabled. Please keep this page open.
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-ocean-100">
                      <div
                        className="h-full rounded-full bg-ocean-600 transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <p className="mt-2 text-right text-sm font-black text-ocean-800">
                      {Math.round(progress)}%
                    </p>
                  </div>
                )}

                {phase === "error" && (
                  <div className="mt-5 flex gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800" role="alert">
                    <AlertTriangle className="shrink-0" size={20} />
                    <div>
                      <p className="font-bold">We could not analyse this video</p>
                      <p className="mt-1">{error}</p>
                    </div>
                  </div>
                )}

                <button
                  className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-ocean-600 px-5 py-4 text-base font-black text-white shadow-lg shadow-ocean-600/20 transition hover:bg-ocean-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
                  type="button"
                  disabled={!file || busy}
                  onClick={startAnalysis}
                >
                  {busy ? <LoaderCircle className="animate-spin" size={21} /> : <ShieldCheck size={21} />}
                  {busy ? "Please wait…" : "Upload and analyse video"}
                </button>
              </div>
            ) : result ? (
              <div>
                <div className="border-b border-emerald-100 bg-emerald-50 px-5 py-4 sm:px-8">
                  <div className="flex items-center gap-3 text-emerald-800">
                    <CheckCircle2 size={24} />
                    <div>
                      <p className="font-black">Analysis complete</p>
                      <p className="text-sm">Review the labelled video below.</p>
                    </div>
                  </div>
                </div>
                <div className="bg-slate-950 p-2 sm:p-4">
                  <video
                    className="aspect-video w-full rounded-xl bg-black"
                    controls
                    preload="metadata"
                    src={result.download_url}
                    onTimeUpdate={(event) => {
                      const currentTime = event.currentTarget.currentTime;
                      for (const incident of result.incidents) {
                        if (
                          currentTime >= incident.occurred_at_seconds &&
                          !playedAlertIdsRef.current.has(incident.id)
                        ) {
                          playedAlertIdsRef.current.add(incident.id);
                          playAlertTone();
                          navigator.vibrate?.([300, 150, 300]);
                        }
                      }
                    }}
                    onSeeked={(event) => {
                      const currentTime = event.currentTarget.currentTime;
                      for (const incident of result.incidents) {
                        if (currentTime < incident.occurred_at_seconds) {
                          playedAlertIdsRef.current.delete(incident.id);
                        }
                      }
                    }}
                  >
                    Your browser cannot play this video.
                  </video>
                </div>
                <div className="p-5 sm:p-8">
                  <div className={`mb-5 rounded-xl border p-3 text-sm font-bold ${storageStatus === "device" ? "border-emerald-200 bg-emerald-50 text-emerald-900" : storageStatus === "partial" ? "border-amber-200 bg-amber-50 text-amber-900" : "border-ocean-200 bg-ocean-50 text-ocean-900"}`}>{storageStatus === "device" ? "Processed video and evidence are saved in this browser. Server copies were removed." : storageStatus === "partial" ? "Some media could not move to browser storage. Its temporary server copy remains available." : "Moving the processed video and evidence into your browser storage..."}</div>
                  <a className="mb-5 inline-flex rounded-xl bg-ocean-600 px-4 py-2 font-black text-white" href={result.download_url} download={`aquaguard-${result.id}.mp4`}>Download processed video</a>
                  {result.detection_mode === "mock" && (
                    <div className="mb-5 flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                      <AlertTriangle className="shrink-0" size={20} />
                      <div>
                        <p className="font-black">Demo boxes are enabled</p>
                        <p className="mt-1">
                          Demo mode draws a sample box. Enable YOLO mode to detect and track
                          the actual people in your video.
                        </p>
                      </div>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <ResultStat icon={<Users size={18} />} label="People tracked" value={String(result.unique_people_tracked)} />
                    <ResultStat icon={<FileVideo2 size={18} />} label="Frames checked" value={String(result.frame_count)} />
                    <ResultStat icon={<ShieldCheck size={18} />} label="Detection mode" value={result.detection_mode === "mock" ? "Demo" : "YOLO"} />
                    <ResultStat icon={<AlertTriangle size={18} />} label="Longest inactive" value={`${result.maximum_inactivity_seconds.toFixed(1)}s`} />
                  </div>
                  {result.incidents.length > 0 && (
                    <div className="mt-5 overflow-hidden rounded-2xl border-2 border-red-500 bg-red-50 shadow-lg shadow-red-200">
                      <div className="animate-alert flex gap-3 bg-red-600 p-4 text-white">
                        <BellRing className="shrink-0" size={26} />
                        <div>
                          <p className="text-lg font-black uppercase tracking-wide">
                            Possible drowning behaviour detected
                          </p>
                          <p className="mt-1 text-sm text-red-50">
                            Verify the person immediately and alert a trained lifeguard.
                          </p>
                        </div>
                      </div>
                      <div className="grid gap-4 p-4">
                        {result.incidents.map((incident) => (
                          <article
                            key={incident.id}
                            className="overflow-hidden rounded-xl border border-red-200 bg-white p-3 text-sm"
                          >
                            <p className="font-bold text-slate-900">
                              Person ID {incident.track_id} · Risk {incident.risk_score.toFixed(0)}
                            </p>
                            <p className="mt-1 text-slate-500">
                              At {incident.occurred_at_seconds.toFixed(1)} seconds
                            </p>
                            <div className="mt-3 grid gap-3 bg-slate-950 p-3 sm:grid-cols-2">
                              <figure>
                                <img
                                  className="aspect-video w-full rounded-lg object-contain"
                                  src={incident.snapshot_url}
                                  alt={`Evidence snapshot for person ${incident.track_id}`}
                                />
                                <figcaption className="mt-1 text-center text-xs text-slate-300">
                                  Alert snapshot
                                </figcaption>
                              </figure>
                              <figure>
                                <video
                                  className="aspect-video w-full rounded-lg bg-black"
                                  controls
                                  preload="metadata"
                                  src={incident.clip_url}
                                />
                                <figcaption className="mt-1 text-center text-xs text-slate-300">
                                  Short evidence clip
                                </figcaption>
                              </figure>
                            </div>
                            <ol className="mt-3 grid gap-1 font-semibold text-slate-700 sm:grid-cols-3">
                              <li>1. Verify visually</li>
                              <li>2. Alert lifeguard</li>
                              <li>3. Follow emergency plan</li>
                            </ol>
                            <div className="mt-3 flex gap-3 font-bold text-red-700">
                              <a href={incident.snapshot_url} target="_blank" rel="noreferrer">
                                View snapshot
                              </a>
                              <a href={incident.clip_url} target="_blank" rel="noreferrer">
                                View clip
                              </a>
                            </div>
                            <button
                              className="mt-3 w-full rounded-xl bg-red-600 px-4 py-3 font-black text-white hover:bg-red-700 disabled:bg-emerald-600"
                              type="button"
                              disabled={acknowledgedIds.includes(incident.id)}
                              onClick={async () => {
                                await acknowledgeIncident(incident.id);
                                setAcknowledgedIds((current) => [...current, incident.id]);
                              }}
                            >
                              {acknowledgedIds.includes(incident.id)
                                ? "Alert acknowledged"
                                : "Acknowledge and respond"}
                            </button>
                          </article>
                        ))}
                      </div>
                    </div>
                  )}
                  <p className="mt-5 rounded-xl bg-slate-100 px-4 py-3 text-xs leading-5 text-slate-600">
                    A result does not prove that a person is safe or drowning. Always rely on trained lifeguards and direct observation.
                  </p>
                  <button
                    className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl border border-slate-300 bg-white px-5 py-3.5 font-bold hover:border-ocean-400 hover:text-ocean-700"
                    type="button"
                    onClick={reset}
                  >
                    <RotateCcw size={19} /> Analyse another video
                  </button>
                </div>
              </div>
            ) : null}
          </section>
        </div>
      </main>

      <ProjectFooter />
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/signup" element={<AuthPage mode="signup" />} />
      <Route path="/" element={<RequireAuth><Navigate to="/analyze" replace /></RequireAuth>} />
      <Route path="/analyze" element={<RequireAuth><AnalyzePage /></RequireAuth>} />
      <Route path="/dashboard" element={<RequireAuth><DashboardPage /></RequireAuth>} />
      <Route path="/incidents" element={<RequireAuth><IncidentsPage /></RequireAuth>} />
      <Route path="/live" element={<RequireAuth><LiveMonitoringPage /></RequireAuth>} />
      <Route path="/cameras" element={<RequireAuth><CamerasPage /></RequireAuth>} />
      <Route path="/model" element={<RequireAuth><ModelTrainingPage /></RequireAuth>} />
      <Route path="/documentation" element={<RequireAuth><DocumentationPage /></RequireAuth>} />
      <Route path="*" element={<Navigate to="/analyze" replace />} />
    </Routes>
  );
}

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="grid min-h-screen place-items-center bg-slate-50 font-bold text-slate-600">Checking your account…</div>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}

function playAlertTone() {
  try {
    const audioContext = new window.AudioContext();
    const beepDuration = 0.24;
    const beepInterval = 0.48;

    for (let index = 0; index < 3; index += 1) {
      const startTime = audioContext.currentTime + index * beepInterval;
      const stopTime = startTime + beepDuration;
      const oscillator = audioContext.createOscillator();
      const gain = audioContext.createGain();
      oscillator.type = "square";
      oscillator.frequency.setValueAtTime(880, startTime);
      gain.gain.setValueAtTime(0.14, startTime);
      gain.gain.exponentialRampToValueAtTime(0.001, stopTime);
      oscillator.connect(gain);
      gain.connect(audioContext.destination);
      oscillator.start(startTime);
      oscillator.stop(stopTime);
    }
  } catch {
    // Some browsers block programmatic sound; the visual alert remains visible.
  }
}

function ResultStat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
      <span className="text-ocean-600">{icon}</span>
      <p className="mt-2 text-xl font-black text-slate-950">{value}</p>
      <p className="text-xs font-medium text-slate-500">{label}</p>
    </div>
  );
}
