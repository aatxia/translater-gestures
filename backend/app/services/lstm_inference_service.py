"""
LSTMSignRecognizer — InferenceService adapter around ml/inference/recognizer.py
(Phase 9's trained checkpoint). Translates between the WebSocket handler's
buffered feature vectors and the app-level SignPrediction/MLNotReadyError
contract; the actual checkpoint loading and forward pass live in ml/inference/
(framework-agnostic, reused as-is here).
"""
from __future__ import annotations

from pathlib import Path

from app.services.inference_service import InferenceService, SignPrediction
from ml.inference.recognizer import CheckpointNotFoundError, SignRecognizer

__all__ = ["CheckpointNotFoundError", "LSTMSignRecognizer"]


class LSTMSignRecognizer(InferenceService):
    def __init__(self, checkpoint_path: Path | str, device: str = "cpu") -> None:
        self._recognizer = SignRecognizer(checkpoint_path, device=device)
        self.sequence_length: int = self._recognizer.sequence_length
        self.is_demo_mode: bool = self._recognizer.is_demo_mode

    def is_ready(self) -> bool:
        return True

    def predict(self, landmark_sequence: list[list[float]]) -> SignPrediction:
        result = self._recognizer.predict(landmark_sequence)
        # demo_mode checkpoints are trained on synthetic placeholder glosses
        # (see ml/datasets/synthetic.py) -- tagging the text makes it
        # impossible to mistake this output for real УЖМ recognition.
        text = f"[DEMO] {result.gloss}" if result.is_demo_mode else result.gloss
        return SignPrediction(sign=result.gloss, text=text, confidence=result.confidence, is_final=False)
