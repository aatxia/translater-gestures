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

## Dataset / training / inference

Not implemented yet — see `PROJECT_STATUS.md` for the phase plan
(Phase 8: dataset pipeline, Phase 9: baseline model training,
Phase 10: real-time inference).
