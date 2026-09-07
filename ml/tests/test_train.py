import torch

from ml.datasets.synthetic import generate_demo_dataset
from ml.training.train import main


def test_end_to_end_training_produces_a_loadable_checkpoint(tmp_path):
    # sequence_length matches configs/model.yaml's model.sequence_length (32)
    # so the dataset lines up exactly with no padding/truncation surprises.
    generate_demo_dataset(tmp_path, sequence_length=32, samples_per_signer_gloss=4, seed=1)
    annotations_path = tmp_path / "annotations" / "demo_annotations.jsonl"
    checkpoint_dir = tmp_path / "checkpoints"

    checkpoint_path = main(
        [
            "--annotations",
            str(annotations_path),
            "--dataset-root",
            str(tmp_path),
            "--config",
            "../configs/model.yaml",
            "--experiment-name",
            "test_run",
            "--output-dir",
            str(checkpoint_dir),
            "--epochs",
            "2",
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

    assert checkpoint_path == checkpoint_dir / "test_run" / "latest.pt"
    assert checkpoint_path.exists()

    checkpoint = torch.load(checkpoint_path, weights_only=False)
    assert checkpoint["model_type"] == "lstm"
    assert checkpoint["demo_mode"] is True
    assert checkpoint["source_tags"] == ["demo_synthetic"]
    assert 0.0 <= checkpoint["val_accuracy"] <= 1.0
    assert checkpoint["sequence_length"] == 32
    assert set(checkpoint["label_to_index"].values()) == set(range(len(checkpoint["label_to_index"])))
    assert "model_state_dict" in checkpoint


def test_raises_clearly_when_val_split_would_be_empty(tmp_path):
    generate_demo_dataset(tmp_path, sequence_length=8, samples_per_signer_gloss=1, seed=1)
    annotations_path = tmp_path / "annotations" / "demo_annotations.jsonl"

    try:
        main(
            [
                "--annotations",
                str(annotations_path),
                "--dataset-root",
                str(tmp_path),
                "--config",
                "../configs/model.yaml",
                "--output-dir",
                str(tmp_path / "checkpoints"),
                "--train-ratio",
                "1.0",
                "--val-ratio",
                "0.0",
                "--test-ratio",
                "0.0",
                "--epochs",
                "1",
                "--device",
                "cpu",
            ]
        )
    except ValueError as exc:
        assert "val split is empty" in str(exc)
    else:
        raise AssertionError("expected ValueError for empty val split")
