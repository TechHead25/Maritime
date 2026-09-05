"""Unit and health check tests for FastAPI root and diagnostic endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Maritime Oil-Spill" in data["platform"]
    assert "version" in data
    assert "health" in data
    assert "cases" in data


def test_health_endpoints():
    for prefix in ["", "/api", "/api/v1"]:
        # Test /health
        res_health = client.get(f"{prefix}/health" if prefix else "/health")
        assert res_health.status_code == 200
        hdata = res_health.json()
        assert hdata["status"] == "healthy"
        assert "timestamp_utc" in hdata

        # Test /health/live
        res_live = client.get(f"{prefix}/health/live" if prefix else "/health/live")
        assert res_live.status_code == 200
        assert res_live.json()["status"] == "alive"

        # Test /health/ready
        res_ready = client.get(f"{prefix}/health/ready" if prefix else "/health/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "ready"
        assert res_ready.json()["loaded_cases_count"] >= 1
