"""
analysis/roi.py
===============
ROIManager — Checks if bounding boxes intersect defined polygon zones.
"""

import cv2
import numpy as np
import logging
from typing import List, Dict

import config

logger = logging.getLogger(__name__)

class ROIManager:
    def __init__(self):
        # Pre-build numpy arrays for pointPolygonTest fast paths
        self._zones: Dict[str, List[dict]] = {}

        for cam_id, zones in config.ROI_ZONES.items():
            self._zones[cam_id] = []
            for z in zones:
                self._zones[cam_id].append({
                    "name":    z["name"],
                    "polygon": np.array(z["polygon"], dtype=np.int32),
                    "classes": set(z.get("classes", [])),
                })

    def check(self, camera_id: str, tracks) -> List[str]:
        """
        Check if any track centroid falls within ANY polygon for this camera.
        Returns a list of violation messages.
        """
        messages = []
        zones = self._zones.get(camera_id, [])
        if not zones or not tracks:
            return messages

        for t in tracks:
            # Calculate centroid of the bounding box
            x1, y1, x2, y2 = t.bbox
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0

            for z in zones:
                # If target classes are defined, skip unrelated classes
                if z["classes"] and t.class_name not in z["classes"]:
                    continue

                # OpenCV returns >= 0 if point is inside or exactly on the edge
                inside = cv2.pointPolygonTest(z["polygon"], (cx, cy), measureDist=False) >= 0

                if inside:
                    track_str = f"#{t.track_id} " if hasattr(t, "track_id") else ""
                    messages.append(
                        f"ROI Violation in '{z['name']}': {track_str}{t.class_name.upper()} detected."
                    )

        return messages
