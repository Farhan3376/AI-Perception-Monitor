"""
analysis/crowd.py
=================
CrowdDetector — Counts the number of persons in a frame.
Fires an alert if the headcount exceeds config.CROWD_THRESHOLD.
"""

import logging
from typing import List

import config

logger = logging.getLogger(__name__)

class CrowdDetector:
    def check(self, camera_id: str, tracks) -> List[dict]:
        """Check if headcount > CROWD_THRESHOLD."""
        alerts = []
        threshold = config.CROWD_THRESHOLD

        if threshold <= 0:
            return alerts

        person_count = sum(1 for t in tracks if t.class_name == "person")

        # In a real app we might want debouncing/hysteresis here so it doesn't
        # flap on and off rapidly, but the AlertHandler's cooldown will handle that.
        if person_count >= threshold:
            msg = f"Crowd detected! {person_count} persons visible (threshold: {threshold})"
            logger.warning("[Crowd] %s", msg)
            alerts.append({
                "camera_id":  camera_id,
                "alert_type": "crowd",
                "severity":   "warning",
                "message":    msg,
            })

        return alerts
