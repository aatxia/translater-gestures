from __future__ import annotations

from pydantic import BaseModel, Field


class TextToGlossRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Ukrainian text to translate into a gloss sequence")


class GlossLabel(BaseModel):
    text: str = Field(..., description="A Ukrainian word/phrase, ready to show a user")
    is_fingerspell: bool = Field(
        ..., description="True if this word came from letter-by-letter fingerspelling, not the dictionary"
    )


class TextToGlossResponse(BaseModel):
    gloss_sequence: list[str] = Field(..., description="УЖМ gloss tokens, in signing order")
    # The frontend must never show gloss_sequence's own tokens (internal
    # English identifiers like "WANT"/"CAR") to the user -- these two
    # fields are the actual Ukrainian words to display instead.
    gloss_labels: list[GlossLabel] = Field(
        ..., description="Ukrainian word/phrase per gloss token (PAST tense markers omitted -- not a word)"
    )
    composed_text: str | None = Field(
        None,
        description="Full composed Ukrainian sentence, when the gloss sequence matches a "
        "supported grammatical pattern; null otherwise (still shown via gloss_labels)",
    )
