# AquaGuard AI — Troubleshooting Guide

Author and developer: Danwin Shaju  
Email: [danwin212@gmail.com](mailto:danwin212@gmail.com)  
GitHub: [github.com/Danwinshaju](https://github.com/Danwinshaju)  
LinkedIn: [linkedin.com/in/danwin-shaju](https://www.linkedin.com/in/danwin-shaju/)  
Copyright: © 2026 Danwin Shaju. All rights reserved.

## The application does not open

### Symptom

`http://127.0.0.1:8000` displays an error or cannot connect.

### Solution

1. Keep the PowerShell startup terminal open.
2. Confirm that it displays `Application startup complete`.
3. Run the command from the project root, not from `frontend` or `backend`:

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection"
npm start
```

4. If port 8000 is already used, stop the earlier Uvicorn terminal with `Ctrl+C`.

## Docker or MongoDB cannot start

1. Open Docker Desktop manually.
2. Wait for **Engine running**.
3. Check:

```powershell
docker --version
docker compose version
docker compose ps
```

4. Run `npm start` again.

## `ModuleNotFoundError: No module named 'app'`

Uvicorn was started from the project root instead of `backend`. Use the single launcher `npm start`, or run manually:

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection\backend"
python -m uvicorn app.main:app --reload
```

## Browser camera remains black or requests permission forever

1. Select the camera icon beside the browser address.
2. Set camera permission to **Allow**.
3. Close Teams, Zoom, Camera, or other programs using the camera.
4. Reload the page.
5. Select **Retry live camera**.
6. Confirm the page uses `127.0.0.1` or `localhost`, which browsers treat as a secure camera context.

## The pool-zone message reports an invalid deep-water boundary

1. Select **Reset full zone**.
2. Draw the pool rectangle again.
3. Keep the deep-water slider between the top and bottom pool boundaries.

## Live tracking freezes or has low FPS

1. Select **Fast** mode.
2. Stop unused RTSP cameras.
3. Close other video, AI, browser, and GPU applications.
4. Use a lower-resolution camera source.
5. Check the Dashboard for GPU selection and free storage.
6. Keep the computer connected to power and use its performance power mode.

## No person box appears

1. Confirm `MOCK_AI=false` in `backend/.env` for real detection.
2. Confirm these files exist:
   - `backend/yolo11n.pt`
   - `backend/yolo11n-pose.pt`
3. Improve lighting and camera angle.
4. Keep the complete person visible where possible.
5. Confirm the person is inside the configured pool zone.

## Boxes appear but IDs change

Tracking identity can change during heavy overlap, fast motion, reflections, or long occlusion. Use a fixed elevated camera angle, reduce obstruction, improve lighting, and keep `LIVE_USE_BYTETRACK=true`.

## No warning or danger alert occurs

AquaGuard does not trigger danger merely because a person appears. Risk must exceed the configured threshold for a persistence duration.

1. Confirm the pool zone covers the correct area.
2. Watch the highest-risk value and status.
3. Confirm real YOLO mode is active.
4. Check whether movement/pose signals are available.
5. Do not dangerously stage behaviour or lower thresholds only to force an alert.

## The beep does not play

Browsers can block audio until the user interacts with the page. Select **Start camera** or click the page before the expected alert. Check the Windows output volume and browser-tab sound setting.

## Processed video is black or cannot play

1. Use a valid MP4, AVI, or MOV file.
2. Keep the server running while playing the result.
3. Reprocess the video so AquaGuard can produce a browser-compatible H.264 output.
4. Check free disk space on Dashboard.

## A network camera remains reconnecting

1. Confirm the RTSP/HTTP URL is complete and correct.
2. Test that the camera is reachable from the same computer/network.
3. Confirm the camera username/password if required.
4. Confirm its stream is not limited to another client.
5. Check firewall and network rules.
6. Remove and re-add the camera only if the saved URL is incorrect.

## Incident snapshot or clip is missing

Evidence is automatically deleted after 24 hours by default. It is also removed when an operator deletes an incident. If the incident is new, check the `storage/incidents` folders and free storage.

## Training fails

1. Use a CSV with exactly the template column names.
2. Give every `sequence_id` at least 16 ordered frames.
3. Include at least two independent sequence IDs.
4. Use numeric feature values and labels `0` or `1`.
5. Review the training log shown on the Train AI page.

## Verification commands

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection"
.\.venv\Scripts\Activate.ps1
cd .\backend
python -m black .
python -m ruff check .
python -m pytest
```

If an error remains, copy the complete red terminal message, including its first and last lines, before asking for help.

© 2026 Danwin Shaju. All rights reserved.
