"""
WebSocket handler — the per-connection message loop.

Security (section 36):
- every message's type is validated against the protocol schema;
- payload size is capped at WS_MAX_MESSAGE_SIZE_BYTES;
- frame rate is capped at WS_MAX_FPS (excess frames are rejected with a
  clear error, not silently dropped -- easier to debug from the frontend);
- the connection is closed cleanly on protocol violations that indicate a
  misbehaving/hostile client (oversized payloads).

ML honesty (section 40): no CV/temporal model exists yet (Phase 6-10), so a
valid frame gets an honest "not implemented" error, never a fabricated
prediction. This makes the handler trivial to upgrade later: only the single
marked block below needs to change once InferenceService has a real
implementation.
"""
from __future__ import annotations

import json
import time

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.inference_service import MLNotReadyError, NotConfiguredInferenceService
from websocket.manager import connection_manager
from websocket.protocol import ConnectionMessage, ErrorMessage, ProtocolError, parse_client_message

logger = get_logger(__name__)

# Phase 6-10 will replace this with a real, checkpoint-backed InferenceService
# (selected via settings.model_type), without changing the loop below.
_inference_service = NotConfiguredInferenceService()


async def websocket_endpoint(websocket: WebSocket) -> None:
    settings = get_settings()
    conn_id = await connection_manager.connect(websocket)
    await websocket.send_json(ConnectionMessage(status="ok").model_dump())

    min_interval_sec = 1.0 / settings.ws_max_fps
    last_frame_at = 0.0
    frames_received = 0
    already_closed = False

    try:
        while True:
            raw_text = await websocket.receive_text()

            if len(raw_text.encode("utf-8")) > settings.ws_max_message_size_bytes:
                logger.warning("WebSocket id=%s sent oversized message, closing", conn_id)
                await websocket.send_json(
                    ErrorMessage(
                        message=(
                            f"Message exceeds maximum allowed size of "
                            f"{settings.ws_max_message_size_bytes} bytes"
                        )
                    ).model_dump()
                )
                await websocket.close(code=1009)  # 1009 = message too big
                already_closed = True
                break

            try:
                raw = json.loads(raw_text)
            except json.JSONDecodeError:
                await websocket.send_json(
                    ErrorMessage(message="Message is not valid JSON").model_dump()
                )
                continue

            try:
                # Parsed and validated now; Phase 6-7 will consume `.data`
                # (base64 JPEG) here to run MediaPipe landmark extraction.
                parse_client_message(raw)
            except ProtocolError as exc:
                await websocket.send_json(ErrorMessage(message=str(exc)).model_dump())
                continue

            now = time.monotonic()
            if now - last_frame_at < min_interval_sec:
                await websocket.send_json(
                    ErrorMessage(
                        message=(
                            f"Frame rate exceeds configured max of {settings.ws_max_fps} FPS; "
                            "frame dropped"
                        )
                    ).model_dump()
                )
                continue
            last_frame_at = now
            frames_received += 1

            try:
                # No landmarks extracted yet in Phase 5 -- CV pipeline lands in
                # Phase 6-7. This call always raises today; kept explicit so the
                # honest-error path and the future real-prediction path are the
                # same code shape.
                prediction = _inference_service.predict(landmark_sequence=[])
                await websocket.send_json(
                    {
                        "type": "final_prediction" if prediction.is_final else "prediction",
                        "text": prediction.text,
                        "confidence": prediction.confidence,
                        "is_final": prediction.is_final,
                    }
                )
            except MLNotReadyError as exc:
                await websocket.send_json(ErrorMessage(message=str(exc)).model_dump())

            if frames_received % 30 == 0:
                logger.info(
                    "WebSocket id=%s received %s frames so far (message payloads not logged)",
                    conn_id,
                    frames_received,
                )

    except WebSocketDisconnect:
        logger.info("WebSocket id=%s disconnected by client", conn_id)
    finally:
        connection_manager.disconnect(conn_id)
        if not already_closed and websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close()
            except RuntimeError:
                # Already closed by the ASGI server between our check and this call.
                pass
