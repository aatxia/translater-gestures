from __future__ import annotations

from pydantic import BaseModel, Field


class TextToGlossRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Ukrainian text to translate into a gloss sequence")


class TextToGlossResponse(BaseModel):
    gloss_sequence: list[str] = Field(..., description="УЖМ gloss tokens, in signing order")
