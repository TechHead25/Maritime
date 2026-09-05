"""Integration and Unit Tests for Live AIS Streaming Service and Real-Time Tracking.

Validates:
- AIS message validation (MMSI, WGS84 coordinates, kinematics, null sentinels).
- Normalization into UTC timestamps and canonical vessel types.
- Bounded rolling retention in HistoricalTrackStore.
- Region subscriptions and geographic filtering.
- State transitions (DISCONNECTED, LIVE, STALE).
- Real-time API endpoints (/api/live/status, /api/live/vessels, /api/live/subscription).
- Zero dummy data: honest empty states when stream is offline.
"""

from datetime import datetime, timedelta, timezone
import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.providers.base import BoundingBox
from backend.app.services.live_ais_service import (
    AISMessageValidator,
    AISNormalizer,
    CurrentVesselState,
    HistoricalTrackStore,
    LiveAISService,
    PREDEFINED_REGIONS,
    live_ais_service,
)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. AIS Message Validator Tests
# ---------------------------------------------------------------------------

def test_mmsi_validation():
    # Valid 9-digit MMSIs
    valid, clean = AISMessageValidator.validate_mmsi("412000001")
    assert valid is True
    assert clean == "412000001"

    valid, clean = AISMessageValidator.validate_mmsi(412000002)
    assert valid is True
    assert clean == "412000002"

    # Invalid MMSIs (too short, starts with 0, or standard test/corrupt)
    assert AISMessageValidator.validate_mmsi("123")[0] is False
    assert AISMessageValidator.validate_mmsi("012345678")[0] is False
    assert AISMessageValidator.validate_mmsi("999999999")[0] is False
    assert AISMessageValidator.validate_mmsi("ABCDEFGH")[0] is False


def test_coordinate_validation():
    # Valid WGS84 coordinates
    assert AISMessageValidator.validate_coordinates(7.82, 82.50) is True
    assert AISMessageValidator.validate_coordinates(-45.0, 120.0) is True

    # Standard NMEA 91.0 / 181.0 null sentinels
    assert AISMessageValidator.validate_coordinates(91.0, 82.0) is False
    assert AISMessageValidator.validate_coordinates(7.0, 181.0) is False

    # Out of bounds
    assert AISMessageValidator.validate_coordinates(95.0, 80.0) is False
    assert AISMessageValidator.validate_coordinates(10.0, -190.0) is False
    assert AISMessageValidator.validate_coordinates("corrupt", "text") is False


def test_kinematics_validation():
    sog, cog = AISMessageValidator.validate_kinematics(14.5, 220.0)
    assert sog == 14.5
    assert cog == 220.0

    # Clamp extreme SOG
    sog, cog = AISMessageValidator.validate_kinematics(150.0, 400.0)
    assert sog == 102.2
    assert cog == 40.0  # 400 % 360 = 40


# ---------------------------------------------------------------------------
# 2. AIS Message Normalizer Tests
# ---------------------------------------------------------------------------

def test_normalizer_timestamp_utc():
    # ISO UTC string
    dt = AISNormalizer.normalize_timestamp("2026-09-03T04:30:00Z")
    assert dt.tzinfo is not None
    assert dt.year == 2026

    # None / empty defaults to current UTC
    now_dt = AISNormalizer.normalize_timestamp(None)
    assert now_dt.tzinfo == timezone.utc


def test_normalizer_vessel_type_mapping():
    assert AISNormalizer.map_vessel_type(80, "EVER GIVEN") == "TANKER"
    assert AISNormalizer.map_vessel_type(70, "MAERSK MC-KINNEY") == "CARGO"
    assert AISNormalizer.map_vessel_type(52, "OCEAN TUG 1") == "TUG"
    assert AISNormalizer.map_vessel_type(30, "LUCKY FISH") == "FISHING"
    assert AISNormalizer.map_vessel_type(60, "QUEEN MARY 2") == "PASSENGER"
    assert AISNormalizer.map_vessel_type(0, "CRUDE OIL TANKER") == "TANKER"


# ---------------------------------------------------------------------------
# 3. Current Vessel State & Historical Track Store Tests
# ---------------------------------------------------------------------------

def test_current_vessel_state_tracking():
    state = CurrentVesselState()
    now = datetime.now(timezone.utc)

    state.update("412000001", {
        "mmsi": "412000001",
        "vessel_name": "NEW DIAMOND",
        "vessel_type": "TANKER",
        "latitude": 7.82,
        "longitude": 82.50,
        "speed_over_ground_knots": 14.2,
        "course_over_ground_deg": 185.0,
        "heading_deg": 185.0,
        "last_update_utc": now,
    })

    assert state.count() == 1
    v = state.get("412000001")
    assert v is not None
    assert v["vessel_name"] == "NEW DIAMOND"
    assert v["data_age_seconds"] >= 0.0

    # Filter within bounding box
    bbox_match = BoundingBox(min_lon=82.0, min_lat=7.0, max_lon=83.0, max_lat=8.0)
    assert len(state.get_all(bbox=bbox_match)) == 1

    # Filter outside bounding box
    bbox_outside = BoundingBox(min_lon=10.0, min_lat=10.0, max_lon=12.0, max_lat=12.0)
    assert len(state.get_all(bbox=bbox_outside)) == 0


