"""
api/routes/events.py
====================
GET /api/events — Paginated historical detection events.
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from database.repository import EventRepository

router = APIRouter()

@router.get("/")
async def get_events(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    limit: int = Query(50, ge=1, le=1000, description="Max number of events to return")
):
    """Get the most recent detection events (bbox arrays per frame)."""
    events = await EventRepository.get_recent(camera_id, limit)
    
    # Custom serialization because Motor returns ObjectIds for _id
    for e in events:
        e["id"] = str(e.pop("_id"))
        
    return events
