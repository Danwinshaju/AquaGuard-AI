# AquaGuard AI — User Guide

Author: Danwin Shaju  
Email: [danwin212@gmail.com](mailto:danwin212@gmail.com)  
GitHub: [github.com/Danwinshaju](https://github.com/Danwinshaju)  
LinkedIn: [linkedin.com/in/danwin-shaju](https://www.linkedin.com/in/danwin-shaju/)  
Copyright: © 2026 Danwin Shaju. All rights reserved.  
Application: `http://127.0.0.1:8000`

## Safety notice

AquaGuard AI is an educational early-warning project, not a certified safety device. Never use it instead of a trained lifeguard, direct supervision, pool barriers, alarms, rescue equipment, or an emergency-response plan. Treat every AI alert as a request for immediate human verification, not as a medical diagnosis.

## 1. Start the application

1. Open Docker Desktop.
2. Wait until Docker shows that its engine is running.
3. Open VS Code and open the AquaGuard project folder.
4. Select **Terminal > New Terminal**.
5. Run:

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection"
npm start
```

6. Keep the terminal open.
7. When the terminal displays `Application startup complete`, open `http://127.0.0.1:8000` in Chrome or Edge.

8. On first use, select **Create an account**, enter your name and email, and choose a password with at least eight characters. On later visits, use **Log in**. Select **Log out** before leaving a shared computer.

To stop AquaGuard, return to the terminal and press `Ctrl+C`.

## 2. Navigation

Every main page has the following navigation:

- **Analyse:** upload and analyse a recorded video.
- **Live:** use the current computer's camera.
- **Cameras:** add RTSP/HTTP network cameras.
- **Dashboard:** review application and dependency health.
- **Incidents:** review saved danger evidence and record outcomes.
- **Train AI:** train the optional temporal model from labelled data.
- **Documentation:** read project and operating information.
- **Log out:** close the current account session and return to the login page.

### Account privacy

Incident lists, dashboard totals, screenshots, clips, CSV exports, notes, status changes, deletion actions, and saved network cameras are filtered by the signed-in account on the backend. Knowing another incident ID does not grant access. An unauthenticated request receives HTTP 401. Sessions last up to seven days and are stored in an HttpOnly browser cookie; the password is stored only as a salted `scrypt` hash.

For detailed signup, login, shared-computer, account-isolation, startup, and storage scenarios, read [ACCOUNTS-AND-STORAGE-GUIDE.md](ACCOUNTS-AND-STORAGE-GUIDE.md).

## 3. Analyse an uploaded video

1. Open **Analyse**.
2. Select **Browse videos**, or drag an MP4, AVI, or MOV file into the upload area.
3. Confirm the selected filename.
4. Select **Upload and analyse video**.
5. Keep the page open while the progress percentage increases.
6. When processing finishes, the labelled output video starts automatically and repeats continuously. It starts muted so Chrome and Edge do not block autoplay; use the player control to unmute it.
7. Watch the person boxes, tracking IDs, movement values, risk labels, and warning banner. Pause or seek with the normal player controls when you need to inspect a frame.
8. If a possible danger incident exists, the page displays its screenshot and short evidence clip.
9. Select **Acknowledge and respond** only after a person has visually checked the situation.
10. Select **Analyse another video** to clear the current result.

### Understanding the result

- **People tracked:** number of tracking identities created in the video.
- **Frames checked:** number of frames evaluated.
- **Detection mode:** YOLO means real person detection; Demo means mock sample boxes.
- **Longest inactive:** longest measured low-movement duration.
- **SAFE:** current evidence is below warning thresholds; it does not prove safety.
- **WARNING:** behaviour needs human attention.
- **DANGER:** configured risk persisted long enough to request immediate verification.

## 4. Use the live browser camera

1. Open **Live**.
2. Select a performance profile:
   - **Fast:** recommended when CPU tracking freezes or becomes slow.
   - **Balanced:** recommended for normal use.
   - **Accurate:** larger AI input for a capable GPU.
3. Expand **Calibrate pool and deep-water zone**.
4. Select **Draw pool zone on camera**.
5. Drag a rectangle over only the pool-water area in the camera picture.
6. Use the sliders to fine-tune the left, top, right, bottom, and deep-water boundary.
7. Select **Start camera**.
8. Allow camera permission when the browser asks.
9. Keep the original camera view and AI tracking output visible.
10. Monitor status, number of people, highest risk, detection mode, and processing FPS.
11. Select **Stop camera** before leaving the page or when monitoring is finished.

### If a live alert occurs

1. Look directly at the actual pool or live camera immediately.
2. Alert the trained lifeguard.
3. Follow the site's emergency-response plan.
4. Do not delay rescue action to examine the AI interface.
5. After the situation is handled, open **Incidents** to review and document the event.

## 5. Add a network camera

1. Confirm that the camera and AquaGuard computer are on a reachable network.
2. Obtain the camera's RTSP, HTTP, or HTTPS stream URL from its manufacturer or administrator.
3. Open **Cameras**.
4. Enter a meaningful camera name, such as `Main Pool - Deep End`.
5. Enter the complete stream URL.
6. Select **Add camera**.
7. Wait for the status to become **online**.
8. Review the annotated preview, people count, risk, last-frame time, and reconnection count.
9. If the stream is interrupted, AquaGuard attempts to reconnect automatically.
10. Use **Remove camera** only when the saved camera should be permanently deleted.

Camera configurations are stored in MongoDB and restored when AquaGuard restarts.

## 6. Use the dashboard

Open **Dashboard** to review:

- unresolved and total incident counts;
- alert activity by day;
- MongoDB connection status;
- CUDA/GPU availability and selected processing device;
- temporal-model readiness;
- registered network-camera health;
- free evidence-storage space.

Investigate degraded or offline health items before depending on live analysis.

## 7. Manage incidents

Only incidents created while your account was signed in appear on this page. **Delete all incidents** deletes only your account's reports and evidence, never another user's data.

1. Open **Incidents**.
2. Use search to find a camera name or video ID.
3. Filter by status, source, minimum risk, or date.
4. Open the snapshot and play the evidence clip.
5. Read **Why this alert was created**.
6. Add operator observations or response details under **Operator notes** and select **Save notes**.
7. Choose the correct lifecycle action:
   - **Acknowledge:** an operator has seen and started responding.
   - **Resolve:** response and review are complete.
   - **False alarm:** human review determined no emergency occurred.
8. Select **Export CSV** for spreadsheet data.
9. Select **Print / Save PDF** for a printable report.
10. Delete only when evidence is no longer needed. Deletion is permanent.

Incident documents, screenshots, and clips are automatically deleted after 24 hours by default.

### Where evidence is stored

The server creates media temporarily because AI processing runs on the server. After both the screenshot and clip are successfully written to the signed-in user's browser IndexedDB, AquaGuard requests deletion of the server copies. Uploaded originals and processed videos follow the same transfer-and-release rule. If browser storage is blocked, full, or unavailable, AquaGuard keeps the temporary server copy rather than deleting the only evidence. Network-camera evidence transfers when the owner next opens **Incidents**.

Device evidence is specific to the browser profile and deployment address. It will not appear automatically on another computer, in another browser, or after browser-site data is cleared. Download any evidence that must be kept. Device evidence and its MongoDB report expire after 24 hours by default.

## 8. Train the optional temporal AI

1. Open **Train AI**.
2. Download the CSV template.
3. Replace the illustrative data with many independently recorded and correctly labelled sequences.
4. Use label `0` for normal behaviour and `1` for drowning-like behaviour.
5. Select the labelled CSV file.
6. Choose the number of epochs.
7. Select **Start training**.
8. Wait for completion and review accuracy, precision, recall, F1, and false-positive rate.
9. Restart AquaGuard after training so new sessions load the model.

Never treat template-data results or training accuracy as real-world safety performance. Use independent test videos and professional safety review.

### Train the aquatic YOLO dataset model

The Swimming and Drowning Detection Roboflow dataset is trained separately because it contains images and YOLO bounding-box labels rather than temporal CSV rows. Open **Train AI**, find **Train aquatic YOLO model**, and download its training guide. Run the one-epoch, 5%-data technical test before starting a full training job. After training, restart AquaGuard and confirm **Custom aquatic dataset model: ACTIVE** on the Live page.

For simple demonstration training, run five epochs with 10% of the dataset. This verifies the workflow and creates a usable model file, but it does not establish safety accuracy.

## 9. Recommended operating checklist

Before monitoring:

- Confirm direct human supervision is active.
- Confirm Docker, MongoDB, cameras, and storage health.
- Clean and securely mount cameras.
- Confirm the pool zone is correctly calibrated.
- Confirm tracking boxes follow visible people.
- Test that browser sound is permitted.
- Confirm the trained lifeguard knows the emergency procedure.

After monitoring:

- Stop the browser camera if it is no longer required.
- Review unresolved incidents.
- Add response notes and correct incident status.
- Export any required report before automatic deletion.
- Press `Ctrl+C` in the server terminal to stop AquaGuard.

## 10. Privacy and responsible use

- Use cameras only where recording and analysis are permitted.
- Inform affected people according to applicable policy and law.
- Do not expose the local AquaGuard API directly to the public internet.
- Store exported incident reports securely.
- Do not retain screenshots or clips longer than necessary.
- Never publish identifiable emergency footage without appropriate authority.

© 2026 Danwin Shaju. All rights reserved.
