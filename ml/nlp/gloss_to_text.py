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
from -- see ml/nlp/lexicon.py, shared with ml/nlp/text_to_gloss.py (Phase 14)
so the two directions never disagree about vocabulary. An unrecognized
gloss, or a recognized-glosses-but-unrecognized-pattern combination, raises
a clear, typed error rather than guessing a plausible-looking but possibly
ungrammatical sentence -- the same "no fake AI" rule the rest of this
project follows for CV/ML.

Phase 16: a run of consecutive FS_ fingerspelling gloss tokens (see
ml/nlp/fingerspelling.py) composes into the word they spell -- standalone,
or filling the object slot of the SVO pattern. Spelling is caseless/formless
(exactly the letters that were spelled, capitalized), never Ukrainian-
declined into the verb's governed case the way a lexicon NOUN is -- there's
no real declension data for arbitrary fingerspelled words to draw on.

Phase 17: `is_question` swaps the trailing "." for "?" -- sign language
questions are marked non-manually (raised eyebrows for yes/no, furrowed for
wh-, section 19), never by a separate manual gloss, so there's no "?" gloss
token for a caller to include. See ml/features/facial_grammar.py, which
detects this from face landmarks; the caller decides whether it applies.
"""
from __future__ import annotations

from ml.nlp.fingerspelling import despell, is_fingerspell_gloss
from ml.nlp.lexicon import NEGATION_GLOSS, NOUNS, PRONOUNS, STANDALONE, VERBS


class UnknownGlossError(ValueError):
    """Raised when a gloss token isn't in the lexicon at all."""


class UnsupportedPatternError(ValueError):
    """Raised when every gloss is individually recognized, but their
    combination doesn't match any implemented composition rule."""


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
    if is_fingerspell_gloss(gloss):
        return "fingerspell"
    raise UnknownGlossError(f"Unknown gloss {gloss!r} -- not in the Phase 12 lexicon yet.")


def _group_units(gloss_sequence: list[str]) -> list[tuple[str, str]]:
    """gloss_sequence -> [(pose, value)], collapsing each consecutive run of
    fingerspelling glosses into one ("fingerspell", <word>) unit. `value` is
    the original gloss for every other pose. Raises UnknownGlossError first,
    same as classifying gloss-by-gloss would."""
    poses = [_classify(gloss) for gloss in gloss_sequence]

    units: list[tuple[str, str]] = []
    i = 0
    while i < len(gloss_sequence):
        if poses[i] != "fingerspell":
            units.append((poses[i], gloss_sequence[i]))
            i += 1
            continue
        j = i
        while j < len(gloss_sequence) and poses[j] == "fingerspell":
            j += 1
        units.append(("fingerspell", despell(gloss_sequence[i:j])))
        i = j
    return units


def compose_sentence(gloss_sequence: list[str], *, is_question: bool = False) -> str:
    """УЖМ gloss sequence -> natural Ukrainian sentence. See module
    docstring for exactly which glosses/patterns are supported; anything
    else raises UnknownGlossError or UnsupportedPatternError. `is_question`
    (Phase 17) ends the sentence with "?" instead of "." -- pass it when a
    non-manual question marker was detected alongside these glosses."""
    if not gloss_sequence:
        raise ValueError("gloss_sequence must not be empty")

    terminator = "?" if is_question else "."
    units = _group_units(gloss_sequence)  # raises UnknownGlossError first
    poses = [pose for pose, _ in units]

    # Pattern: a single standalone word (interjection/particle, or a fully
    # fingerspelled word on its own -- e.g. someone spelling just a name).
    if len(units) == 1 and poses[0] == "standalone":
        return STANDALONE[units[0][1]].text.capitalize() + terminator
    if len(units) == 1 and poses[0] == "fingerspell":
        return units[0][1].capitalize() + terminator

    # Pattern: [PRONOUN, (NOT), VERB, (NOUN | fingerspelled word)?] -- SVO
    # with optional preverbal negation.
    tokens = list(units)
    negated = len(tokens) >= 2 and poses[0] == "pronoun" and poses[1] == "negation"
    if negated:
        tokens.pop(1)
        poses = [poses[0], *poses[2:]]

    if len(tokens) in (2, 3) and poses[0] == "pronoun" and poses[1] == "verb":
        pronoun = PRONOUNS[tokens[0][1]]
        verb = VERBS[tokens[1][1]]
        if pronoun.person_key not in verb.conjugation:
            raise UnsupportedPatternError(
                f"Verb {tokens[1][1]!r} has no known conjugation for person {pronoun.person_key!r}."
            )
        predicate = verb.conjugation[pronoun.person_key]
        if negated:
            predicate = f"не {predicate}"

        if len(tokens) == 2:
            return f"{pronoun.lemma} {predicate}{terminator}"

        if poses[2] == "fingerspell":
            object_form = tokens[2][1].capitalize()
        elif poses[2] == "noun":
            noun = NOUNS[tokens[2][1]]
            if verb.governs_case not in noun.cases:
                raise UnsupportedPatternError(
                    f"Noun {tokens[2][1]!r} has no {verb.governs_case!r} form needed "
                    f"by verb {tokens[1][1]!r}."
                )
            object_form = noun.cases[verb.governs_case]
        else:
            raise UnsupportedPatternError(
                f"Expected a noun (or fingerspelled word) after the verb, got gloss {tokens[2][1]!r}."
            )
        return f"{pronoun.lemma} {predicate} {object_form}{terminator}"

    raise UnsupportedPatternError(
        f"No composition rule matches gloss sequence {gloss_sequence!r} "
        "(every gloss is individually recognized, but not this combination)."
    )
