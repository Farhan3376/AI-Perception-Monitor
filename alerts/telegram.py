"""
alerts/telegram.py
==================
Async Telegram Bot notifier.
"""

import logging
from typing import Optional
import aiohttp

import config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    @staticmethod
    async def send(message: str, image_path: Optional[str] = None):
        if not config.TELEGRAM_ENABLED:
            return

        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
            logger.error("[Telegram] Enabled but token/chat_id missing.")
            return

        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/"
        
        try:
            async with aiohttp.ClientSession() as session:
                if image_path:
                    # Send Photo with caption
                    with open(image_path, "rb") as f:
                        data = aiohttp.FormData()
                        data.add_field("chat_id", config.TELEGRAM_CHAT_ID)
                        data.add_field("caption", message)
                        data.add_field("photo", f, filename="alert.jpg")
                        
                        async with session.post(url + "sendPhoto", data=data) as resp:
                            if resp.status != 200:
                                err = await resp.text()
                                logger.error("[Telegram] Photo failed: %s", err)
                else:
                    # Send text only
                    payload = {"chat_id": config.TELEGRAM_CHAT_ID, "text": message}
                    async with session.post(url + "sendMessage", json=payload) as resp:
                        if resp.status != 200:
                            err = await resp.text()
                            logger.error("[Telegram] Text failed: %s", err)
                
                logger.debug("[Telegram] Alert sent successfully.")
        except Exception as e:
            logger.error("[Telegram] Exception sending alert: %s", e)
