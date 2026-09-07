"""
Phase 9-10: the WebSocket handler's buffering + real (if demo-only) inference
path, isolated from Phase 6-7's CV pipeline (which has its own coverage in
ml/tests/test_landmarks.py and backend/tests/test_websocket.py) by stubbing
the landmark extractor. The real MediaPipe detector needs system libraries
(libEGL) not guaranteed to be present in every CI/sandbox -- stubbing it
here keeps this test about the NEW logic (sliding window -> checkpoint ->
PredictionMessage), not a redundant re-test of landmark detection.
"""
import base64

import cv2
import numpy as np
import websocket.handler as ws_handler
from app.main import app
from fastapi.testclient import TestClient

from ml.datasets.synthetic import generate_demo_dataset
from ml.preprocessing.landmarks import FrameLandmarks
from ml.training.train import main as train_main

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


class _StubLandmarkExtractor:
    """An honest 'nothing detected in this frame' result (all fields None),
    same as the real extractor on a blank frame -- just without needing the
    real MediaPipe/EGL runtime for this test."""

    def extract(self, frame_bgr):
        return FrameLandmarks()


def test_sends_buffering_status_then_a_real_prediction_once_window_fills(
    tmp_path, monkeypatch, reset_inference_caches
):
    checkpoint_path = _train_tiny_checkpoint(tmp_path)
    monkeypatch.setenv("MODEL_CHECKPOINT_PATH", str(checkpoint_path))
    monkeypatch.setenv("WS_MAX_FPS", "100000")  # avoid rate-limiting a tight send loop
    monkeypatch.setattr(ws_handler, "_get_landmark_extractor", lambda: _StubLandmarkExtractor())

    frame_data = _blank_frame_data_url()

    with client.websocket_connect("/ws") as ws:
        ws.receive_json()  # connection ack

        for i in range(SEQUENCE_LENGTH - 1):
            ws.send_json({"type": "frame", "timestamp": i, "data": frame_data})
            response = ws.receive_json()
            assert response["type"] == "error"
            assert f"Buffering: {i + 1}/{SEQUENCE_LENGTH}" in response["message"]

        ws.send_json({"type": "frame", "timestamp": SEQUENCE_LENGTH, "data": frame_data})
        response = ws.receive_json()

        assert response["type"] == "prediction"
        assert response["text"].startswith("[DEMO] ")
        assert response["is_final"] is False
        assert 0.0 <= response["confidence"] <= 1.0


def test_keeps_predicting_on_the_sliding_window_after_the_first_prediction(
    tmp_path, monkeypatch, reset_inference_caches
):
    checkpoint_path = _train_tiny_checkpoint(tmp_path)
    monkeypatch.setenv("MODEL_CHECKPOINT_PATH", str(checkpoint_path))
    monkeypatch.setenv("WS_MAX_FPS", "100000")
    monkeypatch.setattr(ws_handler, "_get_landmark_extractor", lambda: _StubLandmarkExtractor())

    frame_data = _blank_frame_data_url()

    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        for i in range(SEQUENCE_LENGTH + 2):
            ws.send_json({"type": "frame", "timestamp": i, "data": frame_data})
            response = ws.receive_json()
            if i >= SEQUENCE_LENGTH - 1:
                assert response["type"] == "prediction"
