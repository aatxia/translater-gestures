"""
TranslationService — abstraction over gloss-sequence -> natural Ukrainian text
(and the reverse direction, text -> gloss sequence for the avatar).

STATUS: interface only in Phase 2. The rule-based baseline (per master-prompt
section 14/17) is real, buildable logic (no ML dependency) and will be
implemented in Phase 12 (gloss->text) and Phase 14 (text->gloss) — deliberately
scheduled there rather than stubbed early, so it can be built and tested
alongside the gloss sequences it actually needs to handle.

Once implemented, `RuleBasedTranslationService` will satisfy this interface,
and later an HF-Transformers-backed implementation can replace it via
`NLP_BACKEND=huggingface` in .env without touching callers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class NotConfiguredError(RuntimeError):
    """Raised when a translation direction is requested before it's implemented."""


class TranslationService(ABC):
    @abstractmethod
    def gloss_to_text(self, gloss_sequence: list[str]) -> str:
        """Gloss sequence (e.g. ['I', 'WANT', 'WATER']) -> natural Ukrainian
        sentence (e.g. 'Я хочу води.'), applying case/number/gender/word-order
        rules -- NOT a naive ' '.join(). Implemented in Phase 12."""
        raise NotImplementedError

    @abstractmethod
    def text_to_gloss(self, text: str) -> list[str]:
        """Ukrainian text -> gloss sequence, for driving the avatar.
        Implemented in Phase 14."""
        raise NotImplementedError


class NotConfiguredTranslationService(TranslationService):
    def gloss_to_text(self, gloss_sequence: list[str]) -> str:
        raise NotConfiguredError(
            "Gloss-to-text NLP is not implemented yet (scheduled: Phase 12). "
            "See docs/architecture.md and PROJECT_STATUS.md."
        )

    def text_to_gloss(self, text: str) -> list[str]:
        raise NotConfiguredError(
            "Text-to-gloss NLP is not implemented yet (scheduled: Phase 14). "
            "See docs/architecture.md and PROJECT_STATUS.md."
        )
