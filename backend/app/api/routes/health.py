from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import HealthResponse
from app.services.inference_service import NotConfiguredInferenceService

router = APIRouter(tags=["health"])

# Phase 2: no real model loaded yet -> honest "not_implemented" status.
_inference_service = NotConfiguredInferenceService()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app_env=settings.app_env,
        model_type=settings.model_type,
        features={
            "hands": settings.features_hands,
            "pose": settings.features_pose,
            "face": settings.features_face,
        },
        ml_pipeline_status="ready" if _inference_service.is_ready() else "not_implemented",
    )