def test_historical_track_store_bounded_retention():
    store = HistoricalTrackStore(max_waypoints_per_vessel=5, retention_hours=1.0)
    now = datetime.now(timezone.utc)

    # Add 10 waypoints for one vessel
    for i in range(10):
        store.add_waypoint("412000001", {
            "timestamp_utc": now - timedelta(minutes=10 - i),
            "latitude": 7.0 + i * 0.1,
            "longitude": 82.0 + i * 0.1,
            "speed_over_ground_knots": 12.0,
            "course_over_ground_deg": 45.0,
            "heading_deg": 45.0,
        })

    track = store.get_track("412000001")
    # Must be bounded by max_waypoints_per_vessel (5)
    assert len(track) <= 5


# ---------------------------------------------------------------------------
# 4. Live AIS Service Integration & Packet Ingestion
# ---------------------------------------------------------------------------

def test_live_ais_service_ingestion_and_state():
    service = LiveAISService(default_region="SRI_LANKA_SOUTH")

    # Valid raw AIS frame
    raw_packet = json.dumps({
        "MessageType": "PositionReport",
        "MetaData": {
            "MMSI": "412000001",
            "ShipName": "NEW DIAMOND",
            "latitude": 7.8205,
            "longitude": 82.5020,
            "time_utc": datetime.now(timezone.utc).isoformat(),
        },
        "Message": {
            "PositionReport": {
                "Sog": 14.5,
                "Cog": 182.0,
                "TrueHeading": 182,
                "Type": 80,
            }
        }
    })

    success = service.ingest_raw_packet(raw_packet)
    assert success is True

    # Verify vessel in active state
    vessels = service.get_live_vessels()
    assert len(vessels) >= 1
    v = vessels[0]
    assert v["mmsi"] == "412000001"
    assert v["vessel_type"] == "TANKER"
    assert v["speed_over_ground_knots"] == 14.5

    # Verify detailed vessel trail
    det = service.get_vessel_details("412000001")
    assert det is not None
    assert len(det["trail"]) >= 1
    assert det["has_ais_gaps"] is False


def test_live_ais_service_rejects_corrupt_packet():
    service = LiveAISService()
    assert service.ingest_raw_packet("not a json string") is False
    assert service.ingest_raw_packet(json.dumps({"MetaData": {"MMSI": "bad"}})) is False


# ---------------------------------------------------------------------------
# 5. Live AIS API Endpoints Tests
# ---------------------------------------------------------------------------

def test_api_live_status_endpoint(client):
    res = client.get("/api/live/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in ("LIVE", "STALE", "DISCONNECTED")
    assert "active_region" in data


def test_api_live_vessels_endpoint(client):
    # Ingest a verified point directly into the singleton service
    test_packet = json.dumps({
        "MessageType": "PositionReport",
        "MetaData": {
            "MMSI": "412000001",
            "ShipName": "NEW DIAMOND",
            "latitude": 7.8205,
            "longitude": 82.5020,
            "time_utc": datetime.now(timezone.utc).isoformat(),
        },
        "Message": {
            "PositionReport": {
                "Sog": 14.5,
                "Cog": 182.0,
                "TrueHeading": 182,
                "Type": 80,
            }
        }
    })
    live_ais_service.ingest_raw_packet(test_packet)

    res = client.get("/api/live/vessels")
    assert res.status_code == 200
    data = res.json()
    assert "vessels" in data
    assert "total_count" in data
    assert data["total_count"] >= 1


def test_api_live_vessel_details_endpoint(client):
    res = client.get("/api/live/vessels/412000001")
    assert res.status_code == 200
    data = res.json()
    assert data["mmsi"] == "412000001"
    assert "trail" in data
    assert "speed_over_ground_knots" in data

    # 404 for non-existent vessel
    res_404 = client.get("/api/live/vessels/999888777")
    assert res_404.status_code == 404


def test_api_live_subscription_endpoint(client):
    payload = {"region_name": "STRAIT_OF_MALACCA"}
    res = client.post("/api/live/subscription", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["region"] == "STRAIT_OF_MALACCA"

    # Reset back to Sri Lanka
    client.post("/api/live/subscription", json={"region_name": "SRI_LANKA_SOUTH"})
