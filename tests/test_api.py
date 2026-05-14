from fastapi.testclient import TestClient

from app.config.settings import get_settings
from app.main import app


def test_health():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"]


def test_request_id_header_is_preserved():
    client = TestClient(app)

    response = client.get("/health", headers={"X-Request-ID": "req-123"})

    assert response.headers["X-Request-ID"] == "req-123"


def test_metrics_endpoint():
    client = TestClient(app)
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_readiness():
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["tools"] >= 1


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
                assert message["data"]["tool_calls"] == 1
                break

    assert "tool_start" in events
    assert "final" in events
    assert events[-1] == "done"


def test_admin_config_hides_secrets():
    client = TestClient(app)

    response = client.get("/v1/admin/config")

    assert response.status_code == 200
    assert "config" in response.json()


def test_admin_runtime_config_update():
    client = TestClient(app)

    response = client.patch(
        "/v1/admin/config/runtime",
        json={"config": {"agent.max_steps": 3, "tools.enabled": ["weather", "ac_control"]}},
    )

    assert response.status_code == 200
    assert response.json()["changes"]["agent.max_steps"] == 3


def test_admin_audit_events():
    client = TestClient(app)

    response = client.get("/v1/admin/audit/events")

    assert response.status_code == 200
    assert "events" in response.json()


def test_admin_tool_schemas():
    client = TestClient(app)

    response = client.get("/v1/admin/tools/schemas")

    assert response.status_code == 200
    assert response.json()["tools"][0]["type"] == "function"


def test_chat_rejects_too_long_message():
    client = TestClient(app)
    settings = get_settings()

    response = client.post(
        "/v1/chat/stream",
        json={"session_id": "long-message", "message": "x" * (settings.chat_max_message_chars + 1)},
    )

    assert response.status_code == 413
