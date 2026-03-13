"""
detection/detector.py
=====================
YOLODetector — wraps YOLOv8 inference.
Uses the globally configured DEVICE (e.g. "cpu" or "cuda:0").
"""

import logging
from collections import namedtuple
from typing import List, Optional
import numpy as np

import config

logger = logging.getLogger(__name__)

Detection = namedtuple("Detection", ["class_name", "confidence", "bbox"])


class YOLODetector:
    def __init__(self):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise ImportError("pip install ultralytics") from exc

        model_path = config.YOLO_MODEL_PATH
        device     = config.DEVICE
        logger.info("[Detector] Loading YOLO model '%s' on %s", model_path, device.upper())
        self._model = YOLO(model_path)
        self._model.to(device)

        self._class_names   = self._model.names
        self.confidence     = config.CONFIDENCE_THRESHOLD
        self.target_classes = config.TARGET_CLASSES

    def detect(self, frame: np.ndarray) -> List[Detection]:
        # verbose=False prevents console spam per frame
        results = self._model(frame, verbose=False)
        detections = []

        for result in results:
            boxes = result.boxes
            for box in boxes:
                conf = float(box.conf[0])
                if conf < self.confidence:
                    continue

                cls_name = self._class_names.get(int(box.cls[0]), "unknown").lower()
                if self.target_classes and cls_name not in self.target_classes:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                bbox = (int(x1), int(y1), int(x2), int(y2))
                detections.append(Detection(cls_name, conf, bbox))

        return detections
