"""
dataset — loads a `SampleAnnotation`'s feature-vector sequence off disk.

Only the demo/synthetic path (source="demo_synthetic") is implemented: it
just reads the precomputed `.npy` written by `ml/datasets/synthetic.py`.
Loading *real* samples means decoding raw video through the existing
ml/preprocessing (video_reader/landmarks/normalization) + ml/features
pipeline -- there is no real dataset yet to wire that up against (Phase 8
found none publicly available, see PROJECT_STATUS.md), so this module
raises `NotImplementedError` for any other `source` rather than pretending
to support it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ml.datasets.annotation import SampleAnnotation
from ml.datasets.synthetic import DEMO_SOURCE_TAG


def load_feature_sequence(sample: SampleAnnotation, dataset_root: Path | str) -> np.ndarray:
    """Returns the `(sequence_length, feature_size)` array for `sample`."""
    if sample.source != DEMO_SOURCE_TAG:
        raise NotImplementedError(
            f"Loading real-video samples (source={sample.source!r}) is not implemented "
            f"yet -- Phase 9 will decode clip_path through ml/preprocessing + ml/features. "
            f"Only source={DEMO_SOURCE_TAG!r} (precomputed .npy) can be loaded today."
        )
    path = Path(dataset_root) / sample.clip_path
    return np.load(path)
