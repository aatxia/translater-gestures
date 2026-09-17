"""
POST /translate/text-to-gloss — Phase 14: Ukrainian text -> gloss sequence,
via RuleBasedTranslationService (ml/nlp/text_to_gloss.py). A real (if
narrow-coverage) rule-based parse, not a stub -- an unrecognized word gets a
clear 422 naming it, never a guessed gloss sequence. The frontend displays
the returned gloss_sequence (components/Transcript) and drives the 3D
avatar with it (components/Avatar, Phase 15) -- gloss->pose mapping turned
out to be simple static data, so it lives entirely client-side
(components/Avatar/poses.ts) rather than as a backend service/endpoint.

gloss_sequence's own tokens (e.g. "WANT", "CAR") are internal English
identifiers, not Ukrainian -- never meant for a person to read. Alongside
it, this also returns gloss_labels (the real Ukrainian word per token,
ml/nlp/gloss_to_text.py::gloss_display_labels) and, when the sequence
matches a supported grammatical pattern, composed_text (the actual
Ukrainian sentence, same engine Phase 12 uses for gloss->text). Composing
never turns a successful parse into a 422: an UnsupportedPatternError here
just means composed_text is null, not that the translation failed --
gloss_labels still lets the user see what was understood.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.translate import GlossLabel, TextToGlossRequest, TextToGlossResponse
from app.services.translation_service import RuleBasedTranslationService
from ml.nlp.gloss_to_text import compose_sentence as _compose_sentence
from ml.nlp.gloss_to_text import gloss_display_labels

router = APIRouter(prefix="/translate", tags=["translate"])

_translation_service = RuleBasedTranslationService()


@router.post("/text-to-gloss", response_model=TextToGlossResponse)
def text_to_gloss(request: TextToGlossRequest) -> TextToGlossResponse:
    try:
        gloss_sequence = _translation_service.text_to_gloss(request.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        composed_text = _compose_sentence(gloss_sequence)
    except ValueError:
        composed_text = None

    return TextToGlossResponse(
        gloss_sequence=gloss_sequence,
        gloss_labels=[
            GlossLabel(text=text, is_fingerspell=is_fingerspell)
            for text, is_fingerspell in gloss_display_labels(gloss_sequence)
        ],
        composed_text=composed_text,
    )
