"""Tests for Automated Satellite Surveillance & Spill Detection Watcher Service.

Validates:
- Monitored sector catalog definition
- Lookalike rejection against low-wind calm zones
- On-demand surveillance scan cycle execution
- Automated case instantiation and drift pipeline trigger
- Status and alert tracking persistence
- REST API endpoints (/api/surveillance/status, alerts, scan-now)
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.satellite_watcher_service import (
    SatelliteWatcherService,
    MonitoredSector,
    SurveillanceAlert,
    DEFAULT_SECTORS,
)


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def isolated_watcher(tmp_path):
    """Provides a cleanly isolated watcher service using a temporary directory for alerts."""
    watcher = SatelliteWatcherService(scan_interval_seconds=9999)
    watcher.alerts_file = tmp_path / "test_alerts.json"
    watcher._alerts = []
    return watcher


def test_monitored_sectors_integrity():
    """Verify predefined surveillance sectors are configured with valid coordinates."""
    assert len(DEFAULT_SECTORS) >= 4
    for sector in DEFAULT_SECTORS:
        assert isinstance(sector.id, str) and len(sector.id) > 0
        assert isinstance(sector.name, str)
        min_lon, min_lat, max_lon, max_lat = sector.min_lon, sector.min_lat, sector.max_lon, sector.max_lat
        assert min_lon < max_lon
        assert min_lat < max_lat
        assert -180 <= min_lon <= 180
        assert -90 <= min_lat <= 90


def test_lookalike_wind_rejection(isolated_watcher):
    """Verify that low wind speeds (< 2.5 m/s) trigger lookalike natural calm rejection."""
    # Under 2.0 m/s wind -> calm natural slick lookalike
    is_rejected, reason = isolated_watcher._check_lookalike_rejection(
        mean_db=-24.5,
        contrast_ratio=7.5,
        wind_speed_ms=1.8,
    )
    assert is_rejected is True
    assert "low wind speed" in reason.lower()

    # Normal wind (6.5 m/s) with high contrast -> genuine mineral oil slick candidate
    is_rejected, reason = isolated_watcher._check_lookalike_rejection(
        mean_db=-25.0,
        contrast_ratio=8.0,
        wind_speed_ms=6.5,
    )
    assert is_rejected is False
    assert reason == ""


def test_scan_cycle_dry_run(isolated_watcher):
    """Verify that scan cycle runs across sectors without errors."""
    res = isolated_watcher.run_scan_cycle(sector_id="sri_lanka_south")
    assert res["status"] in ["COMPLETED", "SKIPPED"]
    assert res["sectors_scanned"] == 1
    assert "detections_found" in res
    assert "cases_created" in res


def test_api_surveillance_status(test_client):
    """Test GET /api/surveillance/status endpoint returns valid health & metrics."""
    response = test_client.get("/api/surveillance/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data
    assert "active_sectors" in data
    assert "total_alerts" in data
    assert "last_scan_utc" in data
    assert isinstance(data["active_sectors"], list)
    assert len(data["active_sectors"]) >= 4


def test_api_surveillance_alerts(test_client):
    """Test GET /api/surveillance/alerts returns valid alert list."""
    response = test_client.get("/api/surveillance/alerts?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_surveillance_scan_now(test_client):
    """Test POST /api/surveillance/scan-now endpoint triggers a synchronous sweep and produces real-time alerts."""
    response = test_client.post("/api/surveillance/scan-now", json={"sector_id": "ennore_chennai"})
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["COMPLETED", "SKIPPED"]
    assert data["sectors_scanned"] == 1
    if data["spills_detected"] > 0:
        alert = data["alerts"][0]
        assert "alert_id" in alert
        assert alert["sector_id"] == "ennore_chennai"
        assert "Operational" in alert["satellite_platform"]
        # Verify image endpoint serves valid PNG for auto-detected case
        case_id = alert["case_id"]
        img_resp = test_client.get(f"/api/cases/{case_id}/sar-image?view=diagnostics")
        assert img_resp.status_code == 200
        assert img_resp.headers["content-type"] == "image/png"


def test_sri_lanka_south_offshore_coordinate_verification(isolated_watcher):
    """Verify Sri Lanka south tanker sector is located strictly offshore and does not intersect land."""
    sector = isolated_watcher.sectors.get("sri_lanka_south")
    assert sector is not None
    # Sector must be situated south of Dondra Head (latitudes < 6.0 deg N in deep ocean)
    assert sector.max_lat <= 6.0
    assert sector.min_lat >= 5.0
    # Longitude corridor spans 80.0 to 82.5 deg E
    assert 80.0 <= sector.min_lon < sector.max_lon <= 83.0

    # Sector center should be deep ocean
    c_lon = (sector.min_lon + sector.max_lon) / 2.0
    c_lat = (sector.min_lat + sector.max_lat) / 2.0
    assert 5.2 <= c_lat <= 5.8
    assert 80.5 <= c_lon <= 82.0


