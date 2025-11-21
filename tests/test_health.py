"""Smoke tests for the application health endpoint."""

from main import app


def test_health_endpoint_returns_ok_status():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["service"] == "StrataScribe"
