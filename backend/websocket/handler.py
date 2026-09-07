"""
WebSocket handler — the per-connection message loop.

Security (section 36):
- every message's type is validated against the protocol schema;
- payload size is capped at WS_MAX_MESSAGE_SIZE_BYTES;
- frame rate is capped at WS_MAX_FPS (excess frames are rejected with a
  clear error, not silently dropped -- easier to debug from the frontend);
- the connection is closed cleanly on protocol violations that indicate a
  misbehaving/hostile client (oversized payloads).

CV pipeline (Phase 6-7): each valid frame is decoded and run through the
real MediaPipe landmark extractor + normalization + feature vector builder.
This is genuine landmark extraction, not a stub -- but there is still no
trained temporal model (Phase 9-10), so the response is an honest error that
now also reports which modalities were actually detected, never a
fabricated sign prediction (section 40: "NO FAKE AI").
"""
from __future__ import annotations

import asyncio
import json
import time

from fastapi import WebSocket, WebSocketDisconnect
from ml.features.feature_vector import FeatureConfig, build_feature_vector, feature_vector_size
from ml.preprocessing.landmarks import (
    FeatureToggles,
    LandmarkExtractor,
    ModelNotFoundError,
)
from ml.preprocessing.normalization import normalize_frame
from ml.preprocessing.video_reader import FrameDecodeError, decode_base64_frame
from starlette.websockets import WebSocketState

from app.core.config import get_settings
from app.core.logging import get_logger
from websocket.manager import connection_manager
from websocket.protocol import ConnectionMessage, ErrorMessage, ProtocolError, parse_client_message

logger = get_logger(__name__)

_landmark_extractor: LandmarkExtractor | None = None
_landmark_extractor_error: str | None = None


def _get_landmark_extractor() -> LandmarkExtractor | None:
    """Lazily create the (process-wide, reused across connections) landmark
    extractor. If the model files aren't downloaded yet, cache the failure
    so we don't re-check the filesystem on every single frame -- but still
    surface a clear, actionable error to the client."""
    global _landmark_extractor, _landmark_extractor_error
    if _landmark_extractor is not None or _landmark_extractor_error is not None:
        return _landmark_extractor

    settings = get_settings()
    try:
        _landmark_extractor = LandmarkExtractor(
            model_dir=settings.mediapipe_models_dir,
            features=FeatureToggles(
                hands=settings.features_hands,
                pose=settings.features_pose,
                face=settings.features_face,
            ),
        )
    except ModelNotFoundError as exc:
        _landmark_extractor_error = str(exc)
        logger.warning("Landmark extractor unavailable: %s", _landmark_extractor_error)
    return _landmark_extractor



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
                frame_message = parse_client_message(raw)
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
                decoded_frame = decode_base64_frame(frame_message.data)
            except FrameDecodeError as exc:
                await websocket.send_json(
                    ErrorMessage(message=f"Could not decode frame: {exc}").model_dump()
                )
                continue

            extractor = _get_landmark_extractor()
            if extractor is None:
                await websocket.send_json(
                    ErrorMessage(
                        message=_landmark_extractor_error
                        or "Landmark extractor is not available."
                    ).model_dump()
                )
                continue

            # detect() is a blocking call; run it off the event loop so one
            # slow frame doesn't stall every other connection.
            raw_landmarks = await asyncio.to_thread(extractor.extract, decoded_frame)
            normalized = normalize_frame(raw_landmarks)

            feature_config = FeatureConfig(
                hands=settings.features_hands,
                pose=settings.features_pose,
                face=settings.features_face,
            )
            feature_vector = build_feature_vector(normalized, feature_config)

            # Real landmarks ARE extracted now (Phase 6-7) -- but there is still
            # no trained temporal model (Phase 9-10), so this stays an honest
            # error, now with real detection info instead of a fabricated sign.
            await websocket.send_json(
                ErrorMessage(
                    message=(
                        "Sign-recognition ML pipeline is not implemented yet "
                        "(Phase 9-10: no trained temporal model). Landmarks were "
                        f"extracted: left_hand={normalized.present['left_hand']}, "
                        f"right_hand={normalized.present['right_hand']}, "
                        f"pose={normalized.present['pose']}, "
                        f"face={normalized.present['face']} "
                        f"(feature vector size: {feature_vector.shape[0]}/"
                        f"{feature_vector_size(feature_config)})."
                    )
                ).model_dump()
            )

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
