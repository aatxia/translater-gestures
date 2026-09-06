from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "features" in body
    assert set(body["features"].keys()) == {"hands", "pose", "face"}


def test_health_check_reports_ml_not_implemented_honestly():
    """Phase 2: no trained model yet -- health check must say so, not fake readiness."""
    response = client.get("/health")
    body = response.json()
    assert body["ml_pipeline_status"] == "not_implemented"


def test_unknown_route_returns_404():
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
