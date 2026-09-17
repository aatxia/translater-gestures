"""
Coverage for the expanded lexicon (~50 words: 7 pronouns x 15 verbs x 24
nouns) -- the point of expanding it was "sentences, not single words", so
this exhaustively sweeps every grammatically valid pronoun/verb/(noun)
combination through both directions and checks it round-trips exactly,
rather than spot-checking a handful by hand.
"""
import pytest

from ml.nlp.gloss_to_text import UnsupportedPatternError, compose_sentence
from ml.nlp.lexicon import NOUNS, PRONOUNS, VERBS
from ml.nlp.text_to_gloss import parse_gloss_sequence


def _valid_two_token_sequences() -> list[list[str]]:
    """Every [PRONOUN, VERB] pair where the verb actually conjugates for
    that pronoun's person_key -- some verbs intentionally don't cover
    every person (see test_verb_missing_a_conjugation_for_the_subject_...
    in test_gloss_to_text.py), so this only includes real pairs."""
    sequences = []
    for pronoun_gloss, pronoun in PRONOUNS.items():
        for verb_gloss, verb in VERBS.items():
            if pronoun.person_key in verb.conjugation:
                sequences.append([pronoun_gloss, verb_gloss])
    return sequences


def _valid_three_token_sequences() -> list[list[str]]:
    """Every [PRONOUN, VERB, NOUN] triple where the verb conjugates for
    that pronoun AND the noun actually has the case the verb governs
    (mass nouns have both cases; count nouns only accusative -- see
    lexicon.py's module docstring for why that's a grammar decision)."""
    sequences = []
    for pronoun_gloss, pronoun in PRONOUNS.items():
        for verb_gloss, verb in VERBS.items():
            if pronoun.person_key not in verb.conjugation:
                continue
            for noun_gloss, noun in NOUNS.items():
                if verb.governs_case in noun.cases:
                    sequences.append([pronoun_gloss, verb_gloss, noun_gloss])
    return sequences


TWO_TOKEN_SEQUENCES = _valid_two_token_sequences()
THREE_TOKEN_SEQUENCES = _valid_three_token_sequences()


def test_lexicon_is_actually_large_enough_for_real_sentences():
    # Guards against silently shrinking back down -- the whole point of
    # this expansion was moving past single-word translation.
    assert len(PRONOUNS) >= 7
    assert len(VERBS) >= 15
    assert len(NOUNS) >= 20
    assert len(PRONOUNS) + len(VERBS) + len(NOUNS) >= 45


@pytest.mark.parametrize("gloss_sequence", TWO_TOKEN_SEQUENCES, ids=lambda seq: "_".join(seq))
def test_every_valid_pronoun_verb_pair_round_trips(gloss_sequence):
    text = compose_sentence(gloss_sequence)
    assert parse_gloss_sequence(text) == gloss_sequence


@pytest.mark.parametrize("gloss_sequence", THREE_TOKEN_SEQUENCES, ids=lambda seq: "_".join(seq))
def test_every_valid_pronoun_verb_noun_triple_round_trips(gloss_sequence):
    text = compose_sentence(gloss_sequence)
    assert parse_gloss_sequence(text) == gloss_sequence


def test_third_person_singular_is_shared_by_he_and_she():
    # Ukrainian present tense doesn't mark gender -- "він хоче" / "вона
    # хоче" use the identical verb form (lexicon.py's module docstring).
    assert compose_sentence(["HE", "WANT", "WATER"]) == "Він хоче води."
    assert compose_sentence(["SHE", "WANT", "WATER"]) == "Вона хоче води."


def test_animate_noun_accusative_equals_genitive_not_nominative():
    # A real Ukrainian rule: "бачу друга", never "*бачу друг".
    assert compose_sentence(["I", "SEE", "FRIEND"]) == "Я бачу друга."


def test_mass_noun_works_with_both_governed_cases():
    assert compose_sentence(["I", "WANT", "COFFEE"]) == "Я хочу кави."  # genitive_partitive
    assert compose_sentence(["I", "LIKE", "COFFEE"]) == "Я люблю каву."  # accusative


def test_count_noun_correctly_refuses_genitive_partitive_pairing():
    # "хочу грошей" isn't idiomatic partitive the way "хочу води" is --
    # MONEY intentionally has no genitive_partitive form, so WANT+MONEY
    # must raise rather than compose a dubious sentence.
    with pytest.raises(UnsupportedPatternError, match="genitive_partitive"):
        compose_sentence(["I", "WANT", "MONEY"])


def test_intransitive_only_verbs_compose_without_an_object():
    assert compose_sentence(["WE", "LIVE"]) == "Ми живемо."
    assert compose_sentence(["THEY", "SLEEP"]) == "Вони сплять."
    assert compose_sentence(["I", "SPEAK"]) == "Я говорю."


def test_negation_composes_correctly_with_a_new_verb_and_noun():
    assert compose_sentence(["I", "NOT", "DRINK", "TEA"]) == "Я не п'ю чаю."
    assert parse_gloss_sequence("Я не п'ю чаю.") == ["I", "NOT", "DRINK", "TEA"]


def test_expanded_standalone_phrases_round_trip():
    assert compose_sentence(["DOBRANICH"]) == "Добраніч."
    assert compose_sentence(["VYBACHTE"]) == "Вибачте."
    assert compose_sentence(["DO_POBACHENNYA"]) == "До побачення."
    assert parse_gloss_sequence("До побачення.") == ["DO_POBACHENNYA"]
