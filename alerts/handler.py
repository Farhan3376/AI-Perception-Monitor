"""
alerts/handler.py
=================
AlertHandler — Receives raw events, applies cooldowns to prevent spam,
saves images, stores the alert in MongoDB, and dispatches to
all enabled notifiers asynchronously.
"""

import time
import logging
import asyncio
from typing import Dict, Tuple

import config
from storage.saver import ImageSaver
from database.models import AlertRecord
from database.repository import AlertRepository
from alerts.telegram import TelegramNotifier
from alerts.email_alert import EmailNotifier
from alerts.n8n import N8NNotifier

logger = logging.getLogger(__name__)

class AlertHandler:
    def __init__(self):
        # Maps (camera_id, alert_type) -> float (timestamp of last event)
        self._last_alert: Dict[Tuple[str, str], float] = {}

    def handle(self, alert_dict: dict, frame):
        """
        Synchronous entrypoint called by the DetectionPipeline loop.
        Spawns an asyncio task to handle the alert so it doesn't block the video thread.
        """
        camera_id  = alert_dict["camera_id"]
        alert_type = alert_dict["alert_type"]
        now = time.time()

        key = (camera_id, alert_type)
        last_time = self._last_alert.get(key, 0.0)

        # Apply cooldown to prevent spamming
        if now - last_time < config.ALERT_COOLDOWN_SECONDS:
            return

        self._last_alert[key] = now

        # Save image (synchronous, disk I/O)
        image_path = None
        if frame is not None:
            image_path = ImageSaver.save_alert(camera_id, alert_type, frame)

        alert_dict["image_path"] = image_path

        # Dispatch async work to the main event loop
        import api.main
        if api.main.MAIN_LOOP is not None:
            asyncio.run_coroutine_threadsafe(self._process_alert_async(alert_dict), api.main.MAIN_LOOP)
        else:
            logger.error("[AlertHandler] Main event loop not ready to process alert.")

    async def _process_alert_async(self, alert_dict: dict):
        # 1. Save to Database
        record = AlertRecord(**alert_dict)
        try:
            alert_id = await AlertRepository.insert(record)
            logger.info("[AlertHandler] Logged '%s' to DB (id: %s)", record.alert_type, alert_id)
        except Exception as e:
            logger.error("[AlertHandler] Failed to log alert to DB: %s", e)
            return

        message = f"[{record.severity.upper()}] {record.camera_id}: {record.message}"
        image_path = record.image_path

        # 2. Dispatch to Notifiers concurrently
        tasks = []
        
        if config.TELEGRAM_ENABLED:
            tasks.append(TelegramNotifier.send(message, image_path))
            
        if config.EMAIL_ENABLED:
            tasks.append(EmailNotifier.send(f"Alert: {record.alert_type}", message, image_path))
            
        if config.N8N_ENABLED:
            tasks.append(N8NNotifier.send(record.model_dump(mode='json'), image_path))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.error("[AlertHandler] Notifier exception: %s", r)
            
            # Mark as notified in DB
            await AlertRepository.mark_notified(alert_id)
