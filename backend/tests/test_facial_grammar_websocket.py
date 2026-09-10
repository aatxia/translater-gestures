"""
Phase 17: verifies the WebSocket handler actually wires
ml/features/facial_grammar.py in -- every PredictionMessage carries a real
"facial_grammar" field, and a concurrently-detected eyebrow marker flips a
just-confirmed gloss's composed text into a question. The classifier's own
threshold/ratio logic is covered in ml/tests/test_facial_grammar.py; this
is wiring, not re-testing that math.
"""
import base64

import cv2
import numpy as np
from fastapi.testclient import TestClient
from ml.datasets.synthetic import generate_demo_dataset
from ml.features.facial_grammar import (
    LEFT_EYE_TOP,
    LEFT_EYEBROW_CENTER,
    RIGHT_EYE_TOP,
    RIGHT_EYEBROW_CENTER,
)
from ml.preprocessing.landmarks import FrameLandmarks
from ml.training.train import main as train_main

import websocket.handler as ws_handler
from app.main import app

client = TestClient(app)

SEQUENCE_LENGTH = 32  # configs/model.yaml model.sequence_length


def _train_tiny_checkpoint(tmp_path):
    generate_demo_dataset(tmp_path, sequence_length=8, samples_per_signer_gloss=4, seed=1)
    return train_main(
        [
            "--annotations",
            str(tmp_path / "annotations" / "demo_annotations.jsonl"),
            "--dataset-root",
            str(tmp_path),
            "--config",
            "../configs/model.yaml",
            "--experiment-name",
            "test_run",
            "--output-dir",
            str(tmp_path / "checkpoints"),
            "--epochs",
            "1",
            "--hidden-size",
            "8",
            "--num-layers",
            "1",
            "--device",
            "cpu",
        ]
    )


def _blank_frame_data_url(width: int = 64, height: int = 48) -> str:
    image = np.full((height, width, 3), 120, dtype=np.uint8)
    ok, buffer = cv2.imencode(".jpg", image)
    assert ok
    b64 = base64.b64encode(buffer.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _neutral_face() -> np.ndarray:
    """Every one of the 478 landmarks at the exact same point -- after
    normalize_face() this collapses to all zeros, giving a baseline
    eyebrow-eye gap of exactly 0.0 (see BaselineCalibrator's _EPS fallback:
    any nonzero gap afterward registers as an arbitrarily large deviation,
    so this makes the "raised" case below deterministic regardless of the
    exact post-normalization scale)."""
    return np.full((478, 3), 0.5, dtype=np.float32)


def _raised_eyebrows_face() -> np.ndarray:
    face = np.full((478, 3), 0.5, dtype=np.float32)
    face[LEFT_EYEBROW_CENTER, 1] = 0.3
    face[RIGHT_EYEBROW_CENTER, 1] = 0.3
    face[LEFT_EYE_TOP, 1] = 0.6
    face[RIGHT_EYE_TOP, 1] = 0.6
    return face


class _FacialLandmarkExtractor:
    """Real face landmarks (see above), hands/pose absent -- same "no
    real MediaPipe needed" stubbing rationale as test_websocket_inference.py,
    just with a face array plugged in and a per-call frame counter so the
    first few calibration frames are neutral and the rest are raised."""

    def __init__(self, calibration_frames: int):
        self._calibration_frames = calibration_frames
        self._calls = 0

    def extract(self, frame_bgr):
        self._calls += 1
        face = _neutral_face() if self._calls <= self._calibration_frames else _raised_eyebrows_face()
        return FrameLandmarks(face=face)


class _NoFaceExtractor:
    def extract(self, frame_bgr):
        return FrameLandmarks()


def test_facial_grammar_field_is_none_with_no_face_detected(tmp_path, monkeypatch, reset_inference_caches):
    checkpoint_path = _train_tiny_checkpoint(tmp_path)
    monkeypatch.setenv("MODEL_CHECKPOINT_PATH", str(checkpoint_path))
    monkeypatch.setenv("WS_MAX_FPS", "100000")
    monkeypatch.setattr(ws_handler, "_get_landmark_extractor", lambda: _NoFaceExtractor())

    frame_data = _blank_frame_data_url()
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        for i in range(SEQUENCE_LENGTH):
            ws.send_json({"type": "frame", "timestamp": i, "data": frame_data})
            response = ws.receive_json()

    assert response["type"] == "prediction"
    assert response["facial_grammar"] == "NONE"


def test_confirmed_gloss_becomes_a_question_when_eyebrows_are_raised(
    tmp_path, monkeypatch, reset_inference_caches
):
    checkpoint_path = _train_tiny_checkpoint(tmp_path)
    monkeypatch.setenv("MODEL_CHECKPOINT_PATH", str(checkpoint_path))
    monkeypatch.setenv("WS_MAX_FPS", "100000")
    monkeypatch.setenv("WS_GLOSS_STABILITY_FRAMES", "3")
    monkeypatch.setenv("WS_GLOSS_CONFIDENCE_THRESHOLD", "0.0")
    monkeypatch.setenv("WS_FACIAL_CALIBRATION_FRAMES", "3")
    # _get_landmark_extractor() is called once per frame in the real handler
    # (memoized via module globals); the stub must be memoized the same way
    # here -- a fresh instance per call would reset its internal frame
    # counter every time and never progress past "calibrating".
    extractor_stub = _FacialLandmarkExtractor(3)
    monkeypatch.setattr(ws_handler, "_get_landmark_extractor", lambda: extractor_stub)

    frame_data = _blank_frame_data_url()
    final_predictions = []

    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        for i in range(SEQUENCE_LENGTH + 10):
            ws.send_json({"type": "frame", "timestamp": i, "data": frame_data})
            response = ws.receive_json()
            if response["type"] == "final_prediction":
                final_predictions.append(response)

    assert len(final_predictions) == 1
    result = final_predictions[0]
    assert result["facial_grammar"] == "EYEBROWS_RAISED"
    # Phase 12's composed sentence ends "?" instead of "." -- a concurrent
    # eyebrow marker, not a manual gloss, is what makes this a question.
    assert result["text"].rstrip().endswith("?")
