"""
WebSocket protocol schema (see docs/architecture.md section 4).

Client -> Server:
    {"type": "frame", "timestamp": 123456789, "data": "<base64 jpeg>"}

Server -> Client:
    {"type": "connection", "status": "ok" | "closed"}
    {"type": "landmarks_status", "left_hand": true, "right_hand": false,
     "pose": true, "face": true}
    {"type": "prediction", "text": "...", "gloss": "TAK", "confidence": 0.92,
     "is_final": false, "facial_grammar": "NONE"}
    {"type": "final_prediction", "text": "...", "gloss": "TAK", "confidence": 0.95,
     "is_final": true, "facial_grammar": "EYEBROWS_RAISED"}
    {"type": "error", "message": "..."}

"landmarks_status" (real detection, not a guess -- ml/preprocessing/
normalization.py's `present` dict) is sent for every frame that reaches
real landmark extraction, one per frame, *before* whichever of
prediction/final_prediction/error follows -- independent of gloss
inference readiness, so the frontend can show a live "is my hand visible"
indicator (opt-in toggle) from frame 1, not just once a checkpoint exists.

"gloss" (Phase 15) is the raw predicted sign label for this frame -- the
same value "text" is derived from via Phase 12's gloss->text composition
(or, if the lexicon doesn't cover it, "text" *is* the raw gloss). It's what
drives the 3D avatar (frontend/components/Avatar/): the frontend only
plays a gloss once its final_prediction confirms it, never an interim guess.

"facial_grammar" (Phase 17) is this frame's non-manual grammar marker --
"NONE", "EYEBROWS_RAISED" (yes/no question), or "EYEBROWS_FURROWED"
(wh-question) -- from ml/features/facial_grammar.py's per-connection
baseline calibrator. "NONE" also covers "no face detected" and "still
calibrating"; the client can't tell those apart from this field alone, but
none of them should be treated as a detected marker either way.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ValidationError


class FrameMessage(BaseModel):
    type: Literal["frame"]
    timestamp: int
    data: str  # base64-encoded JPEG, produced by frontend useCamera capture loop


class PredictionMessage(BaseModel):
    type: Literal["prediction", "final_prediction"] = "prediction"
    text: str
    gloss: str
    confidence: float
    is_final: bool = False
    facial_grammar: str = "NONE"


class LandmarksStatusMessage(BaseModel):
    type: Literal["landmarks_status"] = "landmarks_status"
    left_hand: bool
    right_hand: bool
    pose: bool
    face: bool
    # Raw (x, y) image-normalized coordinates (MediaPipe's own [0, 1] frame
    # space, before ml/preprocessing/normalization.py's centering/scaling --
    # that version is for the model, this one is for drawing on the actual
    # video frame), so the frontend can overlay real detected points on the
    # camera feed, the way MediaPipe's own demos do -- not just a boolean
    # "hand visible" dot. None (not an empty list) when that modality
    # wasn't detected this frame, same honesty convention as the booleans
    # above. Face is intentionally omitted -- 478 points per frame for a
    # feature nobody asked to see face landmarks for.
    left_hand_points: list[tuple[float, float]] | None = None
    right_hand_points: list[tuple[float, float]] | None = None
    pose_points: list[tuple[float, float]] | None = None


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    message: str


class ConnectionMessage(BaseModel):
    type: Literal["connection"] = "connection"
    status: Literal["ok", "closed"] = "ok"


ServerMessage = PredictionMessage | LandmarksStatusMessage | ErrorMessage | ConnectionMessage


class ProtocolError(ValueError):
    """Raised when an incoming client message doesn't match the known schema."""


def parse_client_message(raw: dict[str, Any]) -> FrameMessage:
    """Validate a raw (already JSON-decoded) client message.

    Only 'frame' is a valid client->server message type in Phase 5. Anything
    else -- unknown type, missing fields, wrong types -- raises ProtocolError
    with a message safe to send back to the client.
    """
    msg_type = raw.get("type")

    if msg_type == "frame":
        try:
            return FrameMessage.model_validate(raw)
        except ValidationError as exc:
            raise ProtocolError(f"Invalid 'frame' message: {exc.errors()[0]['msg']}") from exc

    raise ProtocolError(f"Unknown or unsupported message type: {msg_type!r}")
