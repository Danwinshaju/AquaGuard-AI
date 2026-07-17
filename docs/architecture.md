# AquaGuard AI architecture

## Safety boundary

AquaGuard AI produces possible-risk alerts from imperfect machine-learning and rules-based signals. False positives and false negatives are expected. The UI and documentation must always state that this educational system is not certified and does not replace a lifeguard or other pool-safety controls.

## High-level request flow

```text
Browser (React)
   |  REST: upload, incidents, dashboard, settings
   |  WebSocket: progress and alerts
   v
FastAPI API
   |-- services ------> MongoDB repositories ------> MongoDB
   |-- video service -> local storage
   `-- processing job
          |-- OpenCV frame reader/writer
          |-- YOLO person detector
          |-- multi-person tracker
          |-- movement history
          |-- pose estimation
          `-- risk engine -> incident media + database record
```

Uploaded and generated media first uses temporary server disk because AI processing runs in FastAPI. After the signed-in browser verifies a complete IndexedDB write, an owner-checked release endpoint deletes the corresponding temporary server copy. MongoDB stores accounts, hashed session tokens, owner-scoped metadata, incident lifecycle data, notes, and camera configuration; it does not store the video bytes.

## Backend layers

1. **API layer (`app/api`)** accepts HTTP/WebSocket traffic, validates inputs, and returns schemas. Routes should not contain computer-vision or database logic.
2. **Service layer (`app/services`)** coordinates workflows such as accepting an upload, starting processing, or acknowledging an incident.
3. **Repository layer (`app/db/repositories`)** contains MongoDB queries. Services do not directly construct database queries.
4. **Schemas (`app/schemas`)** define validated API input and output with Pydantic.
5. **Models (`app/models`)** describe stored MongoDB documents.
6. **Vision pipeline (`app/vision`)** owns frame processing, detection, tracking, motion history, pose signals, and risk evaluation.
7. **Core (`app/core`)** owns cross-cutting configuration, authentication, logging, rate limits, and error handling.

This separation makes individual parts easier to learn, test, and replace.

## Planned vision flow

Each frame moves through the following pipeline:

```text
decode frame
  -> apply configured pool zones
  -> detect people
  -> associate detections with track IDs
  -> update each track's time-series history
  -> calculate independent behaviour signals
  -> smooth signal contributions over time
  -> assign SAFE / WARNING / DANGER
  -> draw overlays and encode output frame
  -> persist an incident only after configured temporal verification
```

State is maintained separately for each tracking ID. A single unusual frame cannot create a confirmed danger incident.

## Risk signal contract

Every risk signal will return the same conceptual result:

```text
triggered: boolean
confidence: number from 0.0 to 1.0
risk_contribution: configurable number of points
explanation: human-readable text
```

Planned independent signals are inactivity, sudden downward movement, disappearance, vertical orientation, head visibility, irregular arm movement, low movement after intense movement, and time in the deep-water zone.

Initial thresholds:

- SAFE: score below 40
- WARNING: score from 40 through 69
- DANGER candidate: score 70 or above
- Confirmed DANGER: candidate persists continuously for at least 3 seconds

Thresholds and weights will come from settings, not hard-coded values.

## Data ownership

MongoDB collections planned for the MVP:

- `users`: identity, password hash, and role
- `cameras`: camera metadata and status
- `videos`: upload and processing metadata
- `incidents`: warning/danger lifecycle and evidence paths
- `detection_events`: optional time-series signal details
- `notifications`: alert delivery attempts
- `system_settings`: risk and application configuration
- `audit_logs`: security-relevant user actions

Documents include `createdAt` and `updatedAt` where appropriate. Video bytes and snapshots are stored as files; MongoDB stores their metadata and paths.

## Pool zones

The frontend zone editor will save polygon points as values between `0` and `1`:

```text
normalised_x = pixel_x / video_width
normalised_y = pixel_y / video_height
```

This lets the backend reconstruct the same polygon at different resolutions. Analysis is limited to people whose centre point, or later segmentation overlap, lies in the pool region. Deep, shallow, entry/exit, and ignored regions add context.

## Progress and background work

Video processing can take much longer than a normal web request. Upload returns a video/job ID quickly. Processing runs outside the request, saves progress, and broadcasts progress through a WebSocket. A production deployment should move jobs to a durable worker queue; the beginner MVP will first use a clearly isolated local background processor.

## Security boundaries

- Validate extension, detected MIME type, and maximum size.
- Generate server-side storage names; never trust an uploaded filename as a path.
- Hash passwords with salted `scrypt` and store only opaque session-token hashes in MongoDB.
- Require the HttpOnly session cookie on protected REST and WebSocket routes and filter every owned resource by the authenticated user ID.
- Keep secrets in environment variables and out of Git.
- Restrict CORS to configured frontend origins.
- Add central errors, request logs, audit logs, and rate limiting.

## Mock AI mode

`MOCK_AI=true` will let learners exercise uploads, progress, overlays, incidents, and UI flows without a GPU or model download. The mock will implement the same interface as the real detector so it can be exchanged without changing API routes or UI code.

## Development stages

1. Repository structure and architecture (current stage)
2. FastAPI, health endpoint, MongoDB, and environment settings
3. Upload validation and local storage
4. OpenCV reading and output generation
5. YOLO person detection
6. Tracking IDs
7. Movement and inactivity
8. Risk engine and temporal verification
9. Incident evidence and persistence
10. React TypeScript frontend
11. Upload/progress/results integration
12. Dashboard, incidents, and analytics
13. Pose estimation
14. Authentication and roles
15. Tests, Docker, logging, and deployment documentation

Each stage must run and be tested before the next stage begins.
