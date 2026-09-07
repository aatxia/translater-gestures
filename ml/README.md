# ML Pipeline — UKSL Translator

## Setup

```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## MediaPipe models (external dependency)

Hand/pose/face landmark detection uses Google's pretrained MediaPipe Tasks
model bundles (Apache 2.0) — this project doesn't train these itself. Download
them once:

```bash
../scripts/download_mediapipe_models.sh
```

This fetches `hand_landmarker.task`, `pose_landmarker.task`, and
`face_landmarker.task` into `models/mediapipe/` (gitignored — ~13 MB total,
binary, doesn't belong in git). If `storage.googleapis.com` is blocked in
your network, hand/face automatically fall back to a GitHub mirror; pose
currently has no known mirror (get it manually — see the script's header
comment for the link).

## Preprocessing pipeline (Phase 6)

```
ml/preprocessing/
├── video_reader.py     # base64 JPEG (from WebSocket) or video file -> BGR numpy frames
├── landmarks.py         # MediaPipe Tasks: hands/pose/face detection (LandmarkExtractor)
├── normalization.py    # position/scale-invariant landmark normalization
└── augmentation.py     # training-time sequence augmentation (rotate/scale/noise/dropout)
```

Quick example:

```python
from ml.preprocessing.landmarks import LandmarkExtractor, FeatureToggles
from ml.preprocessing.normalization import normalize_frame
from ml.preprocessing.video_reader import decode_base64_frame

frame = decode_base64_frame(base64_jpeg_string)

with LandmarkExtractor("models/mediapipe", FeatureToggles(hands=True, pose=True, face=False)) as ex:
    raw = ex.extract(frame)
    normalized = normalize_frame(raw)  # fixed-shape, zero-filled when a modality is absent
```

`normalize_frame` never fabricates a detection: if MediaPipe doesn't find a
hand/pose/face in a frame, the corresponding array is zero-filled AND
`normalized.present[...]` is `False`, so downstream code (Phase 7 feature
builder, Phase 9 model) can tell "detected at the origin" apart from "not
detected".

## Feature vectors (Phase 7)

```
ml/features/
├── hands.py            # left+right hand -> (126,) vector
├── pose.py              # 8 selected upper-body landmarks -> (24,) vector
├── face.py              # 24 selected landmarks (brows/eyes/mouth) -> (72,) vector
└── feature_vector.py    # combines enabled modalities per FeatureConfig (section 9 experiments)
```

```python
from ml.features.feature_vector import FeatureConfig, build_feature_vector

config = FeatureConfig(hands=True, pose=True, face=False)  # hands+pose experiment
vector = build_feature_vector(normalized, config)  # shape driven entirely by config
```

This is exactly what `backend/websocket/handler.py` calls today for every incoming
frame — the WebSocket already reports real detection status and feature vector
size, it just has no trained model yet to turn that vector into a prediction.

## Running tests

```bash
cd ml
pytest -v
```

Tests that need a real model file (`test_landmarks.py`) skip automatically
with a clear reason if you haven't run the download script yet — they are
not faked or hardcoded to pass.

## Dataset pipeline (Phase 8)

```
ml/datasets/
├── annotation.py        # SampleAnnotation schema + honest JSONL load/write
├── split.py              # signer-independent train/val/test split (section 11)
├── synthetic.py          # DEMO MODE ONLY: synthetic dataset generator
└── dataset.py             # loads a sample's feature-vector sequence off disk
```

No public isolated-sign УЖМ (Ukrainian Sign Language) dataset with
`signer_id` labeling could be found (see `PROJECT_STATUS.md`, Phase 8, for
what was checked). Until a real one is available, `scripts/generate_demo_dataset.py`
produces a small synthetic dataset (`source="demo_synthetic"`, never to be
mistaken for real data) so the rest of the pipeline can be exercised
end-to-end:

```bash
python scripts/generate_demo_dataset.py --output-dir data --seed 42
python scripts/create_dataset_split.py \
  --annotations data/annotations/demo_annotations.jsonl \
  --output-dir data/splits
```

Full format details: `docs/dataset_format.md`.

## Training (Phase 9)

```
ml/models/
└── lstm.py              # LSTMSignClassifier: stacked LSTM + linear classifier head

ml/training/
├── config.py             # loads configs/model.yaml -> TrainingConfig
├── dataset.py             # SignSequenceDataset: SampleAnnotation -> fixed-length tensor
└── train.py               # CLI: split -> train -> evaluate -> save checkpoint
```

Install torch first (see `ml/requirements-training.txt` — **read its header
before running pip install in Google Colab**, since Colab already has a
GPU-matched torch preinstalled). Then, from the repo root:

```bash
pip install -r ml/requirements-training.txt   # local only, see note above for Colab
python scripts/generate_demo_dataset.py --output-dir data --seed 42   # if you haven't already
python -m ml.training.train --annotations data/annotations/demo_annotations.jsonl
```

Runs identically locally and in Colab (`!python -m ml.training.train ...`
after cloning the repo there) — no Colab-specific paths or hacks. Hyperparameters
(hidden size, epochs, batch size, learning rate) default to `configs/model.yaml`'s
`training:` section and can be overridden per-run with CLI flags (`--epochs`,
`--hidden-size`, ...) without editing the file.

Training does a signer-independent split (`ml/datasets/split.py`, section 11)
of whatever annotation file you point it at, trains on `train`, evaluates on
`val` each epoch, and saves the best checkpoint to
`models/checkpoints/<experiment-name>/latest.pt` (gitignored — a checkpoint is
a build artifact, not source). The checkpoint carries everything Phase 10
inference needs: model weights, architecture config, feature config, sequence
length, and the gloss↔index label mapping — plus `source_tags` and `demo_mode`,
so a checkpoint trained only on `demo_synthetic` data can never be silently
mistaken for one that recognizes real Ukrainian Sign Language.

**Running on the demo dataset is a pipeline sanity check, not a real model**:
since the synthetic classes are trivially separable by construction, val
accuracy reaches 100% in a few epochs — that only proves training/checkpoint
plumbing works end-to-end, it says nothing about real-world recognition.
Real training needs a real annotated УЖМ dataset (still not available as of
Phase 9, see `PROJECT_STATUS.md`).

## Inference

Not implemented yet — see `PROJECT_STATUS.md` for the phase plan
(Phase 10: real-time inference, wiring a trained checkpoint into the backend's
`InferenceService`).
