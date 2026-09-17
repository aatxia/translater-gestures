from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_text_to_gloss_returns_the_parsed_sequence():
    response = client.post("/translate/text-to-gloss", json={"text": "Я хочу води."})

    assert response.status_code == 200
    body = response.json()
    assert body["gloss_sequence"] == ["I", "WANT", "WATER"]
    # The internal English gloss codes above are never what a person should
    # read -- gloss_labels/composed_text carry the actual Ukrainian.
    assert body["gloss_labels"] == [
        {"text": "Я", "is_fingerspell": False},
        {"text": "хотіти", "is_fingerspell": False},
        {"text": "вода", "is_fingerspell": False},
    ]
    assert body["composed_text"] == "Я хочу води."


def test_text_to_gloss_standalone_phrase():
    response = client.post("/translate/text-to-gloss", json={"text": "Привіт."})

    assert response.status_code == 200
    body = response.json()
    assert body["gloss_sequence"] == ["PRIVIT"]
    assert body["gloss_labels"] == [{"text": "привіт", "is_fingerspell": False}]
    assert body["composed_text"] == "Привіт."


def test_text_to_gloss_fingerspells_a_word_outside_the_lexicon():
    # Phase 16: no lexicon noun for "кавун", but it's spellable letter-by-
    # letter, so this succeeds instead of a 422.
    response = client.post("/translate/text-to-gloss", json={"text": "Я хочу кавун."})

    assert response.status_code == 200
    body = response.json()
    assert body["gloss_sequence"] == ["I", "WANT", "FS_К", "FS_А", "FS_В", "FS_У", "FS_Н"]
    assert body["gloss_labels"] == [
        {"text": "Я", "is_fingerspell": False},
        {"text": "хотіти", "is_fingerspell": False},
        {"text": "Кавун", "is_fingerspell": True},
    ]
    assert body["composed_text"] == "Я хочу Кавун."


def test_text_to_gloss_returns_422_with_a_clear_message_for_unspellable_words():
    response = client.post("/translate/text-to-gloss", json={"text": "Я хочу pizza."})

    assert response.status_code == 422
    assert "pizza" in response.json()["detail"]


def test_text_to_gloss_rejects_empty_text():
    response = client.post("/translate/text-to-gloss", json={"text": ""})

    assert response.status_code == 422
