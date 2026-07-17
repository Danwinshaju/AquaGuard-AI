AQUAGUARD AI - PENDRIVE / OFFLINE WINDOWS GUIDE
================================================

This package is intended for a 64-bit Windows 10/11 computer.
The destination computer needs at least 8 GB RAM, hardware virtualization,
and WSL 2 support for Docker Desktop.

FIRST TIME ON THE OFFLINE COMPUTER
----------------------------------
1. Copy the entire AquaGuard-AI-Offline folder from the pendrive to the
   computer's Documents folder. Running from the internal drive is faster.
2. Open PowerShell inside the copied AquaGuard-AI-Offline folder.
3. Run:

   powershell -ExecutionPolicy Bypass -File .\scripts\setup-offline.ps1

4. If Docker or Python is installed, follow the restart message and run the
   same setup command again after restarting Windows.
5. Open Docker Desktop once and wait until the engine is ready.

RUN AQUAGUARD WITHOUT INTERNET
------------------------------
Open PowerShell in the AquaGuard-AI-Offline folder and run:

   powershell -ExecutionPolicy Bypass -File .\scripts\start-offline.ps1

Then open http://127.0.0.1:8000 in Chrome or Edge.

WHAT THE PACKAGE CONTAINS
-------------------------
- Compiled React frontend; Node.js and npm are not required offline.
- Python dependency wheelhouse, including CPU-only PyTorch.
- YOLO person and pose model files.
- MongoDB 8 Docker image archive.
- Optional Python 3.11 and Docker Desktop installers.

IMPORTANT
---------
- The browser live camera works offline.
- RTSP cameras work on the local network without internet.
- Webhook/email alerts cannot work without a network connection to their
  configured destination.
- Do not remove the offline folder, backend model files, or frontend/dist.
- AquaGuard is educational assistance, not a certified safety device.
