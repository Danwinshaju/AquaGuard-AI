# AquaGuard AI

Created and developed by **Danwin Shaju**.

- Email: [danwin212@gmail.com](mailto:danwin212@gmail.com)
- GitHub: [github.com/Danwinshaju](https://github.com/Danwinshaju)
- LinkedIn: [linkedin.com/in/danwin-shaju](https://www.linkedin.com/in/danwin-shaju/)

© 2026 Danwin Shaju. All rights reserved.

## Run the complete application with one command

Open a terminal in the project root and run:

```powershell
npm start
```

This single command starts the MongoDB container, builds the React frontend, and starts Uvicorn. FastAPI serves both the API and built frontend from `http://127.0.0.1:8000`. Press `Ctrl+C` to stop Uvicorn. After the first successful build, `npm run start:fast` can reuse the existing frontend build and start more quickly.

The first browser screen is now **Create account / Log in**. Every incident, evidence file, report export, dashboard total, and saved network camera is associated with the signed-in account. One user cannot list, open, update, export, or delete another user's incidents. Existing incident records created before accounts were introduced remain unowned and are intentionally hidden.

> **Safety notice:** AquaGuard AI is an educational early-warning project. It is not a certified safety device and must never replace trained lifeguards, supervision, barriers, alarms, or emergency procedures.

AquaGuard AI will accept swimming-pool video, track people, estimate risk from behaviour over time, and present possible incidents in a web dashboard.

Complete project documentation is available in [docs/PROJECT-DOCUMENTATION.md](docs/PROJECT-DOCUMENTATION.md) and inside the running application at `http://127.0.0.1:8000/documentation`.

Operating instructions are separated into [USER-GUIDE.md](docs/USER-GUIDE.md), [LIVE-DEMO-GUIDE.md](docs/LIVE-DEMO-GUIDE.md), and [TROUBLESHOOTING-GUIDE.md](docs/TROUBLESHOOTING-GUIDE.md). They can also be downloaded from the in-app Documentation page.

Custom aquatic YOLO training for the Swimming and Drowning Detection dataset is documented in [AQUATIC-MODEL-TRAINING.md](docs/AQUATIC-MODEL-TRAINING.md).

## Current capabilities

AquaGuard supports private user accounts, owner-isolated incidents and cameras, uploaded video, browser live camera, persistent multi-camera RTSP/HTTP ingestion, ByteTrack identity tracking, visual pool-zone drawing, Fast/Balanced/Accurate live modes, YOLO pose signals, in-app temporal-model training, searchable incident notes and CSV/PDF reports, webhook/email escalation, dashboard health monitoring, GPU selection, and automatic 24-hour evidence deletion. See `docs/production-features.md` for configuration and limitations.

## What you need

Install these tools before Stage 2:

1. [Visual Studio Code](https://code.visualstudio.com/)
2. [Git](https://git-scm.com/download/win)
3. [Python 3.11](https://www.python.org/downloads/) (use 3.11 for broad AI-library compatibility)
4. [Node.js LTS](https://nodejs.org/)
5. [Docker Desktop](https://www.docker.com/products/docker-desktop/) (MongoDB will run in Docker later)

During Python installation, select **Add Python to PATH**. Restart PowerShell after installing tools.

Recommended VS Code extensions:

- Python (Microsoft)
- Pylance (Microsoft)
- ESLint (Microsoft)
- Prettier (Prettier)
- Docker (Microsoft)

## Open the project in VS Code

Open PowerShell and run:

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection"
code .
```

If `code` is not recognised, open VS Code, choose **File > Open Folder**, and select this project folder.

In VS Code, open a terminal with **Terminal > New Terminal**. Confirm the tools that are already available:

```powershell
git --version
python --version
node --version
npm --version
docker --version
```

It is okay if Docker is installed but not running during Stage 1.

## Repository map

```text
AI Drowning Detection/
|-- backend/                 Python API and computer-vision code
|   |-- app/                 Application source package
|   |   |-- api/             FastAPI routes and WebSockets
|   |   |-- core/            Settings, security, logging and errors
|   |   |-- db/              MongoDB connection and repositories
|   |   |-- models/          Database document models
|   |   |-- schemas/         Pydantic request/response schemas
|   |   |-- services/        Application workflows
|   |   `-- vision/          Detection, tracking and risk analysis
|   `-- tests/               Backend unit and API tests
|-- frontend/                React and TypeScript web application
|   |-- public/              Static files copied as-is
|   `-- src/
|       |-- api/             Typed backend client
|       |-- components/      Reusable UI components
|       |-- features/        Feature-specific UI and state
|       |-- hooks/           Shared React hooks
|       |-- layouts/         Sidebar/header page layouts
|       |-- pages/           Route-level screens
|       |-- routes/          Router and route guards
|       `-- types/           Shared TypeScript domain types
|-- docs/                    Architecture and learning notes
|-- infrastructure/          Deployment and monitoring configuration
|-- scripts/                 Development helper scripts
|-- storage/                 Local videos and incident media (ignored by Git)
|-- .env.example             Safe environment-variable template
|-- .gitignore               Files Git must not track
`-- docker-compose.yml       Added in Stage 15
```

Folders contain small README files for now so Git can track the intended architecture. They will be replaced or expanded stage by stage.

## Architecture

Read [docs/architecture.md](docs/architecture.md) for the system flow, boundaries, planned database collections, risk engine contract, and stage plan.

## Stage 1 verification

From the project root, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-stage1.ps1
git status --short
```

The verification script should finish with `Stage 1 structure is valid.` Git should list the newly created files.

## Stage 2 setup and run

Run every command below from the project root in the VS Code PowerShell terminal.

Create an isolated Python 3.11 environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

The prompt should start with `(.venv)` and Python should report version 3.11. Install the backend packages:

```powershell
python -m pip install --upgrade pip
python -m pip install -r .\backend\requirements-dev.txt
```

Create the local settings file:

```powershell
Copy-Item .\backend\.env.example .\backend\.env
```

Start MongoDB in Docker:

```powershell
docker compose up -d mongodb
docker compose ps
```

Run the API from the backend folder:

```powershell
cd .\backend
python -m uvicorn app.main:app --reload
```

Keep that terminal running. Open another VS Code terminal and test:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health/database
```

Interactive API documentation is available at <http://127.0.0.1:8000/docs>. Stop the server by clicking its terminal and pressing `Ctrl+C`.

Run automated checks from the backend folder with the virtual environment active:

```powershell
python -m pytest
python -m ruff check .
python -m black --check .
```

## Stage 3: upload a video

With MongoDB and the backend already running, open <http://127.0.0.1:8000/docs>. Expand `POST /api/v1/videos/upload`, choose **Try it out**, select an MP4, AVI, or MOV file, and choose **Execute**.

The backend verifies the extension, declared MIME type, actual container signature, non-empty content, and configured 500 MB limit. It streams the upload in chunks, generates a UUID filename, and stores it under `storage/uploads`.

You may also upload from a second PowerShell terminal:

```powershell
curl.exe -X POST -F "file=@C:\path\to\your\pool-video.mp4" "http://127.0.0.1:8000/api/v1/videos/upload"
```

Run Stage 3 checks from `backend` with the virtual environment active:

```powershell
python -m pytest
python -m ruff check .
python -m black --check .
```

## Stage 4: process an uploaded video

Upload a video through the API documentation and copy the `id` from its response. Then call the processing endpoint in PowerShell:

```powershell
$videoId = "paste-the-upload-id-here"
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/v1/videos/$videoId/process"
```

Open the processed result in a browser:

```text
http://127.0.0.1:8000/api/v1/videos/PASTE-ID-HERE/processed
```

The Stage 4 output displays an educational AquaGuard label, frame number, and lifeguard warning. It does not detect people yet; YOLO is Stage 5.

## Stage 5: person detection

The default `MOCK_AI=true` setting draws one predictable demonstration person box per frame. This lets the entire workflow run quickly without a GPU and is clearly reported as `detection_mode: mock`.

To use real YOLO, stop the backend, edit `backend/.env`, and change:

```text
MOCK_AI=false
```

Restart the backend and process a newly uploaded video. On the first real-YOLO run, Ultralytics downloads the small `yolo11n.pt` pretrained model. CPU processing works but can be slow; a compatible GPU improves speed. YOLO retains only the `person` class and draws the confidence beside each box.

## Stage 6: persistent tracking IDs

Every detected person is matched to the nearest existing track within the configured distance. A track survives a short detection gap and is removed after `TRACKER_MAX_MISSED_FRAMES`. Output labels now show `PERSON ID 1`, `PERSON ID 2`, and so on. The API response reports `unique_people_tracked`.

This centroid tracker is intentionally understandable and lightweight. It can lose identity when people cross or move very quickly; a production version can replace it with ByteTrack or BoT-SORT behind the same tracking boundary.

### One-command Windows setup through Stage 6

From the project root, run the reusable setup file:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-stage6.ps1
```

The script creates/reuses `.venv`, installs official CPU-only PyTorch and all backend packages, creates `backend/.env` when missing, starts MongoDB, and prints installed AI versions.

## Stage 7: movement and inactivity

For each tracking ID, the backend measures the bounding-box centre, displacement from the previous visible frame, speed in pixels per second, total travelled distance, and seconds since significant movement. Movement of at least `MOVEMENT_THRESHOLD_PIXELS` resets that person's inactivity timer. Each person's state is independent.

The processed video shows `Move` and `Inactive` values below every box. Green means movement is below the configured inactivity duration; amber means the inactivity duration reached `INACTIVITY_WARNING_SECONDS`. These measurements are signals only and do not declare drowning. Risk scoring and temporal safety statuses begin in Stage 8.

## Stage 8: risk engine

Eight independent signal modules return a triggered state, confidence, risk contribution, and explanation. Available movement and bounding-box signals work now. Head visibility and irregular arm movement explicitly return unavailable results until pose estimation arrives in Stage 13. Deep-zone and disappearance modules are ready for zone and missing-track context in later stages.

Scores are smoothed per tracking ID. Below 40 is SAFE, 40–69 is WARNING, and 70 or higher remains WARNING until it persists continuously for three seconds; only then does it become DANGER. A score drop resets the danger timer.

## Stage 9: incident evidence

When a person's status first becomes DANGER, AquaGuard saves one annotated JPEG snapshot and a short sampled MP4 clip under `storage/incidents`. It writes an `unresolved` incident document to MongoDB with the video ID, tracking ID, score, timestamp, triggered explanations, evidence filenames, and created/updated timestamps. Duplicate danger frames for the same track do not create duplicate incidents during one processing run.

Sustained inactivity now contributes up to 80 configurable points, while smoothing and the continuous three-second DANGER requirement still apply. A confirmed event produces a pulsing red **Possible drowning behaviour** alert, a warning tone where the browser permits it, an embedded evidence snapshot and clip, emergency-response reminders, and an acknowledgement action saved to MongoDB. This is an assistance alert, never a diagnosis.

Established tracks that disappear are now retained for at least the danger-verification window and evaluated with an 80-point disappearance signal. Confirmed DANGER frames contain a large red `POSSIBLE DROWNING - VERIFY NOW` banner even when the person is no longer visible.

During processed-video playback, the interface compares the player's current time with each incident timestamp. It plays three alert beeps exactly when playback reaches a recorded incident, once per incident. Seeking to a time before the incident resets that playback alert so it can sound again.

## Stage 11: real processing progress

The friendly interface starts video work as an in-memory background job. OpenCV reports actual frames completed, and a WebSocket streams progress to the browser four times per second. The page now displays a real percentage while YOLO, overlays, evidence, and H.264 encoding run. Jobs are intentionally in-memory for the local MVP; a production deployment should use a durable worker queue.

## Stage 12: dashboard and incident review

The React application has `/dashboard`, `/analyze`, `/live`, and `/incidents` routes. Dashboard cards and a Recharts alert-by-day chart use MongoDB incident data. The incident page embeds snapshots and clips and provides acknowledgement, resolution, and false-alarm actions. The live page provides browser-camera tracking and live occupancy.

## Stage 13: YOLO pose estimation

When real YOLO mode is enabled, AquaGuard runs `yolo11n-pose.pt` every six frames and associates pose boxes with existing tracking IDs. Nose confidence supplies head visibility, shoulder-to-hip geometry supplies vertical orientation, and normalized wrist displacement supplies irregular-arm confidence. Visible landmarks and a compact skeleton are drawn on the output. Pose measurements replace the earlier explicit unavailable states in their independent risk signals.

## Live browser camera

The `/live` page requests browser camera permission and sends compressed JPEG frames through `/api/v1/live/ws`. The backend retains YOLO detection, tracking, movement, pose, and risk state for that WebSocket session and returns annotated JPEG frames. Confirmed live DANGER produces the same red warning and three-beep alert. Uploaded-video analysis remains available at `/analyze`.

Live monitoring uses a balanced high-sensitivity profile: 512-pixel person detection on every received frame, 416-pixel periodic pose checks, lower confidence for partially visible people, longer track retention, adaptive browser backpressure, and a 20-second recovery timeout. These `LIVE_*` values can be tuned in `backend/.env` without changing uploaded-video analysis.

When live monitoring confirms DANGER, it keeps a rolling annotated-frame buffer, creates a labelled snapshot and browser-compatible MP4 evidence clip, and saves a `live_camera` incident in MongoDB. New evidence appears immediately on `/live` and remains available with its triggered risk signals and response actions on `/incidents`. A per-person cooldown prevents the same continuing danger from flooding the incident list.

Incident retention defaults to 24 hours. A background task starts with FastAPI, checks every five minutes, deletes each expired snapshot and clip, and then removes its MongoDB document. Operators can also permanently delete an incident immediately from `/incidents`. Configure this with `INCIDENT_RETENTION_HOURS` and `INCIDENT_CLEANUP_INTERVAL_SECONDS` in `backend/.env`.

## Browser-compatible result videos

OpenCV first writes annotated frames to an intermediate file. The backend then uses the bundled FFmpeg executable from `imageio-ffmpeg` to encode H.264 with `yuv420p` and fast-start metadata. This makes processed videos and incident clips playable in Chrome, Edge, and the React video player.

## Fast Mode

Real YOLO defaults to a 416-pixel inference image and runs once every three video frames. The most recent boxes are reused between YOLO frames while tracking, movement, risk scoring, overlays, and video encoding continue on every frame. Configure `DETECTION_FRAME_INTERVAL=1` for maximum detection frequency or a value up to `10` for faster CPU processing with reduced detection responsiveness.

## Beginner web interface

Keep the backend running on port 8000. In a second PowerShell terminal, install and run the frontend:

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection\frontend"
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. Choose an MP4, AVI, or MOV video and select **Upload and analyse video**. The interface calls the existing upload and processing endpoints and displays the processed result.

### Run the friendly interface from one address

Build the frontend after changing its files:

```powershell
cd .\frontend
npm run build
```

FastAPI automatically serves the generated `frontend/dist` folder. With MongoDB and the backend running, open <http://127.0.0.1:8000> to use AquaGuard. A separate `npm run dev` terminal is only needed while actively editing frontend code.

## Important beginner terms

- **Frontend:** the screens the user sees in the browser.
- **Backend:** the server that validates requests, processes video, and talks to the database.
- **API:** the agreed set of URLs through which the frontend communicates with the backend.
- **Database:** persistent storage for videos, incidents, users, and settings.
- **Computer vision:** software that extracts information from images or video.
- **Environment variable:** configuration stored outside source code, especially secrets.
- **Repository:** the project folder tracked by Git.

## Next stage

The current advanced stage is implemented. Open these pages after `npm start`:

- `/live` for visual zone drawing and Fast/Balanced/Accurate tracking modes.
- `/cameras` for persistent RTSP/HTTP camera sources.
- `/incidents` for filters, notes, CSV export, printable PDF, and bulk deletion.
- `/model` for the temporal-model dataset template, training, and validation metrics.

The next recommended engineering stage is a recorded-dataset labelling tool and independent model evaluation report. That work requires real pool footage and safety-reviewed labels; it should not be replaced with generated accuracy claims.
#   A q u a G u a r d - A I  
 