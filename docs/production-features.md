# Production-oriented AquaGuard features

These features improve the engineering quality of the project but do not certify it as a lifesaving device.

## Pool calibration

Open `/live`, expand **Calibrate pool and deep-water zone**, and select **Draw pool zone on camera**. Drag directly over the camera picture to mark the pool rectangle, then use the deep-water slider to place its boundary. The numeric sliders remain available for fine adjustments. Only people whose center lies inside the pool rectangle enter live risk analysis. Calibration is saved in that browser.

## Live performance profiles

Choose **Fast**, **Balanced**, or **Accurate** on `/live`. Fast uses smaller images and fewer pose checks for CPU responsiveness. Balanced is the default. Accurate sends larger frames and checks pose more often, which improves small-person detail but needs more CPU or a supported GPU.

## Strong tracking

Live analysis uses Ultralytics ByteTrack when `LIVE_USE_BYTETRACK=true`. It preserves IDs through short overlaps and occlusion. If ByteTrack fails to initialize at runtime, AquaGuard falls back to its centroid tracker and continues operating.

## Temporal drowning classifier

The optional LSTM examines 16 consecutive movement/pose observations. Open `/model` to download a working CSV template, upload labelled data, train in the background, and review accuracy, precision, recall, F1, and false-positive rate. It activates after `backend/models/drowning_temporal.ts` is created and AquaGuard is restarted. Dataset collection and independent validation are required before making safety claims.

## Multiple network cameras

Open `/cameras` and register an `rtsp://`, `http://`, or `https://` stream. Every camera has an independent AI session, annotated preview, people/risk counters, connection health, and automatic reconnection. Camera registrations are saved in MongoDB and restored automatically after an AquaGuard restart.

## Incident operations and reports

`/incidents` supports camera/video search, status, source, risk and date filters. Operators can add notes, acknowledge or resolve alerts, mark false alarms, select and delete multiple incidents, export CSV, or use **Print / Save PDF** for a printable report. Every operation is restricted to the signed-in owner, including evidence-file responses and **Delete all**. Evidence and its MongoDB record still expire automatically after 24 hours.

## Per-user device storage

Processed video and incident media are stored in the signed-in account's browser IndexedDB. AquaGuard downloads and validates each blob, commits it to IndexedDB, and only then calls an owner-checked endpoint to remove the temporary server file. Failed transfers deliberately keep the server copy. Evidence created by unattended network cameras transfers when the owner opens `/incidents`. IndexedDB is specific to one browser profile and origin, can be cleared by the user/browser, and is not cross-device cloud storage.

## External alerts and escalation

Browser live danger produces the existing visual warning, vibration, and three beeps. Set `ALERT_WEBHOOK_URL` to deliver JSON to a control-room service, Slack-compatible relay, SMS/phone provider, automation server, or physical-siren controller. Alternatively set the SMTP variables for email. An unresolved alert is sent again as `ESCALATED` after `ALERT_ESCALATION_SECONDS`.

## GPU and system health

Leave `YOLO_DEVICE` empty for automatic selection, use `cpu` to force CPU, or use `cuda:0` after installing a CUDA-compatible PyTorch build and NVIDIA driver. `/dashboard` and `/api/v1/health/system` report CUDA, GPU name, MongoDB, temporal model, cameras, and free evidence storage.

## Reliability and privacy

RTSP streams reconnect automatically, MongoDB restarts through Docker, Uvicorn reloads backend changes, and the dashboard exposes degraded dependencies. Signup/login uses salted `scrypt` password hashes and random server-side MongoDB sessions delivered through HttpOnly SameSite cookies. Incidents, evidence, exports, dashboard totals, and network cameras are owner-isolated. Incident documents, screenshots, and clips are deleted after 24 hours. Physical requirements such as an uninterruptible power supply, redundant network equipment, safely mounted cameras, and a trained lifeguard response procedure must be supplied outside the software.
