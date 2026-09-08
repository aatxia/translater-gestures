import pytest
from app.services.translation_service import RuleBasedTranslationService


def test_gloss_to_text_delegates_to_the_real_rule_based_engine():
    service = RuleBasedTranslationService()

    assert service.gloss_to_text(["I", "WANT", "WATER"]) == "Я хочу води."
    assert service.gloss_to_text(["TAK"]) == "Так."


def test_gloss_to_text_raises_clearly_on_unknown_gloss():
    service = RuleBasedTranslationService()

    with pytest.raises(ValueError, match="WATERMELON"):
        service.gloss_to_text(["I", "WANT", "WATERMELON"])


def test_text_to_gloss_delegates_to_the_real_rule_based_engine():
    service = RuleBasedTranslationService()

    assert service.text_to_gloss("Я хочу води.") == ["I", "WANT", "WATER"]
    assert service.text_to_gloss("Так.") == ["TAK"]


def test_text_to_gloss_raises_clearly_on_unrecognized_word():
    service = RuleBasedTranslationService()

    with pytest.raises(ValueError, match="кавун"):
        service.text_to_gloss("Я хочу кавун.")
