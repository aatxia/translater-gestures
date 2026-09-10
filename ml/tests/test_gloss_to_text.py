import pytest

from ml.nlp.gloss_to_text import (
    UnknownGlossError,
    UnsupportedPatternError,
    compose_sentence,
)


@pytest.mark.parametrize(
    ("gloss_sequence", "expected"),
    [
        (["PRIVIT"], "Привіт."),
        (["DYAKUYU"], "Дякую."),
        (["TAK"], "Так."),
        (["NI"], "Ні."),
        (["BUD_LASKA"], "Будь ласка."),
    ],
)
def test_standalone_gloss_composes_a_capitalized_sentence(gloss_sequence, expected):
    assert compose_sentence(gloss_sequence) == expected


def test_pronoun_verb_noun_conjugates_and_declines_not_a_naive_join():
    # The exact example from TranslationService.gloss_to_text()'s docstring.
    assert compose_sentence(["I", "WANT", "WATER"]) == "Я хочу води."


def test_different_pronoun_selects_different_conjugation():
    assert compose_sentence(["YOU", "WANT", "WATER"]) == "Ти хочеш води."
    assert compose_sentence(["WE", "WANT", "WATER"]) == "Ми хочемо води."


def test_verb_governs_case_correctly_per_verb():
    # LIKE/HAVE govern accusative, not genitive_partitive like WANT.
    assert compose_sentence(["I", "LIKE", "BREAD"]) == "Я люблю хліб."
    assert compose_sentence(["I", "HAVE", "TEA"]) == "Я маю чай."


def test_pronoun_verb_without_object():
    assert compose_sentence(["I", "HAVE"]) == "Я маю."


def test_preverbal_negation_is_inserted_before_the_verb_not_where_not_appeared():
    assert compose_sentence(["I", "NOT", "WANT", "WATER"]) == "Я не хочу води."
    assert compose_sentence(["I", "NOT", "HAVE"]) == "Я не маю."


def test_unknown_gloss_raises_a_clear_error_not_a_guess():
    with pytest.raises(UnknownGlossError, match="WATERMELON"):
        compose_sentence(["I", "WANT", "WATERMELON"])


def test_recognized_glosses_in_an_unsupported_pattern_raise_clearly():
    # Two standalone words in a row isn't a pattern this engine composes.
    with pytest.raises(UnsupportedPatternError):
        compose_sentence(["TAK", "NI"])


def test_noun_then_verb_then_pronoun_is_not_the_supported_order():
    with pytest.raises(UnsupportedPatternError):
        compose_sentence(["WATER", "WANT", "I"])


def test_empty_sequence_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        compose_sentence([])


def test_verb_missing_a_conjugation_for_the_subject_raises_unsupported_pattern(monkeypatch):
    from ml.nlp import gloss_to_text
    from ml.nlp.lexicon import VerbEntry

    incomplete_verb = VerbEntry(conjugation={"2sg": "хочеш"}, governs_case="accusative")
    monkeypatch.setitem(gloss_to_text.VERBS, "WANT", incomplete_verb)

    with pytest.raises(UnsupportedPatternError, match="1sg"):
        compose_sentence(["I", "WANT"])


def test_verb_governing_a_case_the_noun_lacks_raises_unsupported_pattern(monkeypatch):
    from ml.nlp import gloss_to_text
    from ml.nlp.lexicon import NounEntry

    incomplete_noun = NounEntry(cases={"accusative": "хліб"})
    monkeypatch.setitem(gloss_to_text.NOUNS, "BREAD", incomplete_noun)

    with pytest.raises(UnsupportedPatternError, match="genitive_partitive"):
        compose_sentence(["I", "WANT", "BREAD"])


def test_fingerspelled_glosses_compose_into_the_spelled_word_standalone():
    gloss_sequence = ["FS_О", "FS_К", "FS_С", "FS_А", "FS_Н", "FS_А"]
    assert compose_sentence(gloss_sequence) == "Оксана."


def test_fingerspelled_glosses_fill_the_object_slot_of_the_svo_pattern():
    gloss_sequence = ["I", "LIKE", "FS_О", "FS_К", "FS_С", "FS_А", "FS_Н", "FS_У"]
    assert compose_sentence(gloss_sequence) == "Я люблю Оксану."


def test_fingerspelled_object_is_not_declined_into_the_verbs_governed_case():
    # WANT governs genitive_partitive for a lexicon NOUN ("WATER" -> "води"),
    # but a fingerspelled word has no case data -- it's inserted as spelled,
    # capitalized, not force-declined into a case that doesn't exist for it.
    gloss_sequence = ["I", "WANT", "FS_К", "FS_А", "FS_В", "FS_У", "FS_Н"]
    assert compose_sentence(gloss_sequence) == "Я хочу Кавун."


def test_is_question_ends_standalone_sentence_with_a_question_mark():
    assert compose_sentence(["TAK"], is_question=True) == "Так?"


def test_is_question_ends_a_fingerspelled_standalone_word_with_a_question_mark():
    gloss_sequence = ["FS_О", "FS_К", "FS_С", "FS_А", "FS_Н", "FS_А"]
    assert compose_sentence(gloss_sequence, is_question=True) == "Оксана?"


def test_is_question_ends_pronoun_verb_with_a_question_mark():
    assert compose_sentence(["I", "HAVE"], is_question=True) == "Я маю?"


def test_is_question_ends_svo_sentence_with_a_question_mark():
    assert compose_sentence(["I", "WANT", "WATER"], is_question=True) == "Я хочу води?"


def test_is_question_defaults_to_false():
    assert compose_sentence(["TAK"]) == "Так."
