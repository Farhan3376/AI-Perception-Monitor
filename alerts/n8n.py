"""
alerts/n8n.py
=============
Async Webhook notifier for n8n or any custom HTTP endpoint.
"""

import logging
from typing import Optional
import aiohttp
import json

import config

logger = logging.getLogger(__name__)

class N8NNotifier:
    @staticmethod
    async def send(payload: dict, image_path: Optional[str] = None):
        """
        payload: The JSON representation of the alert
        """
        if not config.N8N_ENABLED:
            return

        if not config.N8N_WEBHOOK_URL:
            logger.error("[n8n] Enabled but N8N_WEBHOOK_URL missing.")
            return

        try:
            async with aiohttp.ClientSession() as session:
                if image_path:
                    # Multipart form-data with JSON payload and file
                    data = aiohttp.FormData()
                    data.add_field("payload", json.dumps(payload))
                    with open(image_path, "rb") as f:
                        data.add_field("image", f, filename="alert.jpg")
                        
                    async with session.post(config.N8N_WEBHOOK_URL, data=data) as resp:
                        if resp.status >= 400:
                            err = await resp.text()
                            logger.error("[n8n] Webhook failed %d: %s", resp.status, err)
                else:
                    # Simple JSON POST
                    async with session.post(config.N8N_WEBHOOK_URL, json=payload) as resp:
                        if resp.status >= 400:
                            err = await resp.text()
                            logger.error("[n8n] Webhook failed %d: %s", resp.status, err)
                            
                logger.debug("[n8n] Webhook triggered successfully.")
        except Exception as e:
            logger.error("[n8n] Exception calling webhook: %s", e)
