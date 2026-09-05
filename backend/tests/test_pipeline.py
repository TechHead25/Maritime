"""Integration and End-to-End tests for the Complete Forensic Investigation Pipeline with SAR Detection."""

from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app
from backend.app.services.case_service import case_service

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Full Pipeline Execution with Live SAR Detector (Default)
# ---------------------------------------------------------------------------

def test_run_full_investigation_pipeline_with_sar_detection():
    payload = {
        "time_step_minutes": 30,
        "max_hours_backward": 24.0,
        "particle_count": 500,
        "random_seed": 42,
        "estimated_release_hours_ago": 14.0,
        "release_window_half_width_hours": 2.0,
        "use_synthetic_slick": False,
    }

    response = client.post("/api/cases/demo-case-001/investigate", json=payload)
    assert response.status_code == 200
    data = response.json()

    # 1. Case Info
    assert data["case"]["id"] == "demo-case-001"
    assert data["case"]["status"] == "ATTRIBUTION_COMPLETED"

    # 2. Live SAR Detection Slick Info
    assert len(data["slicks"]) > 0
    slick = data["slicks"][0]
    assert slick["area_sq_km"] > 1.0
    assert slick["confidence_score"] >= 0.60
    assert len(slick["slick_polygon"]["coordinates"][0]) >= 4

    # 3. Drift & Origin Info
    assert len(data["drift_simulations"]) > 0
    assert len(data["probability_clouds"]) == 49
    origin = data["origin_centroid"]["coordinates"]
    assert abs(origin[0] - 101.83) < 0.35
    assert abs(origin[1] - 2.61) < 0.35
    assert data["origin_uncertainty_radius_km"] > 0.0

    # 4. Release Window
    assert len(data["release_windows"]) > 0

    # 5. Candidate Vessels
    assert len(data["candidate_vessels"]) >= 3

    # 6. Attribution Scores & Rankings (Vessel A rank 1)
    scores = data["attribution_scores"]
    assert len(scores) >= 3
    top = scores[0]
    assert top["rank"] == 1
    assert top["candidate_name"] == "MT PACIFIC GLORY"
    assert top["mmsi"] == "538009912"
    assert top["total_score"] >= 50.0

    # 7. Evidence Items
    assert len(top["evidence_items"]) >= 4

    # 8. Forensic Summary Verdict Phrasing
    assert "highest-ranked candidate based on the available" in data["summary_verdict"]
    assert "MT PACIFIC GLORY" in data["summary_verdict"]

    # 9. Data Sources Lineage
    assert data["data_sources"]["data_classification"] == "SYNTHETIC_DATA"
    assert "SAR Dark-Patch" in data["data_sources"]["detection_method"]


# ---------------------------------------------------------------------------
# 2. Synthetic Fixture Pipeline Execution Mode
# ---------------------------------------------------------------------------

def test_run_pipeline_with_synthetic_fixture():
    payload = {
        "time_step_minutes": 30,
        "max_hours_backward": 24.0,
        "particle_count": 500,
        "random_seed": 42,
        "estimated_release_hours_ago": 14.0,
        "release_window_half_width_hours": 2.0,
        "use_synthetic_slick": True,
    }

    response = client.post("/api/cases/demo-case-001/investigate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["data_sources"]["detection_method"] == "Synthetic Slick Fixture"
    assert data["attribution_scores"][0]["candidate_name"] == "MT PACIFIC GLORY"


# ---------------------------------------------------------------------------
# 3. Determinism Test
# ---------------------------------------------------------------------------

def test_full_pipeline_determinism():
    payload = {
        "time_step_minutes": 30,
        "max_hours_backward": 12.0,
        "particle_count": 300,
        "random_seed": 77
    }

    res1 = client.post("/api/cases/demo-case-001/investigate", json=payload).json()
    res2 = client.post("/api/cases/demo-case-001/investigate", json=payload).json()

    # Exact equality of origin and scores
    assert res1["origin_centroid"]["coordinates"] == res2["origin_centroid"]["coordinates"]
    assert res1["attribution_scores"][0]["total_score"] == res2["attribution_scores"][0]["total_score"]
    assert res1["attribution_scores"][0]["candidate_name"] == res2["attribution_scores"][0]["candidate_name"]


# ---------------------------------------------------------------------------
# 4. Error Handling: SAR Detection Failure
# ---------------------------------------------------------------------------

def test_pipeline_sar_detection_failure_returns_meaningful_error():
    # Mock SAR detector to simulate failure (no candidates detected)
    with patch("backend.app.services.pipeline_service.sar_detector.detect_primary_slick") as mock_detect:
        mock_detect.side_effect = ValueError("No mineral oil slicks verified in SAR scene. All candidates were classified as low-wind lookalikes.")

        response = client.post(
            "/api/cases/demo-case-001/investigate",
            json={"use_synthetic_slick": False}
        )

        assert response.status_code in [400, 404, 500]
        detail = response.json()["detail"]
        assert "SAR Detection Subsystem failed" in detail
        assert "lookalikes" in detail


def test_pipeline_case_not_found():
    response = client.post("/api/cases/unknown-case-id-12345/investigate", json={})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_pipeline_validation_error():
    # Invalid particle count < 10
    response = client.post("/api/cases/demo-case-001/investigate", json={"particle_count": 2})
    assert response.status_code == 422
