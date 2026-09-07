from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app

client = TestClient(app)


def test_websocket_sends_connection_ack_on_connect():
    with client.websocket_connect("/ws") as ws:
        ack = ws.receive_json()
        assert ack == {"type": "connection", "status": "ok"}


def test_valid_frame_gets_an_honest_ml_not_implemented_error_not_a_fake_prediction():
    """Core 'NO FAKE AI' rule: no trained model exists yet, so a well-formed
    frame message must get an explicit error, never a fabricated sign/text."""
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()  # connection ack
        ws.send_json({"type": "frame", "timestamp": 1, "data": "AAAA"})
        response = ws.receive_json()
        assert response["type"] == "error"
        assert "not" in response["message"].lower()


def test_invalid_json_returns_error_and_keeps_connection_open():
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_text("this is not json")
        response = ws.receive_json()
        assert response["type"] == "error"
        assert "json" in response["message"].lower()

        # connection must still be usable afterwards
        ws.send_json({"type": "frame", "timestamp": 1, "data": "AAAA"})
        follow_up = ws.receive_json()
        assert follow_up["type"] == "error"


def test_unknown_message_type_returns_error():
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_json({"type": "not_a_real_type", "foo": "bar"})
        response = ws.receive_json()
        assert response["type"] == "error"
        assert "unknown" in response["message"].lower()


def test_missing_required_field_returns_error():
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_json({"type": "frame", "timestamp": 1})  # missing 'data'
        response = ws.receive_json()
        assert response["type"] == "error"
        assert "invalid" in response["message"].lower()


def test_second_frame_within_min_interval_is_rate_limited():
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_json({"type": "frame", "timestamp": 1, "data": "AAAA"})
        first = ws.receive_json()
        assert first["type"] == "error"  # ML-not-ready error

        # Sent immediately after -- far faster than any configured max_fps allows.
        ws.send_json({"type": "frame", "timestamp": 2, "data": "AAAA"})
        second = ws.receive_json()
        assert second["type"] == "error"
        assert "rate" in second["message"].lower()


def test_oversized_message_closes_the_connection():
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        oversized_payload = "A" * 2_200_000  # exceeds default 2 MB WS_MAX_MESSAGE_SIZE_BYTES
        ws.send_json({"type": "frame", "timestamp": 1, "data": oversized_payload})
        response = ws.receive_json()
        assert response["type"] == "error"
        assert "exceeds" in response["message"].lower()

        try:
            ws.receive_json()
            assert False, "expected the server to have closed the connection"
        except WebSocketDisconnect:
            pass
