# AquaGuard AI

AquaGuard AI is an educational drowning-risk early-warning project created by **Danwin Shaju**. It analyses uploaded swimming-pool video, a browser camera, and RTSP/HTTP network-camera streams. The system detects and tracks people, evaluates movement and pose over time, produces operator alerts, and creates incident evidence for human review.

> AquaGuard AI is not certified safety equipment and must never replace trained lifeguards, direct supervision, pool barriers, alarms, rescue equipment, or an emergency-response plan.

## Main features

- React 19 and TypeScript user interface
- FastAPI REST API and WebSockets
- MongoDB accounts, sessions, cameras, and incident metadata
- Private signup, login, and logout
- Owner-isolated reports, evidence, dashboard totals, and cameras
- Browser IndexedDB storage for each user's processed videos and incident media
- Uploaded MP4, AVI, and MOV analysis
- Live browser-camera tracking
- RTSP/HTTP network-camera monitoring
- YOLO11 person detection and pose estimation
- ByteTrack person identities
- Movement, inactivity, pool-zone, posture, and temporal risk signals
- Visual warnings, three alert beeps, and browser vibration
- Evidence screenshots and short H.264 clips
- Incident notes, filters, CSV export, printing, and deletion
- Automatic 24-hour report and media cleanup
- Optional temporal-model and aquatic-YOLO training

## User-owned browser storage

Media is created temporarily on the server because AI processing happens there. AquaGuard then:

1. Downloads the processed video, snapshot, and clip into the signed-in user's browser.
2. Validates the returned media blobs.
3. Commits them to that account's IndexedDB records.
4. Calls owner-checked release endpoints.
5. Deletes the temporary server media only after browser storage succeeds.

If browser storage is unavailable or full, the temporary server copy is retained instead of deleting the only evidence. Evidence from an unattended network camera transfers when its owner next opens **Incidents**.

IndexedDB belongs to a specific browser profile and website address. Media does not automatically move to another device and can be lost if the user clears site data. Important evidence should be downloaded before the 24-hour retention period ends.

## Requirements

- Windows 10 or 11
- Python 3.11
- Node.js and npm
- Docker Desktop
- Git

## Run the complete application

Open Docker Desktop and wait for its engine to start. Then open PowerShell in the project root:

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection"
npm start
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000), create an account, and log in. The same address serves the React frontend and FastAPI backend.

After the first successful frontend build, this faster command reuses the existing build:

```powershell
npm run start:fast
```

## Verification

Backend:

```powershell
cd backend
python -m black .
python -m ruff check .
python -m pytest
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Documentation

- [Complete project documentation](docs/PROJECT-DOCUMENTATION.md)
- [User guide](docs/USER-GUIDE.md)
- [Accounts, login, startup, and storage guide](docs/ACCOUNTS-AND-STORAGE-GUIDE.md)
- [Live demonstration guide](docs/LIVE-DEMO-GUIDE.md)
- [Troubleshooting guide](docs/TROUBLESHOOTING-GUIDE.md)
- [Architecture](docs/architecture.md)
- [Production-oriented features](docs/production-features.md)
- [Aquatic model training](docs/AQUATIC-MODEL-TRAINING.md)

The running application also provides a Documentation page and FastAPI API explorer at `/docs`.

## Author

**Danwin Shaju**

- Email: [danwin212@gmail.com](mailto:danwin212@gmail.com)
- GitHub: [github.com/Danwinshaju](https://github.com/Danwinshaju)
- LinkedIn: [linkedin.com/in/danwin-shaju](https://www.linkedin.com/in/danwin-shaju/)

Copyright © 2026 Danwin Shaju. All rights reserved.
