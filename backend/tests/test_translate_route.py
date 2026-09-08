from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_text_to_gloss_returns_the_parsed_sequence():
    response = client.post("/translate/text-to-gloss", json={"text": "Я хочу води."})

    assert response.status_code == 200
    assert response.json() == {"gloss_sequence": ["I", "WANT", "WATER"]}


def test_text_to_gloss_standalone_phrase():
    response = client.post("/translate/text-to-gloss", json={"text": "Привіт."})

    assert response.status_code == 200
    assert response.json() == {"gloss_sequence": ["PRIVIT"]}


def test_text_to_gloss_returns_422_with_a_clear_message_for_unrecognized_words():
    response = client.post("/translate/text-to-gloss", json={"text": "Я хочу кавун."})

    assert response.status_code == 422
    assert "кавун" in response.json()["detail"]


def test_text_to_gloss_rejects_empty_text():
    response = client.post("/translate/text-to-gloss", json={"text": ""})

    assert response.status_code == 422
