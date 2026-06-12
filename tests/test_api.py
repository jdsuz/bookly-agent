from __future__ import annotations

import pytest
from flask import Flask

from bookly_agent.server.flask_blueprint import create_blueprint


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(create_blueprint())
    return app.test_client()


def test_chat_endpoint(client):
    response = client.post(
        "/api/support/chat",
        json={"session_id": "api-test", "message": "Where is order ORD-1042?"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["reply"]
    assert payload["session_id"] == "api-test"


def test_chat_requires_session(client):
    response = client.post("/api/support/chat", json={"message": "hello"})
    assert response.status_code == 400
