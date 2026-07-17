# AquaGuard AI Streamlit deployment guide

This guide publishes a lightweight AquaGuard portfolio demonstration through Streamlit
Community Cloud. It is separate from the full local React, FastAPI, MongoDB, and live-camera
application.

## What the online demo includes

- MP4, AVI, and MOV upload
- YOLO11 person detection
- ByteTrack person identities
- Movement and inactivity-based illustrative risk labels
- H.264 labelled result that autoplays and repeats
- Optional possible-risk evidence frame
- Result-video download
- Temporary-file removal after processing

The online demo has no signup, MongoDB, incident history, browser-camera WebSocket, network
camera, or persistent evidence storage. Those features remain available in the complete local
application.

## Free-cloud limits

- Maximum upload: 150 MB
- Maximum duration: 60 seconds
- Fast mode is recommended for the free CPU
- The first visit may be slow while the app wakes and downloads `yolo11n.pt`
- The app can sleep after inactivity
- Generated files are not persistent

## Deploy from GitHub

1. Open [Streamlit Community Cloud](https://share.streamlit.io/).
2. Sign in with GitHub.
3. Select **Create app** and **Deploy a public app from GitHub**.
4. Enter the following values:

```text
Repository: Danwinshaju/AquaGuard-AI
Branch: agent/browser-owned-evidence
Main file path: streamlit_app.py
App URL: aquaguard-ai-danwin
```

5. Open **Advanced settings** and choose Python 3.11.
6. The demo requires no secrets.
7. Select **Deploy**.
8. Watch the deployment logs while Streamlit installs the CPU versions of PyTorch, YOLO,
   OpenCV, and FFmpeg. The first build can take several minutes.

After the pull request is merged, the app can be changed from
`agent/browser-owned-evidence` to `main` in Streamlit's app settings.

## Public link

The chosen URL should be:

```text
https://aquaguard-ai-danwin.streamlit.app
```

Add that address to the GitHub repository About section, README, LinkedIn Featured section,
and LinkedIn project post only after the deployment succeeds.

## Troubleshooting

### Streamlit says `streamlit_app.py` does not exist

Confirm that the branch is `agent/browser-owned-evidence`. The deployment file is introduced
on that branch before it is merged into `main`.

### Dependency installation exceeds a resource limit

Confirm `requirements.txt` uses the PyTorch CPU wheel index and does not install CUDA wheels.
Reboot the app once after correcting the requirements.

### OpenCV reports that `libGL.so.1` is missing

Confirm the repository contains `packages.txt`. Streamlit installs the listed Debian
`libgl1` and `libglib2.0-0` runtime libraries before starting the Python application.

### Video processing is slow

Use a 10-to-20-second video and select **Fast**. Free hosting uses shared CPU resources.

### Video cannot be opened

Use a normal MP4 with H.264 video. Re-encode unusual AVI or MOV files before uploading.

### The model cannot download

Reboot the app. The initial model download requires outbound HTTPS and may occasionally fail
during a temporary service or network problem.

## Safety statement

The Streamlit version is a portfolio demonstration, not a pool-safety product. It cannot
determine that a person is drowning or safe and must never replace a trained lifeguard,
direct supervision, rescue equipment, or emergency procedures.

Copyright © 2026 Danwin Shaju. All rights reserved.
