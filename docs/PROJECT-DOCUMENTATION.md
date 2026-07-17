# AquaGuard AI — Complete Project Documentation

## 1. Project title

**AquaGuard AI: Educational Drowning-Risk Early-Warning System**

Version: 0.1.0 MVP  
Platform: 64-bit Windows 10/11  
Primary language: Python 3.11 and TypeScript  
Application address: `http://127.0.0.1:8000`

**Author and developer:** Danwin Shaju  
**Email:** [danwin212@gmail.com](mailto:danwin212@gmail.com)  
**GitHub:** [github.com/Danwinshaju](https://github.com/Danwinshaju)  
**LinkedIn:** [linkedin.com/in/danwin-shaju](https://www.linkedin.com/in/danwin-shaju/)  
**Copyright:** © 2026 Danwin Shaju. All rights reserved.

## 2. Abstract

AquaGuard AI is a local full-stack computer-vision project that analyses uploaded swimming-pool video, a browser camera, or RTSP/HTTP network-camera streams. The system detects people, maintains tracking identities, measures movement and pose, evaluates explainable temporal risk signals, and presents possible danger alerts to an operator. A confirmed danger event produces an annotated evidence snapshot, a short evidence video, and a MongoDB incident report.

The project is an educational assistance system. It is not certified safety equipment, cannot prove that a person is safe or drowning, and must not replace lifeguards, direct supervision, barriers, alarms, or emergency procedures.

## 3. Objectives

- Accept uploaded MP4, AVI, and MOV video.
- Support browser-camera monitoring through WebSockets.
- Support multiple RTSP/HTTP network cameras with automatic reconnection.
- Detect and track each visible person.
- Measure movement, inactivity, disappearance, vertical change, head visibility, arm movement, and deep-water duration.
- Reduce single-frame false alarms through smoothing and persistence rules.
- Produce clear visual warnings, three alert beeps, and browser vibration where supported.
- Save incident screenshots, short video evidence, risk explanations, status, and operator notes.
- Provide searchable incident management, CSV export, and printable PDF reports.
- Delete incident documents and evidence automatically after 24 hours.
- Require signup/login and prevent cross-account incident or evidence access.

## 4. Technology stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 19, TypeScript | User interface and page components |
| Frontend build | Vite | Development and production frontend builds |
| Styling | Tailwind CSS | Responsive interface styling |
| Frontend data | TanStack React Query | API state and automatic refresh |
| Charts | Recharts | Dashboard alert visualisation |
| Icons | Lucide React | Consistent interface icons |
| Backend | FastAPI | REST API, WebSockets, validation, API documentation |
| Server | Uvicorn | ASGI application server |
| Computer vision | OpenCV | Video decoding, frames, overlays, snapshots, clips |
| Object detection | Ultralytics YOLO11 | Person bounding boxes |
| Custom aquatic detection | Fine-tuned YOLO11 | Drowning, swimming, and out-of-water appearance |
| Pose estimation | YOLO11 Pose | Head, shoulders, hips, wrists, and body geometry |
| Tracking | ByteTrack | Persistent person identity through time |
| Machine learning | PyTorch | Optional LSTM temporal classifier |
| Database | MongoDB 8 | Incidents, notes, status, and camera configuration |
| Account security | MongoDB sessions + Python scrypt | HttpOnly login sessions, salted password hashes, owner isolation |
| User media storage | Browser IndexedDB | Per-account processed videos, snapshots and clips after verified transfer |
| Containers | Docker Desktop | Local MongoDB service |
| Encoding | FFmpeg via imageio-ffmpeg | H.264 browser-compatible video |
| Tests and quality | Pytest, Ruff, Black | Backend verification and formatting |

## 5. Main system architecture

```text
Uploaded video / Browser camera / RTSP camera
                    |
                    v
          FastAPI REST + WebSocket API
                    |
                    v
        YOLO detection and pose estimation
                    |
                    v
             ByteTrack person IDs
                    |
                    v
       Movement + temporal risk signal engine
                    |
           +--------+---------+
           |                  |
           v                  v
 Annotated output       Danger confirmation
                              |
                              v
             Snapshot + clip + MongoDB report
                              |
                              v
             React dashboard and incident UI
```

The React frontend is compiled into `frontend/dist`. FastAPI serves the compiled interface and the API from port 8000. MongoDB runs in Docker and stores users, opaque sessions, incident ownership, and other persistent documents. Generated media begins in temporary server storage. The frontend verifies complete IndexedDB writes before owner-checked release endpoints delete server media. Every incident query and evidence-file lookup requires the signed-in owner's ID; legacy unowned incidents are hidden.

## 6. AI and computer-vision workflow

1. A frame is read from an uploaded file, browser WebSocket, or network stream.
2. YOLO detects objects from the COCO `person` class.
3. ByteTrack associates current boxes with persistent person IDs.
4. The movement analyser calculates speed, displacement, distance, and inactivity.
5. Periodic YOLO pose inference supplies visible landmarks and posture measurements.
6. Pool-zone calibration determines whether the person's centre lies inside the pool and deep-water area.
7. Independent signals evaluate inactivity, sudden downward movement, low movement after intense activity, disappearance, vertical posture, head visibility, irregular arms, and temporal classifier probability.
8. Risk contributions are combined and smoothed for each tracking ID.
9. Danger must remain above the configured threshold for the persistence duration.
10. A confirmed event triggers the operator warning and evidence workflow.

When `backend/models/aquaguard_aquatic_best.pt` exists, the custom dataset model periodically classifies tracked aquatic appearances. A confident Drowning result contributes an explainable risk signal but still passes through risk smoothing, persistence, and human-verification requirements.

### Performance modes

- **Fast:** smaller images and fewer pose checks for responsive CPU operation.
- **Balanced:** recommended default for normal use.
- **Accurate:** larger images and more frequent pose checks for a capable GPU.

### Temporal model

The optional LSTM reads 16 consecutive movement and pose observations. The `/model` page provides a CSV template, local background training, validation metrics, and model readiness. A trained model is only meaningful when it uses large, correctly labelled, diverse datasets and independent test videos.

## 7. Implemented pages and live demonstrations

Start AquaGuard and open these local demonstrations:

| Page | Address | Demonstration |
|---|---|---|
| Uploaded analysis | `http://127.0.0.1:8000/analyze` | Upload, process, track, alert, and review video |
| Live browser camera | `http://127.0.0.1:8000/live` | Real-time boxes, person IDs, zones, risk and alerts |
| Network cameras | `http://127.0.0.1:8000/cameras` | Persistent RTSP/HTTP camera monitoring |
| Dashboard | `http://127.0.0.1:8000/dashboard` | Health, counts, GPU, storage and alert trends |
| Incidents | `http://127.0.0.1:8000/incidents` | Evidence, status, notes, filters, export, deletion |
| Train AI | `http://127.0.0.1:8000/model` | Dataset template, training job and metrics |
| Documentation | `http://127.0.0.1:8000/documentation` | Complete in-app project guide |
| API explorer | `http://127.0.0.1:8000/docs` | Interactive FastAPI endpoint demonstration |

The application redirects unauthenticated visitors to `/login`. New users register at `/signup`. Account sessions use a random opaque token in an HttpOnly, SameSite cookie; production mode also marks the cookie Secure.

### Separate operating guides

- [USER-GUIDE.md](USER-GUIDE.md) contains step-by-step instructions for every page and the normal operating checklist.
- [LIVE-DEMO-GUIDE.md](LIVE-DEMO-GUIDE.md) provides a prepared ten-minute project-presentation sequence.
- [TROUBLESHOOTING-GUIDE.md](TROUBLESHOOTING-GUIDE.md) covers startup, Docker, camera, tracking, video, alert, evidence, and training problems.
- [AQUATIC-MODEL-TRAINING.md](AQUATIC-MODEL-TRAINING.md) audits the supplied Roboflow dataset and provides CPU/GPU training commands.

All three guides can also be downloaded from the **How to use AquaGuard** section on the in-app Documentation page.

## 8. Major features

- Uploaded-video validation and processing progress.
- Real YOLO detection with an optional clearly identified mock/demo mode.
- Browser live camera with backpressure and recovery handling.
- Persistent multi-camera configurations stored in MongoDB.
- ByteTrack with centroid-tracker fallback.
- Direct pool-zone drawing and fine-adjustment sliders.
- Fast, Balanced, and Accurate runtime modes.
- Explainable movement, pose, zone, disappearance, and temporal risk signals.
- Three audible danger beeps and supported-device vibration.
- Labelled evidence snapshots and short H.264 clips.
- Incident acknowledgement, resolution, false-alarm marking, and notes.
- Incident search and status, source, minimum-risk, and date filters.
- CSV export, printable PDF, selected deletion, and delete-all action.
- Automatic incident escalation through optional webhook or email.
- Automatic 24-hour incident document and evidence deletion.
- GPU, database, model, camera, and disk-health reporting.
- Single-command normal startup.

## 9. Normal installation and startup

Required software:

- Python 3.11
- Node.js and npm
- Docker Desktop with WSL 2
- Git and Visual Studio Code are recommended for development

From the project root:

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection"
npm start
```

The launcher starts MongoDB, builds the frontend, and starts Uvicorn. For later starts that reuse the existing frontend build:

```powershell
npm run start:fast
```

## 10. Verification commands

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection"
.\.venv\Scripts\Activate.ps1
cd .\backend
python -m black .
python -m ruff check .
python -m pytest
```

## 11. Important API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Application health |
| GET | `/api/v1/health/database` | MongoDB health |
| GET | `/api/v1/health/system` | GPU, disk, cameras, model, database |
| POST | `/api/v1/videos/upload` | Upload a video |
| POST | `/api/v1/videos/{id}/process` | Start analysis |
| WS | `/api/v1/live/ws` | Browser-camera processing |
| GET/POST | `/api/v1/cameras` | List or register network cameras |
| DELETE | `/api/v1/cameras/{id}` | Remove camera configuration |
| GET | `/api/v1/incidents` | Search/filter incidents |
| POST | `/api/v1/incidents/{id}/release-evidence` | Delete temporary server media after verified browser storage |
| POST | `/api/v1/videos/{id}/release` | Delete temporary uploaded and processed server video |
| PATCH | `/api/v1/incidents/{id}/acknowledge` | Acknowledge incident |
| PATCH | `/api/v1/incidents/{id}/resolve` | Resolve incident |
| PATCH | `/api/v1/incidents/{id}/false-alarm` | Mark false alarm |
| PATCH | `/api/v1/incidents/{id}/notes` | Save notes |
| GET | `/api/v1/incidents/export.csv` | Export CSV |
| DELETE | `/api/v1/incidents` | Delete all incidents and evidence |
| GET | `/api/v1/model/status` | Temporal model readiness |
| POST | `/api/v1/model/train` | Start temporal-model training |

## 12. Data storage and privacy

MongoDB stores accounts, sessions, incident metadata, and persistent camera configuration. The server `storage` directory is temporary working space for uploads, processed outputs, snapshots, and clips. After verified IndexedDB writes, owner-checked release endpoints delete those server files. Failed transfers remain temporarily on the server, and unattended network-camera evidence transfers when its owner opens Incidents. Incident reports and browser media are deleted automatically after 24 hours by default. Training CSV uploads are removed after training completes.

Signup/login and backend owner filters prevent one account from accessing another account's records or server evidence. Browser IndexedDB remains specific to one browser profile and deployment origin, so users must download evidence they need on another device.

## 13. Configuration

Runtime settings are stored in `backend/.env`. Important options include:

- `MOCK_AI=false` for real YOLO instead of demonstration boxes.
- `YOLO_DEVICE=` for automatic CPU/GPU selection, `cpu`, or `cuda:0`.
- `LIVE_USE_BYTETRACK=true` for strong live tracking.
- Risk thresholds, smoothing, persistence, movement and pose intervals.
- `INCIDENT_RETENTION_HOURS=24` for automatic evidence retention.
- Optional webhook and SMTP alert settings.
- Temporal model location, sequence length, threshold, and weight.

Do not change several risk settings at once without measuring the effect on labelled validation videos.

## 14. Troubleshooting

### The website does not open

Keep the startup terminal running and confirm that Uvicorn prints `Application startup complete`. Use `http://127.0.0.1:8000`, not the backend root before the frontend is built.

### Docker or MongoDB fails

Open Docker Desktop, wait until the engine is running, then restart AquaGuard. Confirm `docker compose version` works.

### The camera is black or permission remains pending

Allow camera permission using the browser address-bar icon. Close applications that may already be using the camera and press **Retry live camera**.

### Tracking freezes or is too slow

Select Fast mode, stop unused network cameras, close other video programs, and consider GPU acceleration.

### Only demonstration boxes appear

Set `MOCK_AI=false` in `backend/.env`, confirm `backend/yolo11n.pt` and `backend/yolo11n-pose.pt` exist, then restart AquaGuard.

### No drowning warning appears

The system does not alert merely because a person is present. Risk must exceed thresholds for the persistence duration. Confirm the pool zone covers the swimmer and observe the live risk score. Never lower thresholds solely to force a demonstration without documenting that change.

## 15. Testing and evaluation

Software tests verify endpoints, video validation, tracking utilities, risk behaviour, evidence handling, retention, and processing workflows. AI safety evaluation additionally requires independently labelled video that includes normal swimming, floating, playing, splashing, partial occlusion, reflections, empty pools, different body types, lighting changes, camera angles, and professionally supervised staged emergencies.

Report accuracy, precision, recall, F1, false-positive rate, missed-event rate, alert delay, processing FPS, and performance by camera/environment. Do not report training-set accuracy as real-world safety performance.

## 16. Limitations and future work

- Detection can fail with occlusion, glare, distance, darkness, poor positioning, network loss, or hardware overload.
- Similar-looking people may exchange tracking identities during complex overlap.
- Risk rules and the optional temporal model require formal validation for each pool and camera environment.
- Browser sound can be blocked until the user interacts with the page.
- A local in-memory processing job is not a distributed production worker queue.
- A production system needs authentication, encryption, audit controls, redundant cameras/network/power, monitoring, certified installation, and formal emergency integration.
- The recommended next engineering stage is a recorded-data labelling interface and independent evaluation report based on real safety-reviewed footage.

## 17. Conclusion

AquaGuard AI demonstrates a complete full-stack computer-vision application: multiple video inputs, detection, tracking, movement and pose analysis, temporal risk scoring, live operator warnings, evidence management, reporting, health monitoring, and model training. Its responsible use is as an educational early-warning prototype under continuous human supervision—not as a replacement for qualified pool-safety personnel.
