from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_session():
    client = TestClient(app)

    response = client.post("/v1/sessions")

    assert response.status_code == 200
    assert "session_id" in response.json()

