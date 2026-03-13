# AI-Perception-Monitor

A production-ready AI Perception Monitoring System built with YOLOv8, FastAPI, WebSockets, and MongoDB.

## Features

- **Multi-Camera Support:** Supports webcams, RTSP streams, and video files.
- **Asynchronous Pipeline:** Cameras read in background threads, detection runs in independent workers, and alerts are dispatched asynchronously.
- **Real-Time Dashboard:** Dark-themed web UI with live MJPEG camera streaming and Chart.js analytics.
- **Behavior Analysis:**
  - **ROI Violations:** Polygon-based zone intrusion detection.
  - **Loitering:** Time-in-zone tracking via DeepSORT.
  - **Crowd Density:** Threshold-based headcount alerts.
- **Multi-Channel Alerts:** Telegram Bot, SMTP Email, and n8n Webhook integrations with smart cooldowns to prevent spam.
- **Persistent Storage:** MongoDB for event logs + Local disk for alert image snapshots (with auto-cleanup).

---

## Architecture

![Architecture](https://via.placeholder.com/800x400.png?text=CV+Monitor+Pro+Architecture)

The system consists of 7 layers:
1. `camera/` - Threaded stream acquisition
2. `detection/` - YOLOv8 + DeepSORT
3. `analysis/` - ROI, Loitering, Crowd detection
4. `database/` - MongoDB Motor async client
5. `storage/` - Disk I/O with auto-purge daemon
6. `alerts/` - Fan-out router
7. `api/` - FastAPI REST & WebSockets

---

## 🚀 Quick Start (Docker)

The easiest way to run the system (which includes MongoDB) is via Docker Compose.

1. **Clone & Configure:**
   ```bash
   git clone ...
   cd cv_monitor_pro
   cp .env.example .env
   # Edit .env to set TELEGRAM_BOT_TOKEN or EMAIL_PASSWORD if desired
   ```

2. **Run (CPU):**
   ```bash
   docker-compose up --build
   ```

3. **Run (GPU):**
   If you have an NVIDIA GPU and `nvidia-docker2` installed, uncomment the `deploy` block in `docker-compose.yml` and the `DEVICE=cuda:0` line before running.

4. **Access:**
   - Dashboard: `http://localhost:8000/dashboard`
   - API Docs: `http://localhost:8000/docs`

---

## 💻 Bare-Metal Setup (Local Server / Edge)

If running without Docker (e.g., on a Raspberry Pi or local Windows machine):

1. **Install MongoDB:** Ensure MongoDB 6.0+ is running locally on port 27017.
2. **Environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure:** Copy `.env.example` to `.env` and set `DEVICE=cpu` or `DEVICE=cuda:0`.
4. **Run:**
   ```powershell
   python main.py
   ```

---

## ⚙️ Configuration Hints

All major settings are in `config.py`.

- **Adding Cameras:** Edit the `CAMERAS` list in `config.py` to add new RTSP URLs.
- **Adding ROI Zones:** Define polygons in the `ROI_ZONES` dict in `config.py`. Coordinates map to the `FRAME_WIDTH` and `FRAME_HEIGHT` (default 960x540).
- **Tweaking Alerts:** Adjust `ALERT_COOLDOWN` in `.env` if you are getting too many or too few notifications for the same event.
