"""
main.py
=======
The ultimate orchestrator.
Initializes the loggers, starts the camera manager, storage cleanup,
instantiates the detection pipelines, alert handlers, and behavior
checkers. Finally, it launches the FastAPI Uvicorn server.
"""

import threading
import time
import logging
import asyncio
import cv2
import uvicorn

import config
from monitoring.logger import setup_logging
from camera.manager import CameraManager
from detection.pipeline import DetectionPipeline
from storage.cleanup import StorageCleanup
from analysis.roi import ROIManager
from analysis.loitering import LoiteringDetector
from analysis.crowd import CrowdDetector
from alerts.handler import AlertHandler
from database.models import DetectionEvent
from database.repository import EventRepository

# Need to inject the CameraManager into the API routes so they can stream WS
import api.main 

def launch_system():
    setup_logging()
    logger = logging.getLogger("SystemHost")
    logger.info("=====================================================")
    logger.info("  CV Monitor Pro — Starting Up")
    logger.info("=====================================================")

    # 1. Camera Manager (Background Threads)
    cam_mgr = CameraManager()
    cam_mgr.start_all()
    api.main.CAMERA_MANAGER = cam_mgr  # Inject global

    # 2. Behavior Analysis
    roi_mgr = ROIManager()
    loiter_det = LoiteringDetector()
    crowd_det = CrowdDetector()

    # 3. Alert Handler
    alert_handler = AlertHandler()

    # 4. Storage Auto-Cleanup
    cleanup = StorageCleanup()
    cleanup.start()

    # --- The Core Event Loop Callback ---
    # This runs inside the DetectionPipeline worker threads on EVERY frame.
    def on_frame_processed(camera_id: str, frame, tracks):
        # 1. Behavior Checks -> Alerts
        roi_alerts = roi_mgr.check(camera_id, tracks)
        for msg in roi_alerts:
            alert_handler.handle({
                "camera_id": camera_id,
                "alert_type": "roi_violation",
                "severity": "critical",
                "message": msg
            }, frame)

        loiter_alerts = loiter_det.check(camera_id, tracks)
        for al in loiter_alerts:
            alert_handler.handle(al, frame)

        crowd_alerts = crowd_det.check(camera_id, tracks)
        for al in crowd_alerts:
            alert_handler.handle(al, frame)

        # 2. Person Detected generic alert
        if any(t.class_name == "person" for t in tracks):
            alert_handler.handle({
                "camera_id": camera_id,
                "alert_type": "person_detected",
                "severity": "info",
                "message": "Person detected in frame"
            }, frame)

        # 3. Draw HUD text on the frame (since the UI streams it raw MJPEG)
        for i, text in enumerate(roi_alerts[:3]):  # Show max 3 alerts on HUD to avoid clutter
            cv2.putText(frame, "(!)" + text, (15, 30 + (i*25)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # 4. Periodically stash raw events to DB (e.g. 1 frame every 2 seconds)
        # We don't save EVERY frame to the DB, that would flood it.
        # We use a dirty trick inside the thread to rate limit event logging:
        t = time.time()
        if not hasattr(threading.current_thread(), "_last_db_save"):
            threading.current_thread()._last_db_save = 0.0

        if t - threading.current_thread()._last_db_save > 2.0:
            threading.current_thread()._last_db_save = t
            objs = [{"track_id": getattr(tk, "track_id", -1), 
                     "class_name": tk.class_name, 
                     "confidence": tk.confidence, 
                     "bbox": tk.bbox} for tk in tracks]
                     
            if objs:
                ev = DetectionEvent(camera_id=camera_id, objects=objs)
                if api.main.MAIN_LOOP is not None:
                    try:
                        # Threadsafe hand-off to the main event loop
                        asyncio.run_coroutine_threadsafe(EventRepository.insert(ev), api.main.MAIN_LOOP)
                    except Exception as e:
                        logger.error("Failed to insert detection event: %s", e)


    # 5. Pipeline Workers
    pipelines = []
    for cam_id in cam_mgr.camera_ids():
        p = DetectionPipeline(cam_id, cam_mgr, on_frame_processed)
        p.start()
        pipelines.append(p)

    logger.info("[SystemHost] Background layers initialized. Starting FastAPI...")

    # 6. Start API (Blocking)
    uvicorn.run(api.main.app, host=config.API_HOST, port=config.API_PORT, access_log=False)

    # 7. Teardown
    logger.info("[SystemHost] Shutting down...")
    for p in pipelines:
        p.stop()
    cleanup.stop()
    cam_mgr.stop_all()


if __name__ == "__main__":
    launch_system()
