"""
fingerspelling.dataset -- turns the real USL_alphabet_train photos into
normalized hand-landmark feature vectors for a single-frame classifier.

Unlike ml/datasets/synthetic.py's sequences of frames (fed to the LSTM
isolated-word recognizer), one dactyl letter is one still photo of a
handshape -- there is no temporal dimension here, so this reuses
ml/preprocessing/normalization.py's normalize_hand() directly on the single
detected hand, not the full multimodal per-frame pipeline built for video.

USL_alphabet_train/ has two kinds of subdirectories that must never be
treated as real classes:
  - `_excluded_non_ukrainian/` -- letters (Ъ, Ы, Э) that aren't part of the
    Ukrainian alphabet; confirmed with the person who uploaded this data
    that they don't belong here.
  - `_excluded_unclear/` -- an ambiguously-named folder ("TR", mixed
    Latin/Cyrillic) and a single-file folder from a corrupted directory
    name; neither has a confirmed real label.
Both are skipped by construction (any directory name starting with "_"),
never silently folded into a real letter's samples.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from ml.preprocessing.landmarks import LandmarkExtractor
from ml.preprocessing.normalization import normalize_hand

_EXCLUDED_PREFIX = "_"


@dataclass(frozen=True)
class ImageSample:
    image_path: Path
    label: str


def scan_image_dataset(root: Path | str) -> list[ImageSample]:
    """One sample per image file directly inside a per-letter subdirectory
    of `root`. Subdirectories starting with "_" are skipped -- see module
    docstring."""
    root = Path(root)
    samples: list[ImageSample] = []
    for class_dir in sorted(root.iterdir()):
        if not class_dir.is_dir() or class_dir.name.startswith(_EXCLUDED_PREFIX):
            continue
        label = class_dir.name
        for image_path in sorted(class_dir.iterdir()):
            if image_path.is_file():
                samples.append(ImageSample(image_path=image_path, label=label))
    return samples


@dataclass
class ExtractionResult:
    features: np.ndarray  # (N, 63) float32
    labels: list[str]
    # (path, reason) for every photo that couldn't honestly be turned into a
    # sample -- never silently dropped without a record.
    skipped: list[tuple[Path, str]] = field(default_factory=list)
    # How many kept samples came from a detected left vs right hand, before
    # left-hand mirroring -- see extract_features' docstring.
    left_hand_count: int = 0
    right_hand_count: int = 0


def extract_features(samples: list[ImageSample], extractor: LandmarkExtractor) -> ExtractionResult:
    """Runs the real MediaPipe hand detector on every sample image and
    normalizes the single detected hand (wrist-centered, MCP-scaled -- same
    convention as the video pipeline's per-frame hands, ml/preprocessing/
    normalization.py's normalize_hand()).

    A photo with no detected hand, or with BOTH hands detected (these are
    meant to be single-handshape photos; two hands means something in the
    frame is ambiguous), is skipped and recorded -- never silently
    zero-filled or guessed, unlike the video pipeline where a missing hand
    is a legitimate "not signing right now" frame.

    A left-hand detection has its x-coordinate mirrored before
    normalization, so a left-hand and a right-hand photo of the same
    handshape land in the same feature space (handshape identity doesn't
    depend on which physical hand performs it, just its mirror image) --
    a deliberate, documented design choice, not something MediaPipe or the
    dataset does on its own.
    """
    features: list[np.ndarray] = []
    labels: list[str] = []
    skipped: list[tuple[Path, str]] = []
    left_count = 0
    right_count = 0

    for sample in samples:
        image_bgr = cv2.imread(str(sample.image_path))
        if image_bgr is None:
            skipped.append((sample.image_path, "unreadable image file"))
            continue

        result = extractor.extract(image_bgr)
        has_left = result.left_hand is not None
        has_right = result.right_hand is not None

        if has_left and has_right:
            skipped.append(
                (sample.image_path, "both hands detected, ambiguous for a single-handshape photo")
            )
            continue
        if not has_left and not has_right:
            skipped.append((sample.image_path, "no hand detected"))
            continue

        if has_left:
            hand = result.left_hand.copy()
            hand[:, 0] *= -1.0  # mirror x so left- and right-hand photos share one feature space
            left_count += 1
        else:
            hand = result.right_hand
            right_count += 1

        normalized = normalize_hand(hand)
        features.append(normalized.flatten().astype(np.float32))
        labels.append(sample.label)

    return ExtractionResult(
        features=np.stack(features) if features else np.zeros((0, 63), dtype=np.float32),
        labels=labels,
        skipped=skipped,
        left_hand_count=left_count,
        right_hand_count=right_count,
    )
