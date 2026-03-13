"""
camera/manager.py
=================
CameraManager — creates, starts and manages all CameraStream instances.
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

from camera.stream import CameraStream
import config

logger = logging.getLogger(__name__)


class CameraManager:
    def __init__(self):
        self._streams: Dict[str, CameraStream] = {}

    def start_all(self):
        for cam in config.CAMERAS:
            cam_id  = cam["id"]
            source  = cam["source"]
            name    = cam.get("name", cam_id)
            stream  = CameraStream(cam_id, source, config.FRAME_WIDTH, config.FRAME_HEIGHT, name)
            self._streams[cam_id] = stream.start()
            logger.info("[CameraManager] Registered camera '%s'", name)

    def stop_all(self):
        for stream in self._streams.values():
            stream.stop()
        logger.info("[CameraManager] All streams stopped.")

    def get_frame(self, camera_id: str) -> Tuple[bool, Optional[np.ndarray]]:
        stream = self._streams.get(camera_id)
        if stream:
            return stream.get_frame()
        return False, None

    def camera_ids(self) -> List[str]:
        return list(self._streams.keys())

    def status(self) -> List[dict]:
        return [
            {
                "id":          cam_id,
                "name":        stream.name,
                "connected":   stream.connected,
                "fps":         round(stream.fps, 1),
                "frame_count": stream.frame_count,
                "source":      str(stream.source),
            }
            for cam_id, stream in self._streams.items()
        ]
