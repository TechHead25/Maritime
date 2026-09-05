"""Integration tests for the Drift Simulation REST API endpoints."""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. POST /api/cases/{case_id}/drift
# ---------------------------------------------------------------------------

def test_api_post_drift_simulation_success():
    payload = {
        "time_step_minutes": 30,
        "max_hours_backward": 24.0,
        "particle_count": 500,
        "wind_leeway_factor": 0.03,
        "current_advection_factor": 1.00,
        "random_seed": 42,
        "estimated_release_hours_ago": 14.0,
        "release_window_half_width_hours": 2.0
    }
    response = client.post("/api/cases/demo-case-001/drift", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "demo-case-001"
    assert data["status"] == "DRIFT_SIMULATION_COMPLETED"
    assert "simulation" in data
    assert "release_window" in data
    assert "probability_clouds" in data
    assert len(data["probability_clouds"]) == 49  # (24h * 2 steps/h) + 1 = 49 clouds

    # Origin centroid should be near [101.83, 2.61]
    origin = data["origin_centroid"]["coordinates"]
    assert abs(origin[0] - 101.83) < 0.05
    assert abs(origin[1] - 2.61) < 0.05
    assert data["origin_uncertainty_radius_km"] > 0.0

    # Verify that case status was updated
    case_res = client.get("/api/cases/demo-case-001")
    assert case_res.status_code == 200
    assert case_res.json()["case"]["status"] == "DRIFT_SIMULATED"


def test_api_post_drift_determinism():
    payload = {
        "time_step_minutes": 30,
        "max_hours_backward": 12.0,
        "particle_count": 300,
        "random_seed": 123
    }
    res1 = client.post("/api/cases/demo-case-001/drift", json=payload).json()
    res2 = client.post("/api/cases/demo-case-001/drift", json=payload).json()

    assert res1["origin_centroid"]["coordinates"] == res2["origin_centroid"]["coordinates"]
    assert res1["origin_uncertainty_radius_km"] == res2["origin_uncertainty_radius_km"]


def test_api_post_drift_invalid_params():
    # Invalid particle count (< 10)
    response = client.post("/api/cases/demo-case-001/drift", json={"particle_count": 2})
    assert response.status_code == 422

    # Invalid timestep (> 120 min)
    response = client.post("/api/cases/demo-case-001/drift", json={"time_step_minutes": 300})
    assert response.status_code == 422


def test_api_post_drift_case_not_found():
    response = client.post("/api/cases/non-existent-case-id/drift", json={})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 2. GET /api/cases/{case_id}/drift
# ---------------------------------------------------------------------------

def test_api_get_latest_drift_simulation():
    # First run the simulation
    client.post("/api/cases/demo-case-001/drift", json={"particle_count": 200})

    # Query the latest computed result
    response = client.get("/api/cases/demo-case-001/drift")
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "demo-case-001"
    assert data["status"] == "DRIFT_SIMULATION_COMPLETED"
    assert data["simulation"]["id"] is not None
    assert len(data["probability_clouds"]) > 0


def test_api_get_drift_not_found_on_new_case():
    # Create an empty case with no simulation run yet
    new_case = client.post("/api/cases", json={"title": "Empty Case For Drift"}).json()
    case_id = new_case["id"]

    response = client.get(f"/api/cases/{case_id}/drift")
    assert response.status_code == 404
    assert "no drift simulation has been computed" in response.json()["detail"].lower()
