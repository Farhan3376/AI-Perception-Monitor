"""
storage/cleanup.py
==================
Background task to delete old images from STORAGE_DIR
to prevent the disk from filling up over time.
"""

import os
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta

import config
from database.repository import EventRepository

logger = logging.getLogger(__name__)

class StorageCleanup(threading.Thread):
    def __init__(self):
        super().__init__(name="StorageCleanup", daemon=True)
        self._running = False
        # Run cleanup once every hour
        self.interval_seconds = 3600

    def start(self):
        self._running = True
        super().start()
        logger.info("[Cleanup] Storage auto-cleanup started (Max Age: %s days).", config.STORAGE_MAX_AGE_DAYS)

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            self._cleanup_files()
            # Also purge old DB events to keep Mongo lean
            # Need an event loop to call async DB methods from this sync thread
            self._cleanup_db()
            
            # Sleep in small chunks so we can exit cleanly on shutdown
            for _ in range(self.interval_seconds):
                if not self._running:
                    break
                time.sleep(1)

    def _cleanup_files(self):
        cutoff = time.time() - (config.STORAGE_MAX_AGE_DAYS * 86400)
        deleted_count = 0
        bytes_freed = 0

        storage_path = Path(config.STORAGE_DIR)
        if not storage_path.exists():
            return

        for root, dirs, files in os.walk(storage_path):
            for file in files:
                filepath = Path(root) / file
                try:
                    stats = filepath.stat()
                    if stats.st_mtime < cutoff:
                        filepath.unlink()
                        deleted_count += 1
                        bytes_freed += stats.st_size
                except Exception as e:
                    logger.debug("Failed to check/delete file %s: %s", filepath, e)

            # Try to remove empty year/month date directories
            try:
                if not os.listdir(root):
                    os.rmdir(root)
            except Exception:
                pass

        if deleted_count > 0:
            mb = bytes_freed / (1024 * 1024)
            logger.info("[Cleanup] Deleted %d old files (%.2f MB freed).", deleted_count, mb)

    def _cleanup_db(self):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            deleted = loop.run_until_complete(EventRepository.delete_older_than(config.STORAGE_MAX_AGE_DAYS))
            if deleted > 0:
                logger.info("[Cleanup] Purged %d old DB events.", deleted)
            loop.close()
        except Exception as e:
            logger.error("[Cleanup] DB purge failed: %s", e)
