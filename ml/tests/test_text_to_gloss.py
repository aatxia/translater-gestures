import pytest

from ml.nlp.gloss_to_text import compose_sentence
from ml.nlp.text_to_gloss import UnrecognizedWordError, parse_gloss_sequence


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Привіт.", ["PRIVIT"]),
        ("привіт", ["PRIVIT"]),
        ("Дякую.", ["DYAKUYU"]),
        ("Так.", ["TAK"]),
        ("Ні.", ["NI"]),
        ("Будь ласка.", ["BUD_LASKA"]),
        ("будь ласка", ["BUD_LASKA"]),
    ],
)
def test_standalone_phrase_parses_to_its_gloss(text, expected):
    assert parse_gloss_sequence(text) == expected


def test_pronoun_verb_noun_sentence_parses_correctly():
    assert parse_gloss_sequence("Я хочу води.") == ["I", "WANT", "WATER"]


def test_different_conjugated_forms_resolve_to_the_same_verb_gloss():
    assert parse_gloss_sequence("Ти хочеш води.") == ["YOU", "WANT", "WATER"]
    assert parse_gloss_sequence("Ми хочемо води.") == ["WE", "WANT", "WATER"]


def test_different_case_forms_resolve_to_the_same_noun_gloss():
    assert parse_gloss_sequence("Я люблю хліб.") == ["I", "LIKE", "BREAD"]
    assert parse_gloss_sequence("Я маю чай.") == ["I", "HAVE", "TEA"]


def test_negation_particle_maps_to_the_negation_gloss_in_place():
    assert parse_gloss_sequence("Я не хочу води.") == ["I", "NOT", "WANT", "WATER"]
    assert parse_gloss_sequence("Я не маю.") == ["I", "NOT", "HAVE"]


def test_pronoun_verb_without_object():
    assert parse_gloss_sequence("Я маю.") == ["I", "HAVE"]


def test_unrecognized_word_raises_clearly():
    with pytest.raises(UnrecognizedWordError, match="кавун"):
        parse_gloss_sequence("Я хочу кавун.")


def test_empty_text_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        parse_gloss_sequence("")
    with pytest.raises(ValueError, match="must not be empty"):
        parse_gloss_sequence("   ")


@pytest.mark.parametrize(
    "text",
    [
        "Привіт.",
        "Дякую.",
        "Так.",
        "Ні.",
        "Будь ласка.",
        "Я хочу води.",
        "Ти хочеш води.",
        "Ми хочемо води.",
        "Я люблю хліб.",
        "Я маю чай.",
        "Я не хочу води.",
        "Я не маю.",
        "Я маю.",
    ],
)
def test_round_trips_through_compose_sentence(text):
    """Every sentence text_to_gloss can parse, gloss_to_text can compose
    back -- the two directions share one lexicon by construction, so they
    can never silently disagree about vocabulary."""
    gloss_sequence = parse_gloss_sequence(text)
    assert compose_sentence(gloss_sequence) == text
