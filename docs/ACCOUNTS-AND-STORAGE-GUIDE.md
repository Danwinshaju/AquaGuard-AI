# AquaGuard AI accounts, startup, and storage guide

- Author: Danwin Shaju
- Email: [danwin212@gmail.com](mailto:danwin212@gmail.com)
- GitHub: [github.com/Danwinshaju](https://github.com/Danwinshaju)
- LinkedIn: [linkedin.com/in/danwin-shaju](https://www.linkedin.com/in/danwin-shaju/)

This guide explains how to run AquaGuard, when to create or reuse an account, how login protection works, and exactly where each type of data is stored.

> AquaGuard AI is an educational early-warning prototype. It is not certified safety equipment and must not replace a trained lifeguard, direct supervision, rescue equipment, or an emergency-response plan.

## 1. Run the complete project

### Required software

- Windows 10 or 11
- Python 3.11 (not Python 3.14)
- Node.js and npm
- Docker Desktop with its Linux engine running

### Normal start

1. Open Docker Desktop.
2. Wait until Docker reports that the engine is running.
3. Open the AquaGuard project folder in VS Code.
4. Select **Terminal > New Terminal**.
5. Run these commands from the project root:

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection"
npm start
```

The launcher starts MongoDB, builds the React frontend, and starts FastAPI/Uvicorn. Keep this terminal open. When it shows `Application startup complete`, open `http://127.0.0.1:8000`.

Do not use `/api` as the application page. `/docs` is the API explorer, while `/login` is the direct login address.

### Faster later start

After at least one successful normal build, reuse the existing frontend build:

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection"
npm run start:fast
```

### Stop and restart

Press `Ctrl+C` in the startup terminal to stop Uvicorn. Start it again with `npm start` or `npm run start:fast`. Docker Desktop must remain available whenever the application needs its local MongoDB container.

## 2. Login use cases

### First-time user

1. Open `http://127.0.0.1:8000/signup`.
2. Enter a display name, valid email address, and password of 8 to 128 characters.
3. Select **Create account**.
4. AquaGuard creates the account, signs the user in, and opens the protected application.

Email addresses are trimmed and converted to lowercase. An email address cannot be registered twice.

### Returning user

1. Open `http://127.0.0.1:8000/login`.
2. Enter the registered email and password.
3. Select **Log in**.

A successful login creates a session lasting up to seven days. Closing the browser does not necessarily log the user out because the cookie may remain valid.

### Protected page opened while logged out

Pages such as `/analyze`, `/live`, `/dashboard`, `/incidents`, and `/cameras` require authentication. The frontend redirects a logged-out visitor to `/login`, and protected backend requests return HTTP 401 without a valid session.

### Multiple users on one installation

Each person should use a separate account. The backend includes the signed-in user ID when it reads or changes incidents, evidence, dashboard totals, processing jobs, and network cameras. Knowing another record ID does not grant access.

Browser media is also keyed by account ID inside IndexedDB. People sharing one Windows/browser profile should still select **Log out** after use so the next person cannot continue the existing session.

### Shared or public computer

1. Download evidence that must be retained.
2. Select **Log out**.
3. If required by local policy, clear site data only after confirming nothing important remains.

Clearing site data deletes browser-owned processed videos, snapshots, and clips. Logging out ends the server session but intentionally does not erase valid evidence immediately.

### Expired or invalid session

If the session is older than seven days, was logged out, or no longer exists in MongoDB, the API returns HTTP 401. Return to `/login` and authenticate normally.

### Forgotten password

This local MVP does not implement email password reset. A production deployment should add a verified reset workflow before public use.

## 3. Authentication implementation

1. `POST /api/v1/auth/signup` validates the form, creates a unique user ID, and stores the normalized email.
2. Passwords are salted and hashed with Python `scrypt`; the original password is never stored.
3. Signup or login creates a cryptographically random opaque session token.
4. The browser receives it in the `aquaguard_session` cookie with `HttpOnly` and `SameSite=Lax`. Production mode also sets `Secure`.
5. MongoDB stores only the SHA-256 hash of that token, its user ID, and expiration time.
6. Protected API dependencies resolve the cookie to the current user.
7. Repository queries include `owner_id`, preventing cross-account reads, updates, exports, and deletions.
8. Logout deletes the current database session and removes the cookie.

The browser cannot read an HttpOnly cookie with JavaScript. A public production deployment still requires HTTPS, rate limiting, monitoring, backups, a security review, and a password-reset flow.

## 4. Storage system

| Data | Primary location | Ownership and lifetime |
|---|---|---|
| Accounts | MongoDB `users` collection | Shared database; password stored only as a salted hash |
| Login sessions | MongoDB `sessions` + HttpOnly cookie | Token hash expires after seven days; logout deletes the session |
| Incident metadata and notes | MongoDB `incidents` collection | Filtered by `owner_id`; deleted after 24 hours by default |
| Network-camera settings | MongoDB `cameras` collection | Filtered by `owner_id`; retained until owner deletion |
| Uploaded original | Temporary server `storage` directory | Owner-checked; released after verified result storage |
| Processed analyzed video | Browser IndexedDB `aquaguard-user-media` | Keyed by account and video; expires after 24 hours by default |
| Incident snapshot and clip | Browser IndexedDB `aquaguard-user-media` | Keyed by account and incident; expires after 24 hours by default |
| Failed browser transfer | Temporary server `storage` directory | Retained temporarily so the only copy is not destroyed |
| Training model files | Backend model path/local project files | Installation resource, not account evidence |

### Verified media transfer

AI processing needs temporary server files. When a result is ready, the frontend downloads the media, confirms that it is a non-empty media blob, and commits it to IndexedDB. Only after that transaction succeeds does it call an authenticated release endpoint to delete the temporary server copy.

If IndexedDB is blocked or full, the page closes during transfer, or the response is invalid, AquaGuard reports partial storage and retains the temporary copy. Network-camera evidence transfers when its owner next opens **Incidents**.

### Meaning of user-owned browser storage

- Media is keyed to one AquaGuard account and browser profile.
- It is stored on that user's device, not in the developer's browser.
- It does not synchronize to another browser, computer, domain, or deployment address.
- Private/incognito mode may remove it when the private session closes.
- Browser cleanup and **Clear site data** can delete it.
- Important evidence must be downloaded before the retention deadline.

MongoDB remains the installation's shared metadata database. User-owned storage does not give each user a separate MongoDB server; access is owner-filtered, while large media moves into the user's browser.

## 5. Analyzed-video playback

After analysis completes, the labelled output starts automatically and repeats. It begins muted because browsers commonly block unmuted autoplay. Use the player's speaker control to hear source audio. AquaGuard's visual danger indicators and alert logic are separate from the source video's audio track.

## 6. Operator checklist

Before use:

- Confirm direct supervision and a trained responder are present.
- Confirm Docker, MongoDB, and AquaGuard health.
- Log in with the correct account.
- Confirm the correct camera and pool zone.
- Confirm tracking boxes follow people.
- Confirm the browser permits camera access and alert audio.

After use:

- Review unresolved incidents.
- Save notes and correct statuses.
- Download evidence that must outlive the 24-hour retention period.
- Stop live monitoring.
- Log out on a shared computer.
- Press `Ctrl+C` when the application should stop.

## 7. Troubleshooting login and storage

### Login page keeps returning

Confirm MongoDB is running, cookies are enabled, and the same address is used consistently. `localhost:8000` and `127.0.0.1:8000` are different browser origins with separate cookies and IndexedDB data.

### Correct password is rejected

Check the email spelling. The application intentionally returns the same generic message for an unknown email and an incorrect password.

### Media says it is partially stored

Keep the page open, confirm available browser disk space, allow site storage, and try again. AquaGuard retains temporary server media when verified transfer fails.

### Evidence is missing in another browser

This is expected. IndexedDB is local to the original browser profile and site address. Open the original profile or use a downloaded copy.

### Docker is not running

Open Docker Desktop, wait for **Engine running**, and run `npm start` again from the project root.

Copyright © 2026 Danwin Shaju. All rights reserved.
