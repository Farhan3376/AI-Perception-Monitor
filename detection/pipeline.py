"""
detection/pipeline.py
=====================
DetectionPipeline — Runs in a background thread per camera.
Takes frames from CameraManager, runs detection + tracking,
and emits results to the Behaviour Analysis & Database layers.
"""

import logging
import threading
import time
from typing import Callable, Optional

from detection.detector import YOLODetector
from detection.tracker  import DeepSORTTracker
import config

logger = logging.getLogger(__name__)


class DetectionPipeline:
    def __init__(self, camera_id: str, camera_manager, callback: Callable):
        """
        camera_manager : must have get_frame(camera_id)
        callback       : func(camera_id, frame, tracks) called on each processed frame
        """
        self.camera_id = camera_id
        self._cam_mgr  = camera_manager
        self._callback = callback

        self._detector: Optional[YOLODetector] = None
        self._tracker:  Optional[DeepSORTTracker] = None

        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name=f"pipeline-{self.camera_id}"
        )
        self._thread.start()
        logger.info("[Pipeline:%s] Started.", self.camera_id)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        logger.info("[Pipeline:%s] Stopped.", self.camera_id)

    def _worker_loop(self):
        # Lazy load heavy ML models only inside the worker thread
        self._detector = YOLODetector()
        if config.ENABLE_TRACKING:
            self._tracker = DeepSORTTracker()

        while self._running:
            ok, frame = self._cam_mgr.get_frame(self.camera_id)
            if not ok or frame is None:
                time.sleep(0.05)
                continue

            # 1. Detect
            detections = self._detector.detect(frame)

            # 2. Track
            if self._tracker:
                tracks = self._tracker.update(detections, frame)
            else:
                tracks = detections

            # 3. Emit upwards
            self._callback(self.camera_id, frame, tracks)

            # A tiny sleep to yield to other threads (important when CPU-bound)
            time.sleep(0.005)
