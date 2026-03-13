"""
api/routes/alerts.py
====================
GET /api/alerts — Fetch high-value alert records.
"""

from fastapi import APIRouter, Query
from typing import Optional
from database.repository import AlertRepository

router = APIRouter()

@router.get("/")
async def get_alerts(
    limit: int = Query(50, ge=1, le=500, description="Max alerts to return")
):
    """Get the history of trigger alerts (loitering, ROI, person detected)."""
    alerts = await AlertRepository.get_recent(limit)
    
    for a in alerts:
        a["id"] = str(a.pop("_id"))
        
    return alerts
