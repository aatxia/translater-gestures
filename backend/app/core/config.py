"""
Centralized application configuration.

All tunable parameters are read from environment variables (see /.env.example
at the repo root). Nothing here is hardcoded — this is the single source of
truth the rest of the backend imports from.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root is three levels up from this file: backend/app/core/config.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[3]

# Make the sibling `ml/` package importable from anywhere in the backend
# (e.g. `from ml.preprocessing.landmarks import ...` in websocket/handler.py),
# regardless of the working directory uvicorn/pytest was launched from.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"

    # --- Backend ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # --- WebSocket ---
    ws_max_message_size_bytes: int = 2_097_152
    ws_max_fps: int = 15
    ws_heartbeat_interval_sec: int = 30

    # --- MediaPipe (Phase 6-7 CV pipeline) ---
    mediapipe_models_dir: Path = REPO_ROOT / "models" / "mediapipe"

    # --- ML model ---
    model_type: str = "lstm"
    model_checkpoint_path: str = "models/checkpoints/baseline/latest.pt"
    model_sequence_length: int = 32
    model_device: str = "cpu"

    # --- Feature toggles ---
    features_hands: bool = True
    features_pose: bool = True
    features_face: bool = True

    # --- NLP ---
    nlp_backend: str = "rule_based"
    nlp_hf_model_name: str = ""

    # --- TTS / STT ---
    tts_provider: str = "browser"
    stt_provider: str = "browser"

    # --- Privacy ---
    store_raw_video: bool = False
    send_video_to_third_party: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def model_checkpoint_path_resolved(self) -> Path:
        """model_checkpoint_path is documented (.env.example) as relative to
        the repo root, not the process's cwd -- uvicorn is commonly launched
        from backend/, where a bare relative path would silently resolve to
        the wrong (nonexistent) location. Mirrors mediapipe_models_dir."""
        path = Path(self.model_checkpoint_path)
        return path if path.is_absolute() else REPO_ROOT / path


@lru_cache
def get_settings() -> Settings:
    """Settings are cached; call get_settings() rather than instantiating Settings() directly."""
    return Settings()
