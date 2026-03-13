"""
database/connection.py
======================
Async MongoDB client setup and teardown.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
import config

logger = logging.getLogger(__name__)

class DatabaseConnection:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect(cls):
        """Connect to MongoDB and ensure indexes exist."""
        logger.info("[DB] Connecting to MongoDB: %s", config.MONGO_URI)
        try:
            # ServerSelectionTimeout is short so we fail fast if Mongo is down
            cls.client = AsyncIOMotorClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
            await cls.client.admin.command('ping')
            cls.db = cls.client[config.MONGO_DB]
            logger.info("[DB] Connected to database '%s'", config.MONGO_DB)
            await cls._create_indexes()
        except Exception as e:
            logger.error("[DB] Failed to connect to MongoDB: %s", e)
            raise

    @classmethod
    async def disconnect(cls):
        """Close the MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("[DB] Disconnected.")

    @classmethod
    async def _create_indexes(cls):
        # Create descending index on timestamp for fast time-series queries
        await cls.db.events.create_index([("timestamp", -1)])
        await cls.db.events.create_index("camera_id")

        await cls.db.alerts.create_index([("timestamp", -1)])
        await cls.db.alerts.create_index("camera_id")
        await cls.db.alerts.create_index("alert_type")
