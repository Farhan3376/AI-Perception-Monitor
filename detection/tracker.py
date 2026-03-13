"""
detection/tracker.py
====================
DeepSORTTracker — multi-object tracking.
Each camera stream should instantiate its own tracker to keep IDs isolated.
"""

import logging
from collections import namedtuple
from typing import List
import numpy as np

from detection.detector import Detection
import config

logger = logging.getLogger(__name__)

Track = namedtuple("Track", ["track_id", "class_name", "confidence", "bbox"])


class DeepSORTTracker:
    def __init__(self):
        self._fallback = False
        try:
            from deep_sort_realtime.deepsort_tracker import DeepSort
            self._tracker = DeepSort(
                max_age=config.TRACKER_MAX_AGE,
                nn_budget=100,
                embedder="mobilenet",
                half=False,
                bgr=True
            )
        except ImportError:
            logger.warning("[Tracker] deep_sort_realtime missing. Using fallback IDs.")
            self._fallback = True

    def update(self, detections: List[Detection], frame: np.ndarray) -> List[Track]:
        if self._fallback or not detections:
            return [
                Track(abs(hash((d.bbox[0], d.bbox[1]))) % 9999, d.class_name, d.confidence, d.bbox)
                for d in detections
            ]

        ds_input = []
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            w, h = x2 - x1, y2 - y1
            ds_input.append(([x1, y1, w, h], det.confidence, det.class_name))

        raw_tracks = self._tracker.update_tracks(ds_input, frame=frame)
        tracks = []
        for t in raw_tracks:
            if not t.is_confirmed():
                continue
            ltrb = t.to_ltrb()
            bbox = (int(ltrb[0]), int(ltrb[1]), int(ltrb[2]), int(ltrb[3]))
            tracks.append(
                Track(
                    track_id=t.track_id,
                    class_name=t.get_det_class(),
                    confidence=t.get_det_conf() or 0.0,
                    bbox=bbox,
                )
            )
        return tracks
