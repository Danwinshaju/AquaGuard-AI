import {
  AlertTriangle,
  BookOpen,
  BrainCircuit,
  Camera,
  CheckCircle2,
  Cctv,
  Database,
  Download,
  FileText,
  FileVideo2,
  Gauge,
  GitBranch,
  Github,
  HardDrive,
  Linkedin,
  Mail,
  MonitorPlay,
  Network,
  Printer,
  Server,
  ShieldAlert,
  Terminal,
  Wrench,
} from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { AppShell } from "../components/AppShell";

const technologies = [
  ["React 19 + TypeScript", "User interface, routing, forms, live status and incident review."],
  ["Vite + Tailwind CSS", "Frontend build system and responsive visual styling."],
  ["FastAPI + Uvicorn", "Python API, WebSockets, video endpoints and frontend hosting."],
  ["Python 3.11", "Computer-vision, risk analysis, evidence and backend services."],
  ["OpenCV", "Video decoding, frame annotation, snapshots and evidence clips."],
  ["Ultralytics YOLO11", "Person detection and human-pose landmark estimation."],
  ["ByteTrack", "Persistent person IDs through movement and short occlusion."],
  ["PyTorch LSTM", "Optional temporal classifier for movement/pose sequences."],
  ["MongoDB 8", "Camera configurations, incident reports, status and operator notes."],
  ["Docker Desktop", "Runs the local MongoDB database consistently on Windows."],
  ["FFmpeg", "Creates H.264 browser-compatible processed videos and evidence clips."],
  ["React Query + Recharts", "API state, automatic refresh and dashboard visualisation."],
] as const;

const apiEndpoints = [
  ["GET", "/api/v1/health", "Application health"],
  ["GET", "/api/v1/health/database", "MongoDB connection"],
  ["GET", "/api/v1/health/system", "GPU, storage, model and camera health"],
  ["POST", "/api/v1/videos/upload", "Upload MP4, AVI or MOV"],
  ["POST", "/api/v1/videos/{id}/process", "Start uploaded-video analysis"],
  ["WS", "/api/v1/live/ws", "Browser-camera frames and tracked output"],
  ["GET/POST", "/api/v1/cameras", "List or register network cameras"],
  ["GET", "/api/v1/incidents", "Search and filter incident reports"],
  ["POST", "/api/v1/incidents/{id}/release-evidence", "Release server media after browser storage"],
  ["PATCH", "/api/v1/incidents/{id}/notes", "Save operator notes"],
  ["GET", "/api/v1/incidents/export.csv", "Export incident report data"],
  ["POST", "/api/v1/model/train", "Train the optional temporal model"],
] as const;

