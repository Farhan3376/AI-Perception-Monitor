"""
camera/stream.py
================
CameraStream — daemon thread reading frames from one camera source.
"""

import threading
import time
import logging
import cv2
import sys
import numpy as np
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class CameraStream:
    def __init__(self, camera_id: str, source, width: int = 960, height: int = 540, name: str = ""):
        self.camera_id = camera_id
        self.source    = source
        self.width     = width
        self.height    = height
        self.name      = name or camera_id

        self._frame:  Optional[np.ndarray] = None
        self._lock    = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self.fps:           float = 0.0
        self.frame_count:   int   = 0
        self.connected:     bool  = False
        self._fps_counter_t: float = time.perf_counter()
        self._fps_frames:    int   = 0

    def start(self) -> "CameraStream":
        self._running = True
        self._thread  = threading.Thread(
            target=self._reader_loop, daemon=True, name=f"stream-{self.camera_id}"
        )
        self._thread.start()
        logger.info("[Stream:%s] Started — %s", self.camera_id, self.source)
        return self

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("[Stream:%s] Stopped.", self.camera_id)

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self._lock:
            if self._frame is None:
                return False, None
            return True, self._frame.copy()

    def _open_capture(self) -> cv2.VideoCapture:
        is_local = isinstance(self.source, int)
        is_win   = sys.platform.startswith("win")
        backend  = cv2.CAP_DSHOW if (is_local and is_win) else cv2.CAP_ANY
        cap = cv2.VideoCapture(self.source, backend)
        if is_local:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return cap

    def _reader_loop(self):
        retry_delay = 2
        while self._running:
            cap = self._open_capture()
            if not cap.isOpened():
                logger.warning("[Stream:%s] Cannot open — retrying in %ds", self.camera_id, retry_delay)
                self.connected = False
                time.sleep(retry_delay)
                continue

            self.connected = True
            logger.info("[Stream:%s] Connected", self.camera_id)

            while self._running:
                ok, frame = cap.read()
                if not ok:
                    logger.warning("[Stream:%s] Read failed — reconnecting", self.camera_id)
                    break

                frame = cv2.resize(frame, (self.width, self.height))

                with self._lock:
                    self._frame = frame

                self.frame_count += 1
                self._fps_frames += 1
                now = time.perf_counter()
                elapsed = now - self._fps_counter_t
                if elapsed >= 1.0:
                    self.fps = self._fps_frames / elapsed
                    self._fps_frames   = 0
                    self._fps_counter_t = now

            cap.release()
            self.connected = False
            if self._running:
                time.sleep(retry_delay)
