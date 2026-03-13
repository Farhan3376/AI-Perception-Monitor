"""
storage/saver.py
================
Saves alert frames to disk as JPEG/PNG images.
"""

import os
import time
import logging
from datetime import datetime
import cv2
import numpy as np
from pathlib import Path

import config

logger = logging.getLogger(__name__)

class ImageSaver:
    @staticmethod
    def save_alert(camera_id: str, alert_type: str, frame: np.ndarray) -> str:
        """
        Saves a frame to disk. Returns the absolute file path.
        Folder structure: STORAGE_DIR / YYYY-MM-DD / camera_id_alert_type_HH-MM-SS.jpg
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S-%f")[:12]  # Include milliseconds

        folder = Path(config.STORAGE_DIR) / date_str
        folder.mkdir(parents=True, exist_ok=True)

        filename = f"{camera_id}_{alert_type}_{time_str}.jpg"
        filepath = folder / filename

        # Save with medium compression to save space
        success = cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        if success:
            logger.debug("[Storage] Saved alert image: %s", filepath)
            return str(filepath)
        else:
            logger.error("[Storage] Failed to save image: %s", filepath)
            return ""
