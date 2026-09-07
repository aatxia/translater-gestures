from app.services.inference_service import SignPrediction
from app.services.lstm_inference_service import LSTMSignRecognizer

from ml.datasets.synthetic import generate_demo_dataset
from ml.training.train import main as train_main


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
            "--batch-size",
            "8",
            "--hidden-size",
            "8",
            "--num-layers",
            "1",
            "--device",
            "cpu",
        ]
    )


def test_predicts_from_a_full_window_and_tags_demo_text(tmp_path):
    checkpoint_path = _train_tiny_checkpoint(tmp_path)
    recognizer = LSTMSignRecognizer(checkpoint_path, device="cpu")

    assert recognizer.is_ready() is True
    assert recognizer.is_demo_mode is True

    feature_size = 222  # hands(126) + pose(24) + face(72), configs/model.yaml default
    window = [[0.0] * feature_size for _ in range(recognizer.sequence_length)]
    prediction = recognizer.predict(window)

    assert isinstance(prediction, SignPrediction)
    assert prediction.text.startswith("[DEMO] ")
    assert prediction.text == f"[DEMO] {prediction.sign}"
    assert 0.0 <= prediction.confidence <= 1.0
    assert prediction.is_final is False
