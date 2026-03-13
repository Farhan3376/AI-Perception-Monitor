"""
config.py — Production CV Monitoring System
============================================
All settings are defined here and can be overridden via environment variables
(loaded from .env by python-dotenv at import time).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
STORAGE_DIR = BASE_DIR / os.getenv("STORAGE_DIR", "data/alerts")
LOG_DIR     = BASE_DIR / "logs"

# Ensure directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Camera Sources ────────────────────────────────────────────────────────
# List of camera definitions. Each entry is a dict with:
#   id     : unique string identifier
#   source : int (webcam index) or URL string (RTSP/HTTP/file path)
#   name   : human-readable label shown in the dashboard
CAMERAS = [
    {"id": "cam0", "source": 0,  "name": "Front Door"},
    # {"id": "cam1", "source": "rtsp://user:pass@192.168.1.10/stream", "name": "Parking Lot"},
]

# ── YOLO Model ─────────────────────────────────────────────────────────────
YOLO_MODEL_PATH       = os.getenv("YOLO_MODEL", "yolov8n.pt")
CONFIDENCE_THRESHOLD  = float(os.getenv("CONFIDENCE", "0.45"))
TARGET_CLASSES        = ["person", "car", "bicycle", "motorcycle", "dog", "cat", "bird"]
# Device: "cpu" always works; "cuda:0" requires an NVIDIA GPU + CUDA drivers.
DEVICE                = os.getenv("DEVICE", "cpu")

# ── Object Tracking ────────────────────────────────────────────────────────
ENABLE_TRACKING  = True
TRACKER_MAX_AGE  = 30   # frames before a lost track is deleted

# ── ROI Zones ──────────────────────────────────────────────────────────────
# Named polygon zones per camera.  Detections inside trigger ROI_VIOLATION events.
# Coordinates are in pixels on the resized frame.
ROI_ZONES = {
    "cam0": [
        {
            "name":    "Restricted Area",
            "polygon": [(300, 150), (660, 150), (660, 390), (300, 390)],
            "classes": ["person"],
        }
    ]
}

# ── Frame Resolution  ──────────────────────────────────────────────────────
FRAME_WIDTH  = int(os.getenv("FRAME_WIDTH",  "960"))
FRAME_HEIGHT = int(os.getenv("FRAME_HEIGHT", "540"))

# ── Behavior Analysis ──────────────────────────────────────────────────────
LOITERING_SECONDS    = int(os.getenv("LOITERING_SECONDS", "10"))
CROWD_THRESHOLD      = int(os.getenv("CROWD_THRESHOLD",   "5"))

# ── Event / Alert Cooldowns ────────────────────────────────────────────────
ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN", "30"))

# ── MongoDB ────────────────────────────────────────────────────────────────
MONGO_URI  = os.getenv("MONGO_URI",  "mongodb://127.0.0.1:27017")
MONGO_DB   = os.getenv("MONGO_DB",   "cv_monitor")

# ── Storage ────────────────────────────────────────────────────────────────
STORAGE_MAX_AGE_DAYS = int(os.getenv("STORAGE_MAX_AGE_DAYS", "30"))

# ── API ────────────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
WS_JPEG_QUALITY = int(os.getenv("WS_JPEG_QUALITY", "70"))

# ── Alerts ─────────────────────────────────────────────────────────────────
TELEGRAM_ENABLED   = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "")

EMAIL_ENABLED   = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
EMAIL_FROM      = os.getenv("EMAIL_FROM",      "")
EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD",  "")
EMAIL_TO        = os.getenv("EMAIL_TO",        "")
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))

N8N_ENABLED     = os.getenv("N8N_ENABLED", "false").lower() == "true"
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

# ── Logging ────────────────────────────────────────────────────────────────
LOG_LEVEL          = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE           = str(LOG_DIR / "cv_monitor.log")
LOG_MAX_BYTES      = 10 * 1024 * 1024
LOG_BACKUP_COUNT   = 5
