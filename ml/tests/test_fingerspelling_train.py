import numpy as np

from ml.fingerspelling.model import INPUT_SIZE
from ml.fingerspelling.train import main as train_main


def _write_fake_features(path, rng, per_class=40, num_classes=4):
    """Two well-separated clusters per class (in different feature
    dimensions) so a small MLP can actually learn a real class boundary --
    this is checking the training loop plumbing, not real-world accuracy,
    same spirit as ml/tests/test_train.py's tiny checkpoint run."""
    classes = [chr(ord("А") + i) for i in range(num_classes)]
    features = []
    labels = []
    for i, label in enumerate(classes):
        base = np.zeros(INPUT_SIZE, dtype=np.float32)
        base[i] = 5.0
        samples = base + rng.normal(scale=0.1, size=(per_class, INPUT_SIZE)).astype(np.float32)
        features.append(samples)
        labels.extend([label] * per_class)
    np.savez_compressed(path, features=np.concatenate(features), labels=np.array(labels, dtype="<U8"))


def test_train_main_produces_a_checkpoint_and_report_with_reasonable_accuracy(tmp_path):
    rng = np.random.default_rng(0)
    features_path = tmp_path / "features.npz"
    _write_fake_features(features_path, rng)

    output_path = tmp_path / "checkpoints" / "latest.pt"
    train_main(
        [
            "--features",
            str(features_path),
            "--output",
            str(output_path),
            "--epochs",
            "50",
        ]
    )

    assert output_path.exists()
    report_path = output_path.with_suffix(".report.json")
    assert report_path.exists()

    import json

    report = json.loads(report_path.read_text(encoding="utf-8"))
    # Trivially separable clusters -- the trained model should do well,
    # confirming the train/eval loop itself is correct (real accuracy on
    # the actual USL_alphabet_train data is reported separately and is NOT
    # expected to look like this -- see PROJECT_STATUS.md).
    assert report["test_accuracy"] > 0.8
