"""
api/routes/cameras.py
=====================
GET /api/cameras — Returns live status of all camera streams.
"""

from fastapi import APIRouter
from typing import List
from database.models import CameraStatus
import api.main  # to access CAMERA_MANAGER

router = APIRouter()

@router.get("/", response_model=List[CameraStatus])
async def get_cameras():
    """Get the live status, FPS, and properties of all connected cameras."""
    if api.main.CAMERA_MANAGER is None:
        return []
        
    return api.main.CAMERA_MANAGER.status()
