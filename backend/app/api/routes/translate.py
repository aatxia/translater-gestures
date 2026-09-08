"""
POST /translate/text-to-gloss — Phase 14: Ukrainian text -> gloss sequence,
via RuleBasedTranslationService (ml/nlp/text_to_gloss.py). A real (if
narrow-coverage) rule-based parse, not a stub -- an unrecognized word gets a
clear 422 naming it, never a guessed gloss sequence. The frontend displays
the returned gloss_sequence (components/Transcript) and drives the 3D
avatar with it (components/Avatar, Phase 15) -- gloss->pose mapping turned
out to be simple static data, so it lives entirely client-side
(components/Avatar/poses.ts) rather than as a backend service/endpoint.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.translate import TextToGlossRequest, TextToGlossResponse
from app.services.translation_service import RuleBasedTranslationService

router = APIRouter(prefix="/translate", tags=["translate"])

_translation_service = RuleBasedTranslationService()


@router.post("/text-to-gloss", response_model=TextToGlossResponse)
def text_to_gloss(request: TextToGlossRequest) -> TextToGlossResponse:
    try:
        gloss_sequence = _translation_service.text_to_gloss(request.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TextToGlossResponse(gloss_sequence=gloss_sequence)
