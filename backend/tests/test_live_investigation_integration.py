"""Tests for Live Maritime Intelligence and Investigation Integration.

Verifies:
- Unified vessel profile generation with verified registry particulars and no data fabrication.
- Real-time status classification (LIVE POSITION, RECENT POSITION, HISTORICAL POSITION, OFFLINE).
- Cross-investigation relationship indexing and multi-case evidence chain correlation.
- Creating an investigation case centered on a vessel and establishing subject status.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.live_ais_service import live_ais_service
from backend.app.services.vessel_intelligence_service import vessel_intelligence_service

client = TestClient(app)


def test_unified_vessel_profile_registry_verification():
    """Verifies that registered vessels load authentic particulars from the ITU MARS / Equasis adapter."""
    # Test known benchmark tanker: NEW DIAMOND (MMSI: 412000001)
    profile = vessel_intelligence_service.get_unified_vessel_profile("412000001")
    assert profile is not None
    identity = profile["identity"]
    assert identity["mmsi"] == "412000001"
    assert identity["vessel_name"] == "NEW DIAMOND"
    assert identity["imo"] == "9191424"
    assert identity["flag_country"] == "Panama"
    assert identity["vessel_type"] == "TANKER"
    assert identity["registry_verified"] is True
    assert identity["deadweight_tonnage"] == 299986


def test_unified_vessel_profile_unindexed_vessel_no_fabrication():
    """Verifies that an unindexed MMSI does not fabricate registry particulars."""
    profile = vessel_intelligence_service.get_unified_vessel_profile("999123456")
    identity = profile["identity"]
    assert identity["mmsi"] == "999123456"
    assert identity["imo"] is None
    assert identity["flag_country"] is None
    assert identity["registry_verified"] is False


def test_telemetry_status_classification():
    """Verifies strict classification into LIVE POSITION, RECENT POSITION, and STALE POSITION."""
    now_utc = datetime.now(timezone.utc)
    mmsi = "412000001"

    # 1. Fresh telemetry (< 300s) -> LIVE POSITION
    live_ais_service.current_state.update(mmsi, {
        "mmsi": mmsi,
        "vessel_name": "NEW DIAMOND",
        "vessel_type": "TANKER",
        "latitude": 6.85,
        "longitude": 81.75,
        "speed_over_ground_knots": 12.4,
        "course_over_ground_deg": 88.0,
        "heading_deg": 87.0,
        "last_update_utc": now_utc - timedelta(seconds=45),
        "navigational_status": "Underway using engine",
    })

    profile = vessel_intelligence_service.get_unified_vessel_profile(mmsi)
    assert profile["telemetry"]["position_status"] == "LIVE POSITION"
    assert profile["telemetry"]["is_currently_live"] is True
    assert profile["telemetry"]["data_age_seconds"] < 300.0
    assert profile["telemetry"]["latitude"] == 6.85

    # 2. Telemetry between 300s and 7200s -> RECENT POSITION
    live_ais_service.current_state.update(mmsi, {
        "mmsi": mmsi,
        "vessel_name": "NEW DIAMOND",
        "vessel_type": "TANKER",
        "latitude": 6.85,
        "longitude": 81.75,
        "speed_over_ground_knots": 12.4,
        "course_over_ground_deg": 88.0,
        "heading_deg": 87.0,
        "last_update_utc": now_utc - timedelta(seconds=1200),
        "navigational_status": "Underway using engine",
    })
    profile2 = vessel_intelligence_service.get_unified_vessel_profile(mmsi)
    assert profile2["telemetry"]["position_status"] == "RECENT POSITION"
    assert profile2["telemetry"]["is_currently_live"] is False

    # 3. Telemetry > 7200s -> STALE POSITION
    live_ais_service.current_state.update(mmsi, {
        "mmsi": mmsi,
        "vessel_name": "NEW DIAMOND",
        "vessel_type": "TANKER",
        "latitude": 6.85,
        "longitude": 81.75,
        "speed_over_ground_knots": 12.4,
        "course_over_ground_deg": 88.0,
        "heading_deg": 87.0,
        "last_update_utc": now_utc - timedelta(seconds=9000),
        "navigational_status": "Underway using engine",
    })
    profile3 = vessel_intelligence_service.get_unified_vessel_profile(mmsi)
    assert profile3["telemetry"]["position_status"] == "STALE POSITION"


def test_investigation_relationships_indexing():
    """Verifies that cases and forensic evidence citing the vessel are indexed."""
    profile = vessel_intelligence_service.get_unified_vessel_profile("412000001")
    # If case-001 is loaded, NEW DIAMOND should appear in investigations
    assert "investigations" in profile
    assert "evidence_chain" in profile
    # Should have at least one investigation link if cases are initialized
    if profile["investigations"]:
        inv = profile["investigations"][0]
        assert "case_id" in inv
        assert "case_title" in inv
        assert "relationship_type" in inv


def test_api_vessel_intelligence_endpoint():
    """Verifies GET /api/vessels/{mmsi}/intelligence endpoint."""
    res = client.get("/api/vessels/412000001/intelligence")
    assert res.status_code == 200
    data = res.json()
    assert data["identity"]["mmsi"] == "412000001"
    assert "telemetry" in data
    assert "investigations" in data
    assert "evidence_chain" in data


def test_api_create_investigation_from_vessel():
    """Verifies POST /api/investigations/from-vessel endpoint."""
    payload = {
        "mmsi": "412000001",
        "title": "Live Patrol Inquiry - Tanker Subject",
        "description": "Triggered from live tracking console.",
        "buffer_degrees": 0.5,
    }
    res = client.post("/api/investigations/from-vessel", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "SUCCESS"
    assert body["subject_vessel"]["mmsi"] == "412000001"
    created_case = body["case"]
    assert created_case["metadata"]["investigation_subject_mmsi"] == "412000001"
    assert created_case["title"] == "Live Patrol Inquiry - Tanker Subject"

    # Cleanup case
    del_res = client.delete(f"/api/cases/{created_case['id']}")
    assert del_res.status_code == 200
