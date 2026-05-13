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


def test_websocket_chat():
    client = TestClient(app)

    with client.websocket_connect("/v1/chat/ws") as websocket:
        websocket.send_json({"session_id": "ws-demo", "message": "把空调调到22度"})
        events = []
        while True:
            message = websocket.receive_json()
            events.append(message["event"])
            if message["event"] == "done":
                break

    assert "tool_start" in events
    assert "final" in events
    assert events[-1] == "done"
