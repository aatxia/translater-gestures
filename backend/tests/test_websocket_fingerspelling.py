"""
Live integration of the real fingerspelling classifier (ml/fingerspelling/)
into the WebSocket handler -- separate from test_websocket_inference.py's
word-level (still synthetic-only) LSTM coverage. Uses a real trained tiny
checkpoint (two classes, well-separated) and a stub landmark extractor, same
spirit as test_websocket_inference.py's _RightHandOnlyExtractor.
"""
import base64

import cv2
import numpy as np
import websocket.handler as ws_handler
from app.main import app
from fastapi.testclient import TestClient

from ml.fingerspelling.dataset import hand_to_feature_vector
from ml.fingerspelling.train import main as train_main
from ml.preprocessing.landmarks import FrameLandmarks

client = TestClient(app)

# A real (if arbitrary) 21-point hand shape -- fed through the same
# hand_to_feature_vector() the live handler uses, so the tiny checkpoint
# below is trained on the exact feature space a real detection would land in.
_HAND_A = np.array([[i * 0.01, i * 0.02, 0.0] for i in range(21)], dtype=np.float32)
_HAND_B = np.array([[i * 0.02, i * 0.01, 0.0] for i in range(21)], dtype=np.float32)


def _blank_frame_data_url(width: int = 64, height: int = 48) -> str:
    image = np.full((height, width, 3), 120, dtype=np.uint8)
    ok, buffer = cv2.imencode(".jpg", image)
    assert ok
    b64 = base64.b64encode(buffer.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _train_tiny_checkpoint(tmp_path):
    vector_a, reason_a = hand_to_feature_vector(None, _HAND_A)
    vector_b, reason_b = hand_to_feature_vector(None, _HAND_B)
    assert reason_a is None and reason_b is None

    rng = np.random.default_rng(0)
    features = np.concatenate(
        [
            vector_a + rng.normal(scale=0.01, size=(30, 63)).astype(np.float32),
            vector_b + rng.normal(scale=0.01, size=(30, 63)).astype(np.float32),
        ]
    )
    labels = np.array(["А"] * 30 + ["Б"] * 30, dtype="<U8")

    features_path = tmp_path / "features.npz"
    np.savez_compressed(features_path, features=features, labels=labels)

    checkpoint_path = tmp_path / "checkpoints" / "latest.pt"
    train_main(["--features", str(features_path), "--output", str(checkpoint_path), "--epochs", "40"])
    return checkpoint_path


class _RightHandOnlyExtractor:
    """Reports a fixed single-hand detection every frame -- no pose/face,
    matching test_websocket_inference.py's stub extractor convention."""

    def __init__(self, hand: np.ndarray):
        self._hand = hand

    def extract(self, frame_bgr):
        return FrameLandmarks(right_hand=self._hand)


class _BothHandsExtractor:
    def extract(self, frame_bgr):
        return FrameLandmarks(left_hand=_HAND_A, right_hand=_HAND_B)


def test_no_letter_message_when_no_fingerspelling_checkpoint_is_loaded(
    monkeypatch, reset_inference_caches, reset_fingerspelling_caches
):
    """The fingerspelling path is additive/optional -- a missing checkpoint
    must never surface as an error, unlike the word-level ML-not-ready path."""
    monkeypatch.setenv("WS_MAX_FPS", "100000")
    monkeypatch.setenv("FINGERSPELLING_CHECKPOINT_PATH", "does/not/exist.pt")
    monkeypatch.setattr(ws_handler, "_get_landmark_extractor", lambda: _RightHandOnlyExtractor(_HAND_A))

    with client.websocket_connect("/ws") as ws:
        ws.receive_json()  # connection ack
        ws.send_json({"type": "frame", "timestamp": 1, "data": _blank_frame_data_url()})
        status = ws.receive_json()
        assert status["type"] == "landmarks_status"
        # Next message is the word-level ML-not-ready error, not a letter message.
        response = ws.receive_json()
        assert response["type"] == "error"


def test_confirms_a_real_letter_once_held_stably(
    tmp_path, monkeypatch, reset_inference_caches, reset_fingerspelling_caches
):
    checkpoint_path = _train_tiny_checkpoint(tmp_path)
    monkeypatch.setenv("WS_MAX_FPS", "100000")
    monkeypatch.setenv("FINGERSPELLING_CHECKPOINT_PATH", str(checkpoint_path))
    monkeypatch.setenv("FINGERSPELLING_STABILITY_FRAMES", "3")
    monkeypatch.setenv("FINGERSPELLING_CONFIDENCE_THRESHOLD", "0.5")
    monkeypatch.setattr(ws_handler, "_get_landmark_extractor", lambda: _RightHandOnlyExtractor(_HAND_A))

    frame_data = _blank_frame_data_url()
    letter_messages = []

    with client.websocket_connect("/ws") as ws:
        ws.receive_json()  # connection ack
        for i in range(5):
            ws.send_json({"type": "frame", "timestamp": i, "data": frame_data})
            ws.receive_json()  # landmarks_status
            letter_msg = ws.receive_json()
            assert letter_msg["type"] in {"letter_prediction", "letter_confirmed"}
            letter_messages.append(letter_msg)
            ws.receive_json()  # word-level ML-not-ready error (unrelated path)

    assert any(m["type"] == "letter_confirmed" for m in letter_messages)
    confirmed = next(m for m in letter_messages if m["type"] == "letter_confirmed")
    assert confirmed["letter"] == "А"
    assert confirmed["is_final"] is True
    assert 0.0 <= confirmed["confidence"] <= 1.0


def test_no_letter_message_when_both_hands_detected(
    tmp_path, monkeypatch, reset_inference_caches, reset_fingerspelling_caches
):
    """Ambiguous for a single-handshape classifier -- silently skipped, same
    honesty convention as the offline dataset builder's skip logic."""
    checkpoint_path = _train_tiny_checkpoint(tmp_path)
    monkeypatch.setenv("WS_MAX_FPS", "100000")
    monkeypatch.setenv("FINGERSPELLING_CHECKPOINT_PATH", str(checkpoint_path))
    monkeypatch.setattr(ws_handler, "_get_landmark_extractor", lambda: _BothHandsExtractor())

    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_json({"type": "frame", "timestamp": 1, "data": _blank_frame_data_url()})
        status = ws.receive_json()
        assert status["type"] == "landmarks_status"
        response = ws.receive_json()
        assert response["type"] == "error"  # word-level path, not a letter message
