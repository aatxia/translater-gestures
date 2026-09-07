"""
gloss_to_text — rule-based УЖМ gloss sequence -> natural Ukrainian sentence
(section 14/17). Framework-agnostic (no FastAPI import); wrapped by
backend/app/services/translation_service.py::RuleBasedTranslationService.

This is a genuine (if narrow) grammar engine, not `' '.join(gloss_sequence)`:
it conjugates verbs by subject person, declines nouns into whichever case
the verb governs, handles preverbal negation ("не" before the verb, the
correct position in Ukrainian -- not wherever NOT happened to appear in the
gloss order), and composes standard Ukrainian word order from sign order
(which doesn't have to match it).

Coverage is intentionally small: no public annotated УЖМ dataset exists yet
(Phase 8), so there is no real gloss vocabulary to build a broad lexicon
from. Every gloss and every sentence pattern this module accepts is listed
explicitly below. An unrecognized gloss, or a recognized-glosses-but-
unrecognized-pattern combination, raises a clear, typed error rather than
guessing a plausible-looking but possibly ungrammatical sentence -- the same
"no fake AI" rule the rest of this project follows for CV/ML.
"""
from __future__ import annotations

from dataclasses import dataclass


class UnknownGlossError(ValueError):
    """Raised when a gloss token isn't in the lexicon at all."""


class UnsupportedPatternError(ValueError):
    """Raised when every gloss is individually recognized, but their
    combination doesn't match any implemented composition rule."""


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
    text: str  # lowercase surface form; composition capitalizes it


# --- Lexicon -----------------------------------------------------------
# Covers: the Phase 8 demo-dataset glosses (all standalone interjections),
# plus a small illustrative pronoun/verb/noun set exercising real
# conjugation + case government -- exactly the ["I","WANT","WATER"] ->
# "Я хочу води." example from TranslationService.gloss_to_text()'s docstring.

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

NEGATION_GLOSS = "NOT"  # e.g. ["I", "NOT", "WANT", "WATER"] -> "Я не хочу води."


def _classify(gloss: str) -> str:
    if gloss in PRONOUNS:
        return "pronoun"
    if gloss in VERBS:
        return "verb"
    if gloss in NOUNS:
        return "noun"
    if gloss in STANDALONE:
        return "standalone"
    if gloss == NEGATION_GLOSS:
        return "negation"
    raise UnknownGlossError(f"Unknown gloss {gloss!r} -- not in the Phase 12 lexicon yet.")


def compose_sentence(gloss_sequence: list[str]) -> str:
    """УЖМ gloss sequence -> natural Ukrainian sentence. See module
    docstring for exactly which glosses/patterns are supported; anything
    else raises UnknownGlossError or UnsupportedPatternError."""
    if not gloss_sequence:
        raise ValueError("gloss_sequence must not be empty")

    poses = [_classify(gloss) for gloss in gloss_sequence]  # raises UnknownGlossError first

    # Pattern: a single standalone word (interjection/particle).
    if len(gloss_sequence) == 1 and poses[0] == "standalone":
        return STANDALONE[gloss_sequence[0]].text.capitalize() + "."

    # Pattern: [PRONOUN, (NOT), VERB, NOUN?] -- SVO with optional preverbal negation.
    tokens = list(gloss_sequence)
    negated = len(tokens) >= 2 and poses[0] == "pronoun" and poses[1] == "negation"
    if negated:
        tokens.pop(1)
        poses = [poses[0], *poses[2:]]

    if len(tokens) in (2, 3) and poses[0] == "pronoun" and poses[1] == "verb":
        pronoun = PRONOUNS[tokens[0]]
        verb = VERBS[tokens[1]]
        if pronoun.person_key not in verb.conjugation:
            raise UnsupportedPatternError(
                f"Verb {tokens[1]!r} has no known conjugation for person {pronoun.person_key!r}."
            )
        predicate = verb.conjugation[pronoun.person_key]
        if negated:
            predicate = f"не {predicate}"

        if len(tokens) == 2:
            return f"{pronoun.lemma} {predicate}."

        if poses[2] != "noun":
            raise UnsupportedPatternError(f"Expected a noun after the verb, got gloss {tokens[2]!r}.")
        noun = NOUNS[tokens[2]]
        if verb.governs_case not in noun.cases:
            raise UnsupportedPatternError(
                f"Noun {tokens[2]!r} has no {verb.governs_case!r} form needed by verb {tokens[1]!r}."
            )
        object_form = noun.cases[verb.governs_case]
        return f"{pronoun.lemma} {predicate} {object_form}."

    raise UnsupportedPatternError(
        f"No composition rule matches gloss sequence {gloss_sequence!r} "
        "(every gloss is individually recognized, but not this combination)."
    )
