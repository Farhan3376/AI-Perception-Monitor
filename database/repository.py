"""
database/repository.py
======================
Repository pattern for database operations.
Abstracts the raw Motor queries behind clean async functions.
"""

from typing import List, Optional
from database.connection import DatabaseConnection
from database.models import DetectionEvent, AlertRecord


class EventRepository:
    @staticmethod
    async def insert(event: DetectionEvent) -> str:
        """Insert a single detection event (1 frame's results)."""
        doc = event.model_dump()
        result = await DatabaseConnection.db.events.insert_one(doc)
        return str(result.inserted_id)

    @staticmethod
    async def get_recent(camera_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        """Fetch the most recent events, optionally filtered by camera."""
        query = {"camera_id": camera_id} if camera_id else {}
        cursor = DatabaseConnection.db.events.find(query).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    @staticmethod
    async def delete_older_than(days: int) -> int:
        """Purge old events to free up space."""
        if DatabaseConnection.db is None:
            return 0
            
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        res = await DatabaseConnection.db.events.delete_many({"timestamp": {"$lt": cutoff}})
        return res.deleted_count


class AlertRepository:
    @staticmethod
    async def insert(alert: AlertRecord) -> str:
        doc = alert.model_dump()
        result = await DatabaseConnection.db.alerts.insert_one(doc)
        return str(result.inserted_id)

    @staticmethod
    async def get_recent(limit: int = 50) -> List[dict]:
        cursor = DatabaseConnection.db.alerts.find().sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    @staticmethod
    async def mark_notified(alert_id: str):
        from bson import ObjectId
        await DatabaseConnection.db.alerts.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {"notified": True}}
        )
