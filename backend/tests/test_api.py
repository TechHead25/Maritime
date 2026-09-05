"""Integration tests for the Investigation Case REST API."""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. GET /api/cases
# ---------------------------------------------------------------------------

def test_api_list_cases():
    response = client.get("/api/cases?include_synthetic=true")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check that demo-case-001 is loaded
    case_ids = [c["id"] for c in data]
    assert "demo-case-001" in case_ids


def test_api_v1_list_cases_compatibility():
    response = client.get("/api/v1/cases?include_synthetic=true")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# ---------------------------------------------------------------------------
# 2. GET /api/cases/{case_id}
# ---------------------------------------------------------------------------

def test_api_get_case_details_success():
    response = client.get("/api/cases/demo-case-001")
    assert response.status_code == 200
    data = response.json()

    # Verify structured detail keys
    assert "case" in data
    assert "sar_scenes" in data
    assert "slicks" in data
    assert "vessel_tracks" in data
    assert "environment" in data

    # Check case properties
    assert data["case"]["id"] == "demo-case-001"
    assert data["case"]["status"] == "CREATED"
    assert data["case"]["metadata"]["synthetic"] is True

    # Check SAR Scene
    assert len(data["sar_scenes"]) == 1
    assert "Sentinel-1A" in data["sar_scenes"][0]["satellite_platform"]

    # Check Slick Detection
    assert len(data["slicks"]) == 1
    assert data["slicks"][0]["area_sq_km"] == 14.85
    assert data["slicks"][0]["centroid"]["coordinates"] == [102.14, 2.877]

    # Check Vessel Tracks (4 benchmark vessels)
    assert len(data["vessel_tracks"]) == 4
    mmsi_list = [v["mmsi"] for v in data["vessel_tracks"]]
    assert "538009912" in mmsi_list  # Vessel A (Culprit)
    assert "352001140" in mmsi_list  # Vessel B (Wrong time)
    assert "211889900" in mmsi_list  # Vessel C (Distant)
    assert "636015522" in mmsi_list  # Vessel D (AIS gap)

    # Check Environmental Data
    assert "ocean_currents" in data["environment"]
    assert "wind_data" in data["environment"]


def test_api_get_case_details_not_found():
    response = client.get("/api/cases/non-existent-case-uuid-999")
    assert response.status_code == 404
    err = response.json()
    assert "detail" in err
    assert "not found" in err["detail"].lower()


# ---------------------------------------------------------------------------
# 3. GET /api/cases/{case_id}/summary
# ---------------------------------------------------------------------------

def test_api_get_case_summary_success():
    response = client.get("/api/cases/demo-case-001/summary")
    assert response.status_code == 200
    summary = response.json()

    assert summary["case_id"] == "demo-case-001"
    assert summary["title"].startswith("Malacca Strait")
    assert summary["status"] == "CREATED"
    assert summary["synthetic"] is True
    assert summary["vessel_count"] == 4
    
    # Check SAR summary
    assert summary["sar_scene"] is not None
    assert "Sentinel-1A" in summary["sar_scene"]["platform"]

    # Check Slick summary
    assert summary["slick_detection"] is not None
    assert summary["slick_detection"]["area_sq_km"] == 14.85
    assert summary["slick_detection"]["orientation_deg"] == 48.5

    # Check Environmental summary
    assert summary["ocean_currents"] is not None
    assert summary["ocean_currents"]["u_eastward_m_per_s"] == 0.789
    assert summary["wind_data"] is not None
    assert summary["wind_data"]["u_eastward_m_per_s"] == -3.5


def test_api_get_case_summary_not_found():
    response = client.get("/api/cases/non-existent-case-uuid-999/summary")
    assert response.status_code == 404
    err = response.json()
    assert "detail" in err


# ---------------------------------------------------------------------------
# 4. POST /api/cases (Create Case)
# ---------------------------------------------------------------------------

def test_api_create_case_success():
    payload = {
        "title": "Strait of Hormuz Incident #2026-09",
        "region_of_interest": {
            "type": "Polygon",
            "coordinates": [
                [[55.0, 25.0], [57.0, 25.0], [57.0, 27.0], [55.0, 27.0], [55.0, 25.0]]
            ]
        },
        "metadata": {"lead_investigator": "Captain Miller"}
    }
    response = client.post("/api/cases", json=payload)
    assert response.status_code == 201
    case = response.json()
    assert case["title"] == "Strait of Hormuz Incident #2026-09"
    assert case["status"] == "CREATED"
    assert case["id"] is not None

    # Verify retrieval
    get_res = client.get(f"/api/cases/{case['id']}")
    assert get_res.status_code == 200


def test_api_create_case_validation_error():
    # Empty title or missing title
    response = client.post("/api/cases", json={})
    assert response.status_code == 422