export function DocumentationPage() {
  return (
    <AppShell>
      <section className="rounded-3xl bg-gradient-to-br from-slate-950 via-ocean-950 to-ocean-800 p-7 text-white shadow-xl sm:p-10">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="max-w-3xl">
            <p className="flex items-center gap-2 text-sm font-black uppercase tracking-[0.18em] text-cyan-300">
              <BookOpen size={19} /> Complete project guide
            </p>
            <h1 className="mt-4 text-4xl font-black tracking-tight sm:text-5xl">AquaGuard AI Documentation</h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-200">
              A local educational drowning-risk early-warning application for uploaded video,
              browser cameras and RTSP/HTTP cameras. This page explains how the complete system
              works, how to demonstrate it and how to run it safely.
            </p>
          </div>
          <button className="flex items-center gap-2 rounded-xl bg-white px-5 py-3 font-black text-slate-950 hover:bg-cyan-50" type="button" onClick={() => window.print()}>
            <Printer size={19} /> Print / Save PDF
          </button>
        </div>
        <div className="mt-7 flex flex-wrap gap-3 text-sm font-bold">
          <Badge>Version 0.1.0 MVP</Badge><Badge>Local-first</Badge><Badge>Windows + Python 3.11</Badge><Badge>Educational use</Badge>
        </div>
      </section>

      <section className="mt-6 rounded-2xl border-2 border-amber-300 bg-amber-50 p-5 text-amber-950" id="safety">
        <div className="flex gap-4">
          <AlertTriangle className="shrink-0 text-amber-700" size={27} />
          <div><h2 className="text-lg font-black">Critical safety limitation</h2><p className="mt-1 leading-6">AquaGuard is not a certified safety device and cannot determine with certainty that a person is drowning or safe. Detection may be wrong, late or interrupted. Always maintain direct supervision, trained lifeguards, physical barriers and an established emergency-response procedure.</p></div>
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm" id="author">
        <p className="text-xs font-black uppercase tracking-[0.16em] text-ocean-600">Project author and developer</p>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-5">
          <div><h2 className="text-2xl font-black">Danwin Shaju</h2><p className="mt-1 text-sm text-slate-500">Creator and developer of AquaGuard AI</p><p className="mt-2 text-xs font-semibold text-slate-500">© {new Date().getFullYear()} Danwin Shaju. All rights reserved.</p></div>
          <div className="flex flex-wrap gap-2">
            <a className="flex items-center gap-2 rounded-xl bg-ocean-600 px-4 py-2.5 font-bold text-white hover:bg-ocean-700" href="mailto:danwin212@gmail.com"><Mail size={18} /> danwin212@gmail.com</a>
            <a className="flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 font-bold text-white hover:bg-slate-700" href="https://github.com/Danwinshaju" target="_blank" rel="noreferrer"><Github size={18} /> GitHub</a>
            <a className="flex items-center gap-2 rounded-xl bg-blue-700 px-4 py-2.5 font-bold text-white hover:bg-blue-800" href="https://www.linkedin.com/in/danwin-shaju/" target="_blank" rel="noreferrer"><Linkedin size={18} /> LinkedIn</a>
          </div>
        </div>
      </section>

      <div className="mt-8 grid items-start gap-8 lg:grid-cols-[250px_1fr]">
        <aside className="rounded-2xl border border-slate-200 bg-white p-5 lg:sticky lg:top-5 print:hidden">
          <p className="font-black">On this page</p>
          <nav className="mt-3 grid gap-1 text-sm font-semibold text-slate-600">
            {[["#demos", "Live demonstrations"], ["#usage", "How to use the app"], ["#overview", "System overview"], ["#technology", "Technology stack"], ["#architecture", "Architecture"], ["#ai", "AI detection workflow"], ["#features", "Features"], ["#run", "Run and verify"], ["#api", "API reference"], ["#data", "Data and retention"], ["#troubleshooting", "Troubleshooting"]].map(([href, label]) => <a className="rounded-lg px-3 py-2 hover:bg-slate-100 hover:text-ocean-700" href={href} key={href}>{label}</a>)}
          </nav>
        </aside>

        <div className="min-w-0 space-y-9">
          <DocSection id="demos" icon={<MonitorPlay />} title="Live demonstrations">
            <p className="text-slate-600">Use these working pages during your project demonstration. Start AquaGuard first, then open each demo in the same browser.</p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              <DemoLink to="/analyze" icon={<FileVideo2 />} title="Uploaded video" text="Upload a pool video, track people and review labelled results." />
              <DemoLink to="/live" icon={<Camera />} title="Browser live camera" text="Real-time boxes, person IDs, risk status, zones and audible alerts." />
              <DemoLink to="/cameras" icon={<Cctv />} title="Network cameras" text="Register persistent RTSP/HTTP sources and view AI output." />
              <DemoLink to="/dashboard" icon={<Gauge />} title="Dashboard" text="System health, incident counts, GPU and alert trends." />
              <DemoLink to="/incidents" icon={<ShieldAlert />} title="Incident evidence" text="Snapshots, short clips, notes, filters, CSV and PDF reports." />
              <DemoLink to="/model" icon={<BrainCircuit />} title="Train temporal AI" text="Download the dataset template and review training metrics." />
            </div>
            <a className="mt-4 inline-flex items-center gap-2 rounded-xl border border-slate-300 px-4 py-2 font-bold text-slate-700 hover:border-ocean-400" href="/docs" target="_blank" rel="noreferrer"><Network size={18} /> Open interactive API demo</a>
          </DocSection>

          <DocSection id="usage" icon={<BookOpen />} title="How to use AquaGuard">
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-950"><strong>Before using AI monitoring:</strong> maintain direct supervision, confirm a trained lifeguard is responsible for response, and treat every warning as a request for human verification.</div>
            <ol className="mt-5 grid gap-4 sm:grid-cols-2">
              <Step number="1" title="Start the system" text="Open Docker Desktop, run npm start from the project root, keep the terminal open and visit 127.0.0.1:8000." />
              <Step number="2" title="Choose an input" text="Use Analyse for a recorded video, Live for this computer's camera, or Cameras for an RTSP/HTTP stream." />
              <Step number="3" title="Calibrate and check" text="Draw the pool zone, choose a performance mode and confirm tracking boxes follow the visible people." />
              <Step number="4" title="Monitor the output" text="Watch person IDs, risk status, processing FPS and visual warnings while maintaining direct observation." />
              <Step number="5" title="Respond to alerts" text="Verify immediately, alert a trained lifeguard and follow the emergency plan without delaying to inspect the software." />
              <Step number="6" title="Review your incidents" text="Evidence moves into your browser storage; your account can only inspect, update, export, or delete its own reports." />
            </ol>
            <h3 className="mt-6 text-lg font-black">Separate instruction files</h3>
            <p className="mt-1 text-sm text-slate-600">Download the guide you need and open it with VS Code, Notepad, Word, or a Markdown viewer.</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <GuideDownload href="/api/v1/documentation/user-guide" title="Complete User Guide" text="Step-by-step instructions for every AquaGuard page and normal operating checklist." />
              <GuideDownload href="/api/v1/documentation/live-demo-guide" title="Live Demo Guide" text="A prepared ten-minute presentation order with demonstration rules and local links." />
              <GuideDownload href="/api/v1/documentation/troubleshooting-guide" title="Troubleshooting Guide" text="Common startup, Docker, camera, tracking, alert, video and training solutions." />
              <GuideDownload href="/api/v1/documentation/aquatic-model-training" title="Aquatic YOLO Training" text="Dataset audit, CPU/GPU commands, outputs, integration and responsible evaluation." />
            </div>
          </DocSection>

          <DocSection id="overview" icon={<FileText />} title="Project overview">
            <p className="leading-7 text-slate-600">AquaGuard accepts video frames, detects people, maintains an identity for each person, measures movement and pose, combines explainable risk signals over time and produces an operator warning only after the configured persistence rules are satisfied. Confirmed danger events create a labelled snapshot, a short video clip and a MongoDB incident report.</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-3"><MiniCard title="Inputs" text="Uploaded MP4/AVI/MOV, browser webcam, RTSP or HTTP stream." /><MiniCard title="Processing" text="YOLO, ByteTrack, pose, movement, temporal rules and risk smoothing." /><MiniCard title="Outputs" text="Tracked video, warning state, three beeps, evidence and reports." /></div>
          </DocSection>

          <DocSection id="technology" icon={<Wrench />} title="Technology stack">
            <div className="grid gap-3 sm:grid-cols-2">{technologies.map(([name, purpose]) => <div className="rounded-xl border border-slate-200 bg-white p-4" key={name}><p className="font-black text-slate-950">{name}</p><p className="mt-1 text-sm leading-6 text-slate-600">{purpose}</p></div>)}</div>
          </DocSection>

          <DocSection id="architecture" icon={<GitBranch />} title="System architecture">
            <div className="overflow-x-auto rounded-2xl bg-slate-950 p-5 text-sm font-bold text-slate-100">
              <div className="flex min-w-[680px] items-center justify-between gap-3 text-center">
                <FlowBox icon={<Camera />} label="Video sources" /><Arrow /><FlowBox icon={<Server />} label="FastAPI + WebSocket" /><Arrow /><FlowBox icon={<BrainCircuit />} label="Detection + tracking + risk" /><Arrow /><FlowBox icon={<Database />} label="MongoDB + evidence" /><Arrow /><FlowBox icon={<MonitorPlay />} label="React operator UI" />
              </div>
            </div>
            <ul className="mt-5 list-disc space-y-2 pl-6 text-slate-600"><li>The React frontend and FastAPI backend use the same local address: <code>127.0.0.1:8000</code>.</li><li>Browser-camera frames travel through a WebSocket and annotated JPEG frames return to the page.</li><li>Network cameras run independent backend AI sessions with automatic reconnection.</li><li>MongoDB stores account and report metadata; processed media moves from temporary server files into the owner's browser IndexedDB.</li></ul>
          </DocSection>

          <DocSection id="ai" icon={<BrainCircuit />} title="AI detection and risk workflow">
            <ol className="grid gap-4 sm:grid-cols-2">
              <Step number="1" title="Detect people" text="YOLO11 retains the person class and returns bounding boxes with confidence." />
              <Step number="2" title="Maintain identities" text="ByteTrack assigns persistent person IDs through movement and short occlusion." />
              <Step number="3" title="Measure behaviour" text="Movement, inactivity, vertical change, disappearance, head visibility and arm motion are evaluated." />
              <Step number="4" title="Apply pool calibration" text="Only people inside the drawn pool zone enter risk analysis; deep-water duration adds context." />
              <Step number="5" title="Score over time" text="Independent signal contributions are smoothed. Optional LSTM output adds temporal evidence." />
              <Step number="6" title="Warn and save evidence" text="Persistent danger produces visual/audio alerts, a snapshot, evidence clip and incident report." />
            </ol>
            <div className="mt-5 rounded-xl bg-violet-50 p-4 text-sm leading-6 text-violet-950"><strong>Performance profiles:</strong> Fast uses smaller inputs and fewer pose checks; Balanced is recommended for normal CPU use; Accurate uses larger inputs and more pose checks for a capable GPU.</div>
          </DocSection>

          <DocSection id="features" icon={<CheckCircle2 />} title="Implemented features">
            <div className="grid gap-x-8 gap-y-3 sm:grid-cols-2">{["Private signup, login and logout", "Owner-isolated incidents, evidence and cameras", "Per-account browser IndexedDB media", "Verified transfer before server-file release", "Uploaded-video analysis with processing progress", "Browser live camera and tracked AI output", "Persistent RTSP/HTTP camera registrations", "Direct-on-video pool-zone drawing", "Fast, Balanced and Accurate modes", "YOLO person and pose analysis", "ByteTrack person identity tracking", "Explainable temporal risk signals", "Optional locally trained LSTM classifier", "Three-beep danger alert and browser vibration", "Evidence snapshot and short H.264 clip", "MongoDB incident lifecycle and notes", "Search, status, risk, source and date filters", "CSV export and printable PDF reports", "Select/delete selected/delete all incidents", "Automatic 24-hour evidence deletion", "Webhook/email alert delivery and escalation", "Dashboard GPU, storage and database health", "Single-command normal startup"].map((feature) => <p className="flex gap-2 text-sm font-semibold text-slate-700" key={feature}><CheckCircle2 className="mt-0.5 shrink-0 text-emerald-600" size={18} />{feature}</p>)}</div>
          </DocSection>

          <DocSection id="run" icon={<Terminal />} title="Run and verify the project">
            <p className="text-slate-600">Open Docker Desktop, then use PowerShell in the project root.</p>
            <CodeBlock>{`cd "C:\\Users\\ELCOT\\OneDrive - ELCOT\\Documents\\AI Drowning Detection"\nnpm start`}</CodeBlock>
            <p className="mt-4 text-slate-600">For a faster restart that reuses the compiled frontend:</p><CodeBlock>{`npm run start:fast`}</CodeBlock>
            <p className="mt-4 text-slate-600">Development verification:</p><CodeBlock>{`.\\.venv\\Scripts\\Activate.ps1\ncd .\\backend\npython -m black .\npython -m ruff check .\npython -m pytest`}</CodeBlock>
          </DocSection>

          <DocSection id="api" icon={<Network />} title="Important API endpoints">
            <div className="overflow-x-auto"><table className="w-full min-w-[650px] border-collapse text-left text-sm"><thead><tr className="bg-slate-900 text-white"><th className="p-3">Method</th><th className="p-3">Endpoint</th><th className="p-3">Purpose</th></tr></thead><tbody>{apiEndpoints.map(([method, path, purpose]) => <tr className="border-b border-slate-200" key={path}><td className="p-3 font-black text-ocean-700">{method}</td><td className="p-3 font-mono text-xs">{path}</td><td className="p-3 text-slate-600">{purpose}</td></tr>)}</tbody></table></div>
          </DocSection>

          <DocSection id="data" icon={<HardDrive />} title="Data storage and retention">
            <div className="grid gap-4 sm:grid-cols-2"><MiniCard title="MongoDB" text="Accounts, sessions, incident metadata, lifecycle status, notes and camera configurations." /><MiniCard title="User browser storage" text="IndexedDB receives processed videos, snapshots and clips before temporary server copies are deleted." /></div>
            <p className="mt-4 leading-7 text-slate-600">Incident records, snapshots and clips are automatically deleted after 24 hours by default. Operators can delete one, selected, or all incidents earlier. Uploaded training CSV files are removed when their training job finishes.</p>
          </DocSection>

          <DocSection id="troubleshooting" icon={<Wrench />} title="Troubleshooting">
            <div className="space-y-3"><Trouble title="127.0.0.1:8000 does not open" text="Keep the npm start terminal running. Check that Uvicorn says Application startup complete." /><Trouble title="MongoDB or Docker error" text="Open Docker Desktop and wait for Engine running, then run npm start again." /><Trouble title="Camera permission is stuck" text="Allow camera access from the browser address-bar icon, close other camera applications and select Retry live camera." /><Trouble title="Tracking freezes" text="Select Fast mode, stop unused network cameras and close other video programs." /><Trouble title="No real boxes are shown" text="Set MOCK_AI=false in backend/.env and confirm yolo11n.pt and yolo11n-pose.pt exist in backend." /><Trouble title="No alert is produced" text="A danger alert needs persistent risk, not simply a visible person. Calibrate the pool zone and verify live risk values." /></div>
          </DocSection>

          <section className="rounded-2xl border border-slate-200 bg-slate-100 p-6 text-sm leading-6 text-slate-600">
            <p className="font-black text-slate-900">Project conclusion</p><p className="mt-2">AquaGuard demonstrates a complete local full-stack computer-vision workflow: capture, detection, tracking, temporal risk analysis, operator alerts, evidence management, reporting and system-health monitoring. A real-world safety deployment would additionally require certified hardware, formal dataset governance, independent validation, measured false-alarm/missed-event rates, redundancy, privacy controls and trained human response.</p>
          </section>
        </div>
      </div>
    </AppShell>
  );
}

