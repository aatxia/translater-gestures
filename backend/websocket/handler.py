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

Inference (Phase 9-10): feature vectors are buffered into a sliding window
(per connection); once the window is full, it's run through a trained
LSTM checkpoint if one exists. If no checkpoint has been trained yet, the
response stays an honest error reporting which modalities were actually
detected -- never a fabricated sign prediction (section 40: "NO FAKE AI").

Gloss aggregation (Phase 11): raw per-frame predictions are debounced by
GlossSequenceAggregator (ml/inference/aggregator.py) into a stable gloss
sequence -- most frames are still interim ("prediction", is_final=False);
a "final_prediction" (is_final=True) fires only when the same gloss has
been predicted `WS_GLOSS_STABILITY_FRAMES` times in a row above
`WS_GLOSS_CONFIDENCE_THRESHOLD`.

Facial grammar (Phase 17): every frame with a detected face is fed to a
per-connection BaselineCalibrator (ml/features/facial_grammar.py) --
independent of whether sign inference has a trained checkpoint, since it
serves a separate purpose. Once calibrated, its eyebrow-position marker
rides along on every PredictionMessage ("facial_grammar"), and flips a
just-confirmed gloss's composed text to a question ("?" instead of ".").
"""
from __future__ import annotations

import asyncio
import json
import time
from collections import deque

from fastapi import WebSocket, WebSocketDisconnect
from ml.features.facial_grammar import BaselineCalibrator, FacialGrammarMarker
from ml.features.feature_vector import (
    FeatureConfig,
    build_feature_vector,
    feature_vector_size,
)
from ml.inference.aggregator import GlossSequenceAggregator
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
from app.services.inference_provider import get_inference_service
from app.services.inference_service import MLNotReadyError
from app.services.translation_service import RuleBasedTranslationService
from websocket.manager import connection_manager
from websocket.protocol import (
    ConnectionMessage,
    ErrorMessage,
    PredictionMessage,
    ProtocolError,
    parse_client_message,
)

logger = get_logger(__name__)

# Stateless (a small hand-authored lexicon, see ml/nlp/gloss_to_text.py) --
# unlike the landmark extractor / inference service, there's nothing here
# worth lazily loading or caching failure state for.
translation_service = RuleBasedTranslationService()

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
    # Per-connection: an isolated sliding window per signer, sized to the
    # loaded checkpoint's sequence_length once (if) inference is ready.
    feature_buffer: deque[list[float]] | None = None
    # Per-connection: debounces the raw per-frame prediction stream into a
    # stable gloss sequence (Phase 11 -- see ml/inference/aggregator.py).
    gloss_aggregator = GlossSequenceAggregator(
        stability_frames=settings.ws_gloss_stability_frames,
        confidence_threshold=settings.ws_gloss_confidence_threshold,
    )
    # Per-connection: calibrates against this signer's own neutral face,
    # then classifies eyebrow position into a non-manual grammar marker
    # (Phase 17 -- see ml/features/facial_grammar.py).
    facial_calibrator = BaselineCalibrator(
        calibration_frames=settings.ws_facial_calibration_frames,
        raised_ratio=settings.ws_facial_raised_ratio,
        furrowed_ratio=settings.ws_facial_furrowed_ratio,
    )

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

            # Calibrates/classifies regardless of ML readiness below -- an
            # honest FacialGrammarMarker.NONE when no face was detected at
            # all, never a guess from zero-filled landmarks.
            facial_marker = (
                facial_calibrator.update(normalized.face)
                if normalized.present["face"]
                else FacialGrammarMarker.NONE
            )

            feature_config = FeatureConfig(
                hands=settings.features_hands,
                pose=settings.features_pose,
                face=settings.features_face,
            )
            feature_vector = build_feature_vector(normalized, feature_config)

            inference_service = get_inference_service()
            if not inference_service.is_ready():
                # Real landmarks ARE extracted (Phase 6-7) -- but no trained
                # checkpoint is loaded (Phase 9-10 not run, or not found at
                # settings.model_checkpoint_path_resolved), so this stays an
                # honest error with real detection info, never a fabricated sign.
                await websocket.send_json(
                    ErrorMessage(
                        message=(
                            "Sign-recognition ML pipeline is not implemented yet "
                            "(Phase 9-10: no trained checkpoint found). Landmarks were "
                            f"extracted: left_hand={normalized.present['left_hand']}, "
                            f"right_hand={normalized.present['right_hand']}, "
                            f"pose={normalized.present['pose']}, "
                            f"face={normalized.present['face']} "
                            f"(feature vector size: {feature_vector.shape[0]}/"
                            f"{feature_vector_size(feature_config)})."
                        )
                    ).model_dump()
                )
                continue

            sequence_length = inference_service.sequence_length
            if feature_buffer is None:
                feature_buffer = deque(maxlen=sequence_length)
            feature_buffer.append(feature_vector.tolist())

            if len(feature_buffer) < sequence_length:
                await websocket.send_json(
                    ErrorMessage(
                        message=(
                            f"Buffering: {len(feature_buffer)}/{sequence_length} frames "
                            "collected before the first prediction."
                        )
                    ).model_dump()
                )
                continue

            try:
                # predict() runs a real (if small) forward pass -- keep it off
                # the event loop, same reasoning as extractor.extract above.
                prediction = await asyncio.to_thread(inference_service.predict, list(feature_buffer))
            except MLNotReadyError as exc:
                await websocket.send_json(ErrorMessage(message=str(exc)).model_dump())
                continue

            confirmed = gloss_aggregator.update(prediction.sign, prediction.confidence)
            display_text = prediction.text
            if confirmed:
                # Phase 12: translate the just-confirmed gloss into a real
                # Ukrainian sentence when the (intentionally small) rule-based
                # lexicon covers it; otherwise keep the raw gloss text rather
                # than guessing a composition -- see ml/nlp/gloss_to_text.py.
                # Phase 17: a concurrent eyebrow marker makes it a question --
                # written Ukrainian uses "?" for both yes/no and wh-questions,
                # so either marker flips the terminator the same way.
                try:
                    composed = translation_service.gloss_to_text(
                        [prediction.sign],
                        is_question=facial_marker != FacialGrammarMarker.NONE,
                    )
                    display_text = f"[DEMO] {composed}" if inference_service.is_demo_mode else composed
                except ValueError:
                    pass
            await websocket.send_json(
                PredictionMessage(
                    type="final_prediction" if confirmed else "prediction",
                    text=display_text,
                    gloss=prediction.sign,
                    confidence=prediction.confidence,
                    is_final=confirmed,
                    facial_grammar=facial_marker.value,
                ).model_dump()
            )
            if confirmed:
                logger.info(
                    "WebSocket id=%s confirmed gloss #%s (sequence so far: %s)",
                    conn_id,
                    len(gloss_aggregator.sequence),
                    gloss_aggregator.sequence,
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
