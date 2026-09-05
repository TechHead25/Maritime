"""Unit and Integration Tests for Dynamic Case Creation & File Ingestion (Task 3)."""

from datetime import datetime, timezone
import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import CaseStatus, InvestigationCase
from backend.app.services.case_service import case_service
from backend.app.services.case_creation_service import (
    CaseCreationService,
    sanitize_filename,
    MAX_FILE_SIZE_BYTES,
)

client = TestClient(app)


def test_sanitize_filename():
    """Verifies prevention of path traversal and illegal characters."""
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("malicious:file*name?.csv") == "malicious_file_name_.csv"
    assert sanitize_filename(".hidden") != ".hidden"


def test_create_investigation_api_success(tmp_path):
    """Verifies creating a new dynamic case via POST /api/cases/create-investigation."""
    sample_ais_csv = (
        "mmsi,vessel_name,timestamp,latitude,longitude,sog,cog,nav_status\n"
        "538009912,DYNAMIC TANKER,2026-09-02T02:00:00Z,7.70,82.60,14.0,45.0,Under way using engine\n"
        "538009912,DYNAMIC TANKER,2026-09-02T04:00:00Z,7.80,82.75,0.8,48.0,Not under command\n"
        "538009912,DYNAMIC TANKER,2026-09-02T06:00:00Z,7.90,82.90,12.0,50.0,Under way using engine\n"
    )

    response = client.post(
        "/api/cases/create-investigation",
        data={
            "title": "Automated Dynamic Test Case",
            "description": "Integration test dynamic case",
            "incident_timestamp": "2026-09-02T05:00:00Z",
            "min_lon": "80.0",
            "min_lat": "5.0",
            "max_lon": "85.0",
            "max_lat": "10.0",
        },
        files={
            "ais_file": ("test_ais_feed.csv", io.BytesIO(sample_ais_csv.encode("utf-8")), "text/csv"),
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "Automated Dynamic Test Case"
    assert data["status"] == "CREATED"

    created_id = data["id"]

    # Verify case details are accessible immediately
    detail_res = client.get(f"/api/cases/{created_id}")
    assert detail_res.status_code == 200
    details = detail_res.json()
    assert len(details["vessel_tracks"]) >= 1
    assert details["vessel_tracks"][0]["vessel_name"] == "DYNAMIC TANKER"


def test_create_investigation_validation_error_inverted_coordinates():
    """Verifies that invalid or inverted coordinates return 400 Bad Request."""
    response = client.post(
        "/api/cases/create-investigation",
        data={
            "title": "Invalid Coordinates Case",
            "min_lon": "85.0",
            "min_lat": "10.0",
            "max_lon": "80.0",  # min > max
            "max_lat": "5.0",
        }
    )
    assert response.status_code == 400
    assert "Invalid bounding box" in response.json()["detail"]


def test_create_investigation_unsupported_file_extension():
    """Verifies that executable or disallowed extensions are blocked."""
    response = client.post(
        "/api/cases/create-investigation",
        data={
            "title": "Malicious Extension Case",
            "min_lon": "80.0",
            "min_lat": "5.0",
            "max_lon": "85.0",
            "max_lat": "10.0",
        },
        files={
            "ais_file": ("malicious_script.exe", io.BytesIO(b"MZ..."), "application/octet-stream")
        }
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_run_pipeline_on_newly_created_dynamic_case():
    """Verifies that the complete forensic pipeline runs end-to-end on a user-created case."""
    sample_ais_csv = (
        "mmsi,vessel_name,timestamp,latitude,longitude,sog,cog,nav_status\n"
        "538009912,DYNAMIC TANKER,2026-09-02T02:00:00Z,7.70,82.60,14.0,45.0,Under way using engine\n"
        "538009912,DYNAMIC TANKER,2026-09-02T04:00:00Z,7.80,82.75,0.8,48.0,Not under command\n"
        "538009912,DYNAMIC TANKER,2026-09-02T06:00:00Z,7.90,82.90,12.0,50.0,Under way using engine\n"
    )

    # 1. Create dynamic case
    create_res = client.post(
        "/api/cases/create-investigation",
        data={
            "title": "E2E Dynamic Investigation Pipeline Case",
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

    # 2. Run pipeline
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
    res_data = pipeline_res.json()
    assert res_data["case"]["status"] == "ATTRIBUTION_COMPLETED"
    assert len(res_data["probability_clouds"]) >= 5
    assert len(res_data["candidate_vessels"]) >= 1
    assert len(res_data["attribution_scores"]) >= 1
    assert res_data["attribution_scores"][0]["rank"] == 1