function DocSection({ id, icon, title, children }: { id: string; icon: ReactNode; title: string; children: ReactNode }) { return <section className="scroll-mt-5" id={id}><div className="mb-4 flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-ocean-100 text-ocean-700">{icon}</span><h2 className="text-2xl font-black">{title}</h2></div>{children}</section>; }
function Badge({ children }: { children: ReactNode }) { return <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1.5">{children}</span>; }
function DemoLink({ to, icon, title, text }: { to: string; icon: ReactNode; title: string; text: string }) { return <Link className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-ocean-400 hover:shadow-md" to={to}><span className="text-ocean-600">{icon}</span><p className="mt-3 font-black group-hover:text-ocean-700">{title}</p><p className="mt-1 text-sm leading-6 text-slate-600">{text}</p><span className="mt-3 inline-block text-sm font-black text-ocean-700">Open demo →</span></Link>; }
function MiniCard({ title, text }: { title: string; text: string }) { return <div className="rounded-xl border border-slate-200 bg-white p-4"><p className="font-black">{title}</p><p className="mt-1 text-sm leading-6 text-slate-600">{text}</p></div>; }
function Step({ number, title, text }: { number: string; title: string; text: string }) { return <li className="flex gap-4 rounded-xl border border-slate-200 bg-white p-4"><span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ocean-600 font-black text-white">{number}</span><div><p className="font-black">{title}</p><p className="mt-1 text-sm leading-6 text-slate-600">{text}</p></div></li>; }
function FlowBox({ icon, label }: { icon: ReactNode; label: string }) { return <div className="flex min-h-28 w-28 shrink-0 flex-col items-center justify-center gap-2 rounded-xl border border-cyan-700 bg-slate-900 p-3 text-cyan-100">{icon}<span>{label}</span></div>; }
function Arrow() { return <span className="text-2xl text-cyan-400">→</span>; }
function CodeBlock({ children }: { children: string }) { return <pre className="mt-3 overflow-x-auto rounded-xl bg-slate-950 p-4 text-sm leading-6 text-cyan-100"><code>{children}</code></pre>; }
function Trouble({ title, text }: { title: string; text: string }) { return <details className="rounded-xl border border-slate-200 bg-white p-4"><summary className="cursor-pointer font-black">{title}</summary><p className="mt-3 text-sm leading-6 text-slate-600">{text}</p></details>; }
function GuideDownload({ href, title, text }: { href: string; title: string; text: string }) { return <a className="rounded-xl border border-slate-200 bg-white p-4 transition hover:border-ocean-400 hover:shadow-sm" href={href}><Download className="text-ocean-600" size={22} /><p className="mt-3 font-black text-slate-900">{title}</p><p className="mt-1 text-sm leading-6 text-slate-600">{text}</p><span className="mt-3 inline-block text-sm font-black text-ocean-700">Download Markdown →</span></a>; }
