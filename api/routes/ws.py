"""
api/routes/ws.py
================
WebSocket route for real-time video streaming with bounding box overlays.
"""

import asyncio
import logging
import cv2
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK

import api.main
import config

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/stream/{camera_id}")
async def stream_video(websocket: WebSocket, camera_id: str):
    """
    Streams JPEG-encoded frames over WebSocket.
    The Client (JS dashboard) converts these directly to <img src="data:image/jpeg;base64,...">
    """
    await websocket.accept()
    logger.info("[WebSocket] Client connected to camera '%s'", camera_id)

    mgr = api.main.CAMERA_MANAGER
    if mgr is None or camera_id not in mgr.camera_ids():
        await websocket.close(reason="Camera not found or system not ready")
        return

    try:
        while True:
            success, frame = mgr.get_frame(camera_id)
            if not success or frame is None:
                await asyncio.sleep(0.1)
                continue

            # In a full-blown app, we'd take the raw frame and draw the latest tracked
            # boxes stored in memory here. For simplicity/efficiency, we're relying on 
            # the fact that our hooks can optionally draw on the frame before it gets here,
            # OR we just stream the raw frame and let the JS canvas draw the boxes.
            # Here we just encode and send the frame as MJPEG-over-Websockets.
            
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), config.WS_JPEG_QUALITY]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            
            await websocket.send_bytes(buffer.tobytes())
            
            # Throttle to roughly 30 fps to not overwhelm the network/browser
            await asyncio.sleep(1 / 30.0)

    except (WebSocketDisconnect, ConnectionClosedOK):
        logger.info("[WebSocket] Client disconnected from camera '%s'", camera_id)
    except Exception as e:
        logger.error("[WebSocket] Unhandled error: %s", e)
