"""
api/main.py
===========
FastAPI application that serves the REST API and mounts the web dashboard.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

import config
from database.connection import DatabaseConnection

# Routers
from api.routes import cameras, events, alerts, ws

logger = logging.getLogger(__name__)

# The Main Orchestrator sets this globally so API routes can access it
CAMERA_MANAGER = None  
# Stored so background threads can submit async work to the main loop safely
MAIN_LOOP = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("[API] Starting up...")
    
    import asyncio
    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_running_loop()

    await DatabaseConnection.connect()
    yield
    # Shutdown
    logger.info("[API] Shutting down...")
    await DatabaseConnection.disconnect()

app = FastAPI(title="CV Monitor Pro API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(cameras.router, prefix="/api/cameras", tags=["cameras"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(ws.router, tags=["stream"])

# Mount static dashboard at /dashboard
dashboard_path = Path(config.BASE_DIR) / "dashboard"
if dashboard_path.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_path), html=True), name="dashboard")
    logger.info("[API] Mounted /dashboard UI")

@app.get("/api/health")
async def health():
    return {"status": "ok", "db": DatabaseConnection.client is not None}
