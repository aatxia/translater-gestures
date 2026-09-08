"""
lexicon — the shared, hand-authored gloss<->Ukrainian vocabulary used by
both directions of rule-based translation: ml/nlp/gloss_to_text.py (Phase 12,
gloss -> text) and ml/nlp/text_to_gloss.py (Phase 14, text -> gloss). Defined
once so the two directions can never silently drift apart -- a word this
project can compose into text is also a word it can parse back out of text.

Coverage is intentionally small: no public annotated УЖМ dataset exists yet
(Phase 8), so there's no real gloss vocabulary to build a broader lexicon
from. See PROJECT_STATUS.md.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PronounEntry:
    lemma: str  # capitalized surface form, e.g. "Я"
    person_key: str  # selects the matching VerbEntry.conjugation entry


@dataclass(frozen=True)
class VerbEntry:
    conjugation: dict[str, str]  # person_key -> conjugated surface form
    governs_case: str  # which NounEntry.cases key a direct object takes


@dataclass(frozen=True)
class NounEntry:
    cases: dict[str, str]  # case name -> surface form


@dataclass(frozen=True)
class StandaloneEntry:
    text: str  # lowercase surface form; gloss_to_text capitalizes it


PRONOUNS: dict[str, PronounEntry] = {
    "I": PronounEntry("Я", "1sg"),
    "YOU": PronounEntry("Ти", "2sg"),
    "WE": PronounEntry("Ми", "1pl"),
}

VERBS: dict[str, VerbEntry] = {
    "WANT": VerbEntry(
        conjugation={"1sg": "хочу", "2sg": "хочеш", "1pl": "хочемо"},
        governs_case="genitive_partitive",
    ),
    "LIKE": VerbEntry(
        conjugation={"1sg": "люблю", "2sg": "любиш", "1pl": "любимо"},
        governs_case="accusative",
    ),
    "HAVE": VerbEntry(
        conjugation={"1sg": "маю", "2sg": "маєш", "1pl": "маємо"},
        governs_case="accusative",
    ),
}

NOUNS: dict[str, NounEntry] = {
    "WATER": NounEntry({"nominative": "вода", "genitive_partitive": "води", "accusative": "воду"}),
    "BREAD": NounEntry({"nominative": "хліб", "genitive_partitive": "хліба", "accusative": "хліб"}),
    "TEA": NounEntry({"nominative": "чай", "genitive_partitive": "чаю", "accusative": "чай"}),
}

# ml/datasets/synthetic.py's DEMO_GLOSSES, mapped to their real meaning.
STANDALONE: dict[str, StandaloneEntry] = {
    "PRIVIT": StandaloneEntry("привіт"),
    "DYAKUYU": StandaloneEntry("дякую"),
    "TAK": StandaloneEntry("так"),
    "NI": StandaloneEntry("ні"),
    "BUD_LASKA": StandaloneEntry("будь ласка"),
}

NEGATION_GLOSS = "NOT"  # e.g. ["I", "NOT", "WANT", "WATER"] <-> "Я не хочу води."
NEGATION_PARTICLE = "не"
