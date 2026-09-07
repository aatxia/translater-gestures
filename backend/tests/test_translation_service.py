import pytest
from app.services.translation_service import (
    NotConfiguredError,
    RuleBasedTranslationService,
)


def test_gloss_to_text_delegates_to_the_real_rule_based_engine():
    service = RuleBasedTranslationService()

    assert service.gloss_to_text(["I", "WANT", "WATER"]) == "Я хочу води."
    assert service.gloss_to_text(["TAK"]) == "Так."


def test_gloss_to_text_raises_clearly_on_unknown_gloss():
    service = RuleBasedTranslationService()

    with pytest.raises(ValueError, match="WATERMELON"):
        service.gloss_to_text(["I", "WANT", "WATERMELON"])


def test_text_to_gloss_still_not_configured_until_phase_14():
    service = RuleBasedTranslationService()

    with pytest.raises(NotConfiguredError, match="Phase 14"):
        service.text_to_gloss("Я хочу води.")
