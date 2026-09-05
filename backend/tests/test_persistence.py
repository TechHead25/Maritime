"""Unit and Integration Tests for Durable Local Persistence of Investigation Runs (Task 4)."""

from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import CaseStatus
from backend.app.services.case_service import CaseService, case_service
from backend.app.services.persistence_service import PersistenceService, persistence_service

client = TestClient(app)


def test_atomic_persistence_and_api_retrieval(tmp_path):
    """Verifies that running an investigation writes artifacts to disk and GET returns it."""
    sample_ais_csv = (
        "mmsi,vessel_name,timestamp,latitude,longitude,sog,cog,nav_status\n"
        "538009912,PERSISTENCE TANKER,2026-09-02T02:00:00Z,7.70,82.60,14.0,45.0,Under way using engine\n"
        "538009912,PERSISTENCE TANKER,2026-09-02T04:00:00Z,7.80,82.75,0.8,48.0,Not under command\n"
        "538009912,PERSISTENCE TANKER,2026-09-02T06:00:00Z,7.90,82.90,12.0,50.0,Under way using engine\n"
    )

    # 1. Create a dynamic test case
    create_res = client.post(
        "/api/cases/create-investigation",
        data={
            "title": "Persistence Test Case",
            "incident_timestamp": "2026-09-02T06:00:00Z",
            "min_lon": "82.0",
            "min_lat": "7.0",
            "max_lon": "84.0",
            "max_lat": "9.0",
        },
        files={
            "ais_file": ("test_ais_feed.csv", io.BytesIO(sample_ais_csv.encode("utf-8")), "text/csv"),
        }
    )
    assert create_res.status_code == 201
    case_id = create_res.json()["id"]

    # 2. Execute investigation pipeline
    pipeline_res = client.post(
        f"/api/cases/{case_id}/investigate",
        json={
            "time_step_minutes": 30,
            "max_hours_backward": 24.0,
            "estimated_release_hours_ago": 9.0,
            "particle_count": 200,
            "random_seed": 42,
            "use_synthetic_slick": True,
        }
    )
    assert pipeline_res.status_code == 200
    original_result = pipeline_res.json()

    # 3. Verify disk artifacts
    case_dir = Path("data/cases") / case_id
    assert (case_dir / "investigation_result.json").exists()
    assert (case_dir / "investigation_config.json").exists()
    assert (case_dir / "provenance.json").exists()
    assert (case_dir / "outputs" / "investigation_result.json").exists()
    assert (case_dir / "reports").is_dir()

    # 4. Verify provenance content
    with open(case_dir / "provenance.json", "r", encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["case_id"] == case_id
    assert prov["status"] == "PERSISTENCE_VERIFIED"
    assert "sar_detector" in prov["engine_components"]

    # 5. Verify GET /api/cases/{case_id}/investigation endpoint
    get_res = client.get(f"/api/cases/{case_id}/investigation")
    assert get_res.status_code == 200
    persisted_payload = get_res.json()
    assert persisted_payload["case"]["id"] == case_id
    assert len(persisted_payload["attribution_scores"]) == len(original_result["attribution_scores"])
    assert persisted_payload["attribution_scores"][0]["rank"] == 1

    # 6. Simulate Backend Restart (Create completely new CaseService instance)
    fresh_service = CaseService(data_dir=Path("data/cases"))
    fresh_details = fresh_service.get_case_details(case_id)
    assert fresh_details is not None
    assert fresh_details["case"].status == CaseStatus.ATTRIBUTION_COMPLETED
    assert len(fresh_details["probability_clouds"]) >= 5
    assert len(fresh_details["candidates"]) >= 1
    assert len(fresh_details["attribution_scores"]) >= 1
    assert fresh_details["attribution_scores"][0].rank == 1


def test_corrupted_result_file_graceful_fallback(tmp_path):
    """Verifies that a corrupted or malformed investigation_result.json does not crash the system."""
    # 1. Create a dynamic test case
    create_res = client.post(
        "/api/cases/create-investigation",
        data={
            "title": "Corrupt File Test Case",
            "incident_timestamp": "2026-09-02T06:00:00Z",
            "min_lon": "82.0",
            "min_lat": "7.0",
            "max_lon": "84.0",
            "max_lat": "9.0",
        }
    )
    assert create_res.status_code == 201
    case_id = create_res.json()["id"]

    # 2. Write invalid corrupted JSON
    case_dir = Path("data/cases") / case_id
    with open(case_dir / "investigation_result.json", "w", encoding="utf-8") as f:
        f.write("{ INVALID MALFORMED JSON !!! ")

    # 3. Reload service - must handle gracefully without raising exception
    fresh_service = CaseService(data_dir=Path("data/cases"))
    loaded_case = fresh_service.get_case(case_id)
    assert loaded_case is not None
    # Investigation result should be empty/None
    assert fresh_service.get_investigation_result(case_id) is None


def test_get_investigation_not_found():
    """Verifies 404 is returned when querying a case with no completed investigation."""
    create_res = client.post(
        "/api/cases/create-investigation",
        data={
            "title": "Unanalyzed Case",
            "incident_timestamp": "2026-09-02T06:00:00Z",
            "min_lon": "82.0",
            "min_lat": "7.0",
            "max_lon": "84.0",
            "max_lat": "9.0",
        }
    )
    assert create_res.status_code == 201
    case_id = create_res.json()["id"]

    get_res = client.get(f"/api/cases/{case_id}/investigation")
    assert get_res.status_code == 404
    assert "No completed investigation result found" in get_res.json()["detail"]
