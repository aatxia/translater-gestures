"""
TranslationService — abstraction over gloss-sequence -> natural Ukrainian text
(and the reverse direction, text -> gloss sequence for the avatar).

STATUS: gloss_to_text is real as of Phase 12 -- RuleBasedTranslationService
delegates to ml/nlp/gloss_to_text.py, a genuine (if narrow, hand-authored
lexicon) rule-based grammar engine per master-prompt section 14/17, not a
naive `' '.join()`. text_to_gloss stays NotConfigured until Phase 14 --
deliberately scheduled there rather than stubbed early, so it can be built
and tested alongside the text-parsing it actually needs to handle.

Later an HF-Transformers-backed implementation can replace either direction
via `NLP_BACKEND=huggingface` in .env without touching callers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ml.nlp.gloss_to_text import compose_sentence


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


class RuleBasedTranslationService(TranslationService):
    """Phase 12: gloss_to_text is a real rule-based engine (see
    ml/nlp/gloss_to_text.py for exactly which glosses/patterns it covers --
    coverage is intentionally small, since no public annotated УЖМ dataset
    exists yet to build a broader lexicon from). An unrecognized gloss or
    gloss combination raises UnknownGlossError/UnsupportedPatternError
    (both ValueError subclasses) rather than guessing.

    text_to_gloss is unchanged from NotConfiguredTranslationService --
    that direction is Phase 14's job.
    """

    def gloss_to_text(self, gloss_sequence: list[str]) -> str:
        return compose_sentence(gloss_sequence)

    def text_to_gloss(self, text: str) -> list[str]:
        raise NotConfiguredError(
            "Text-to-gloss NLP is not implemented yet (scheduled: Phase 14). "
            "See docs/architecture.md and PROJECT_STATUS.md."
        )
