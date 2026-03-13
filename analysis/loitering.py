"""
analysis/loitering.py
=====================
LoiteringDetector — Tracks how long an object (with a track_id) stays in frame
(or inside an ROI). Fires a loitering event when a threshold is exceeded.
"""

import time
import logging
from typing import Dict, List

import config

logger = logging.getLogger(__name__)


class LoiteringDetector:
    def __init__(self):
        # Maps (camera_id, track_id) to the first time it was seen.
        self._first_seen: Dict[tuple, float] = {}
        # Maps (camera_id, track_id) to boolean (already warned).
        self._warned: Dict[tuple, bool] = {}

    def check(self, camera_id: str, tracks) -> List[dict]:
        """
        Check track dwell times against config.LOITERING_SECONDS.
        Returns a list of alert dicts for objects that just exceeded the threshold.
        """
        alerts = []
        now = time.time()
        threshold = config.LOITERING_SECONDS

        # Track IDs present in the current frame
        current_ids = set()

        for t in tracks:
            # We must have a DeepSORT track ID to measure dwell time reliably.
            if not hasattr(t, "track_id") or t.class_name != "person":
                continue

            tid = t.track_id
            key = (camera_id, tid)
            current_ids.add(key)

            if key not in self._first_seen:
                self._first_seen[key] = now
                self._warned[key] = False
            else:
                elapsed = now - self._first_seen[key]
                if elapsed >= threshold and not self._warned[key]:
                    self._warned[key] = True
                    msg = f"Person #{tid} loitering for {elapsed:.1f}s"
                    logger.warning("[Loitering] %s", msg)
                    alerts.append({
                        "camera_id":  camera_id,
                        "alert_type": "loitering",
                        "severity":   "warning",
                        "message":    msg,
                    })

        # Housekeeping: remove IDs that are no longer in frame
        lost_keys = [k for k in self._first_seen.keys() if k[0] == camera_id and k not in current_ids]
        for k in lost_keys:
            del self._first_seen[k]
            del self._warned[k]

        return alerts
