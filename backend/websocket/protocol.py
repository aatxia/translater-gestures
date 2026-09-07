"""
WebSocket protocol schema (see docs/architecture.md section 4).

Client -> Server:
    {"type": "frame", "timestamp": 123456789, "data": "<base64 jpeg>"}

Server -> Client:
    {"type": "connection", "status": "ok" | "closed"}
    {"type": "prediction", "text": "...", "confidence": 0.92, "is_final": false}
    {"type": "final_prediction", "text": "...", "confidence": 0.95, "is_final": true}
    {"type": "error", "message": "..."}
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
    confidence: float
    is_final: bool = False


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    message: str


class ConnectionMessage(BaseModel):
    type: Literal["connection"] = "connection"
    status: Literal["ok", "closed"] = "ok"


ServerMessage = PredictionMessage | ErrorMessage | ConnectionMessage


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
