# AquaGuard AI — Live Demonstration Guide

Author and developer: Danwin Shaju  
Email: [danwin212@gmail.com](mailto:danwin212@gmail.com)  
GitHub: [github.com/Danwinshaju](https://github.com/Danwinshaju)  
LinkedIn: [linkedin.com/in/danwin-shaju](https://www.linkedin.com/in/danwin-shaju/)  
Copyright: © 2026 Danwin Shaju. All rights reserved.

This guide provides a clear project-presentation sequence. AquaGuard is educational assistance and not certified safety equipment.

## Before the demonstration

1. Connect the computer to power.
2. Open Docker Desktop and wait for the engine to start.
3. Close applications that may use the camera or GPU.
4. Keep one short normal-swimming video and one professionally prepared demonstration video available locally.
5. Never stage unsafe behaviour in water for a demonstration.
6. Start AquaGuard from the project root:

```powershell
npm start
```

7. Open `http://127.0.0.1:8000/documentation`.

## Recommended 10-minute presentation

### 1. Introduce the project — 1 minute

- Explain that AquaGuard analyses uploaded, browser-camera, and network-camera video.
- State clearly that it is an educational early-warning prototype.
- Show the technology stack and architecture on the Documentation page.

### 2. Uploaded-video demonstration — 2 minutes

1. Open **Analyse**.
2. Upload the prepared short video.
3. Explain the progress percentage.
4. Play the processed output.
5. Point out person boxes, persistent IDs, movement values, risk labels, and evidence.

### 3. Live-camera demonstration — 3 minutes

1. Open **Live**.
2. Choose **Fast** or **Balanced**.
3. Draw a pool/test zone directly on the camera image.
4. Start the camera and grant permission.
5. Move slowly in front of the camera.
6. Explain detection boxes, person IDs, risk score, FPS, and AI output.
7. Explain that warning and danger require temporal evidence and are not triggered just because a person is visible.

### 4. Incident workflow — 2 minutes

1. Open **Incidents**.
2. Show the saved snapshot and evidence clip.
3. Explain risk signals and lifecycle status.
4. Add a demonstration note.
5. Show filters, CSV export, printable PDF, and automatic 24-hour deletion.

### 5. System and AI engineering — 1 minute

1. Open **Dashboard** and show database, GPU, model, camera, and storage health.
2. Open **Train AI** and explain the CSV sequence format and independent validation requirement.

### 6. Conclusion — 1 minute

- Summarise detection, tracking, temporal risk, alerts, evidence, reporting, and monitoring.
- Repeat the safety limitation and need for trained human supervision.
- Open the author section with Danwin Shaju's contact and project profiles.

## Useful local demonstration links

- Documentation: `http://127.0.0.1:8000/documentation`
- Uploaded analysis: `http://127.0.0.1:8000/analyze`
- Live camera: `http://127.0.0.1:8000/live`
- Cameras: `http://127.0.0.1:8000/cameras`
- Dashboard: `http://127.0.0.1:8000/dashboard`
- Incidents: `http://127.0.0.1:8000/incidents`
- Train AI: `http://127.0.0.1:8000/model`
- Interactive API: `http://127.0.0.1:8000/docs`

## Demonstration rules

- Use short local videos to reduce processing wait time.
- Use Fast mode if live output becomes slow.
- Do not change risk thresholds immediately before presenting.
- Do not claim that a sample video proves accuracy.
- Do not force an alert by staging dangerous behaviour.
- If a real emergency occurs, stop presenting and follow the emergency procedure.

© 2026 Danwin Shaju. All rights reserved.
