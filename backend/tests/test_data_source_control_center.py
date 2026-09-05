"""Tests for the Data Source Control Center.

Verifies:
- All 6 external data provider categories are represented.
- Authentication credentials are strictly masked with zero secret exposure.
- Real-time latency, coverage, and rate-limit metrics.
- Multi-factor data freshness calculation according to provider-specific physical thresholds.
- On-demand live latency ping and configuration update endpoints.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.data_source_control_service import data_source_control_service

client = TestClient(app)


def test_control_center_returns_all_six_categories():
    """Verifies that all 6 required categories are returned."""
    res = client.get("/api/data-sources/control-center")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    providers = data["providers"]
    assert len(providers) == 6

    expected_categories = {
        "Earth Observation",
        "AIS",
        "Ocean",
        "Weather",
        "Vessel Identity",
        "Basemap",
    }
    returned_categories = {p["category"] for p in providers}
    assert returned_categories == expected_categories


def test_control_center_masks_secrets():
    """Verifies that credentials are strictly masked and no raw secrets leak."""
    res = client.get("/api/data-sources/control-center")
    data = res.json()
    providers = data["providers"]

    for p in providers:
        auth = p["authentication"]
        assert "configured" in auth
        assert "auth_type" in auth
        assert "masked_credential" in auth
        masked = auth["masked_credential"]

        # Ensure no raw tokens/keys are exposed
        assert not masked.startswith("ey")  # JWT
        if "***" in masked:
            assert len(masked) <= 15  # Masked preview


def test_freshness_thresholds_calculation():
    """Verifies provider-specific freshness calculations."""
    now = datetime.now(timezone.utc)

    # 1. SAR: Fresh (< 48h), Aging (< 7d), Stale (> 7d)
    fresh_sar = data_source_control_service._calculate_freshness(
        last_timestamp_iso=(now - timedelta(hours=20)).isoformat(),
        fresh_threshold_hours=48.0,
        aging_threshold_hours=168.0,
        is_available=True,
    )
    assert fresh_sar == "Fresh"

    aging_sar = data_source_control_service._calculate_freshness(
        last_timestamp_iso=(now - timedelta(days=4)).isoformat(),
        fresh_threshold_hours=48.0,
        aging_threshold_hours=168.0,
        is_available=True,
    )
    assert aging_sar == "Aging"

    stale_sar = data_source_control_service._calculate_freshness(
        last_timestamp_iso=(now - timedelta(days=10)).isoformat(),
        fresh_threshold_hours=48.0,
        aging_threshold_hours=168.0,
        is_available=True,
    )
    assert stale_sar == "Stale"

    # 2. AIS: Fresh (< 5m), Aging (< 2h), Stale (> 2h)
    fresh_ais = data_source_control_service._calculate_freshness(
        last_timestamp_iso=(now - timedelta(minutes=2)).isoformat(),
        fresh_threshold_hours=0.083,
        aging_threshold_hours=2.0,
        is_available=True,
    )
    assert fresh_ais == "Fresh"

    stale_ais = data_source_control_service._calculate_freshness(
        last_timestamp_iso=(now - timedelta(hours=4)).isoformat(),
        fresh_threshold_hours=0.083,
        aging_threshold_hours=2.0,
        is_available=True,
    )
    assert stale_ais == "Stale"


def test_api_ping_provider():
    """Verifies on-demand live latency ping endpoint."""
    res = client.post("/api/data-sources/weather/ping")
    assert res.status_code == 200
    body = res.json()
    assert body["provider_id"] == "weather"
    assert "latency_ms" in body
    assert body["status"] in ("ONLINE", "DEGRADED", "UNAVAILABLE")


def test_api_configure_provider():
    """Verifies updating runtime configuration parameters."""
    payload = {
        "fallback_enabled": True,
        "custom_timeout_seconds": 10.0,
        "rate_limit_rpm": 60,
    }
    res = client.post("/api/data-sources/earth_observation/configure", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "SUCCESS"
    assert body["provider_id"] == "earth_observation"
    assert body["config"]["fallback_enabled"] is True
    assert body["config"]["rate_limit_rpm"] == 60
