"""
database/models.py
==================
Pydantic v2 models for MongoDB persistence and FastAPI response schemas.
"""

from typing import List, Tuple, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ObjectDet(BaseModel):
    """A single detected object."""
    track_id:   int
    class_name: str
    confidence: float
    bbox:       Tuple[int, int, int, int]


class DetectionEvent(BaseModel):
    """A single frame's detection results, stored periodically."""
    camera_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    objects:   List[ObjectDet]
    image_url: Optional[str] = None


class AlertRecord(BaseModel):
    """A high-value alert (e.g. ROI violation, loitering)."""
    camera_id:   str
    alert_type:  str   # "person_detected", "roi_violation", "loitering"
    severity:    str   # "info", "warning", "critical"
    message:     str
    timestamp:   datetime = Field(default_factory=datetime.utcnow)
    image_path:  Optional[str] = None
    notified:    bool = False


class CameraStatus(BaseModel):
    id:          str
    name:        str
    connected:   bool
    fps:         float
    frame_count: int
