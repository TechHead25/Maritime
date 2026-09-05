"""Comprehensive Integration and Unit Tests for Real Data Providers & Registry.

Validates compliance with GEMINI.md and user requirements:
- No silent synthetic fallback in production mode.
- Explicit ProviderUnavailableError when providers are unconfigured.
- Proper handling of authentication failures, timeouts, rate limits, and malformed responses.
- Accurate provenance recording on all external observations.
- Rejection of queries outside spatial/temporal coverage envelopes.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import os
import pytest
import requests
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import (
    SARScene,
    SlickPolygon,
    VesselPosition,
    VesselTrack,
)
from backend.app.providers.base import (
    BoundingBox,
    EnvironmentalQuery,
    NoSARObservationError,
    ProviderAuthenticationError,
    ProviderCoverageError,
    ProviderProvenance,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    SARQuery,
    AISQuery,
)
from backend.app.providers.copernicus_sar import CopernicusSARProvider
from backend.app.providers.live_ais import LiveAISWebSocketProvider
from backend.app.providers.copernicus_marine import CopernicusMarineCurrentProvider
from backend.app.providers.openmeteo_wind import OpenMeteoMarineWindProvider
from backend.app.providers.vessel_identity import MaritimeVesselIdentityAdapter
from backend.app.providers.registry import ProviderRegistry, provider_registry
from backend.app.providers.synthetic import (
    SyntheticAISProvider,
    SyntheticOceanCurrentProvider,
    SyntheticSARProvider,
    SyntheticWindProvider,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_bbox():
    return BoundingBox(min_lon=82.0, min_lat=7.0, max_lon=83.0, max_lat=8.0)


@pytest.fixture
def test_sar_query(test_bbox):
    return SARQuery(
        bbox=test_bbox,
        start_time=datetime(2020, 9, 2, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2020, 9, 3, 23, 59, tzinfo=timezone.utc),
        satellite_platform="Sentinel-1A",
        sensor_mode="IW",
        polarization="VV",
    )


@pytest.fixture
def test_env_query(test_bbox):
    return EnvironmentalQuery(
        bbox=test_bbox,
        start_time=datetime(2020, 9, 3, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2020, 9, 3, 12, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# 1. Production Mode Forbids Synthetic Fallback
# ---------------------------------------------------------------------------

def test_production_mode_strictly_forbids_synthetic_fallback(monkeypatch):
    """In production mode (ALLOW_SYNTHETIC_PROVIDERS=false), unconfigured providers must fail clearly."""
    monkeypatch.setenv("ALLOW_SYNTHETIC_PROVIDERS", "false")
    reg = ProviderRegistry()
    assert reg.allow_synthetic is False

    # Force providers to report unavailable
    monkeypatch.setattr(reg._historical_sar, "is_available", lambda: False)
    monkeypatch.setattr(reg._copernicus_sar, "is_available", lambda: False)

    with pytest.raises(ProviderUnavailableError) as exc:
        reg.get_sar_provider()
    assert "Data source unavailable" in str(exc.value)

    # Force AIS providers unavailable
    monkeypatch.setattr(reg._historical_ais, "is_available", lambda: False)
    monkeypatch.setattr(reg._live_ais, "is_available", lambda: False)

    with pytest.raises(ProviderUnavailableError) as exc_ais:
        reg.get_ais_provider()
    assert "Data source unavailable" in str(exc_ais.value)


def test_test_mode_permits_synthetic_providers(monkeypatch):
    """When explicitly authorized via ALLOW_SYNTHETIC_PROVIDERS=true, test registry can return synthetics."""
    monkeypatch.setenv("ALLOW_SYNTHETIC_PROVIDERS", "true")
    reg = ProviderRegistry()
    assert reg.allow_synthetic is True

    # When production sources are offline, falls back to synthetic in test mode only
    monkeypatch.setattr(reg._historical_sar, "is_available", lambda: False)
    monkeypatch.setattr(reg._copernicus_sar, "is_available", lambda: False)

    prov = reg.get_sar_provider()
    assert isinstance(prov, SyntheticSARProvider)


# ---------------------------------------------------------------------------
# 2. Live AIS Provider: Unconfigured State & Safety
# ---------------------------------------------------------------------------

def test_live_ais_unconfigured_behavior(monkeypatch, test_bbox):
    """If no AIS credentials are set, live provider reports unavailable and does not fabricate tracks."""
    monkeypatch.delenv("AISSTREAM_API_KEY", raising=False)
    monkeypatch.delenv("AIS_PROVIDER_KEY", raising=False)

    provider = LiveAISWebSocketProvider(api_key=None)
    assert provider.is_available() is False

    auth_status = provider.get_auth_status()
    assert auth_status["authenticated"] is False
    assert auth_status["status"] == "UNCONFIGURED"

    query = AISQuery(
        bbox=test_bbox,
        start_time=datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 9, 2, 0, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderUnavailableError):
        provider.fetch_vessel_tracks(query)


# ---------------------------------------------------------------------------
# 3. Authentication Failure Handling
# ---------------------------------------------------------------------------

def test_copernicus_sar_authentication_failure(test_sar_query):
    """Mocking an HTTP 401 from CDSE STAC must raise ProviderAuthenticationError."""
    provider = CopernicusSARProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized: Invalid or expired CDSE token."

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(ProviderAuthenticationError):
            provider.search_scenes(test_sar_query)


# ---------------------------------------------------------------------------
# 4. Timeout Handling
# ---------------------------------------------------------------------------

def test_copernicus_sar_timeout_handling(test_sar_query):
    """External request timeouts must be cleanly wrapped as ProviderTimeoutError."""
    provider = CopernicusSARProvider(timeout_seconds=0.1)

    with patch("requests.post", side_effect=requests.exceptions.Timeout("Read timed out")):
        with pytest.raises(ProviderTimeoutError):
            provider.search_scenes(test_sar_query)


# ---------------------------------------------------------------------------
# 5. Rate Limit Handling
# ---------------------------------------------------------------------------

def test_copernicus_sar_rate_limit_handling(test_sar_query):
    """HTTP 429 Too Many Requests must raise ProviderRateLimitError."""
    provider = CopernicusSARProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "Too many requests"

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(ProviderRateLimitError):
            provider.search_scenes(test_sar_query)


# ---------------------------------------------------------------------------
# 6. No SAR Observation & Missing Coverage Handling
# ---------------------------------------------------------------------------

def test_copernicus_sar_no_observation_found(test_sar_query):
    """When no scenes intersect the query, returns empty list or raises NoSARObservationError."""
    provider = CopernicusSARProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"features": []}

    with patch("requests.post", return_value=mock_resp):
        # Without raise_if_empty: returns empty list
        scenes = provider.search_scenes(test_sar_query, raise_if_empty=False)
        assert scenes == []

        # With raise_if_empty: raises NoSARObservationError
        with pytest.raises(NoSARObservationError):
            provider.search_scenes(test_sar_query, raise_if_empty=True)


def test_copernicus_sar_pre_mission_coverage_rejection(test_bbox):
    """Queries before Sentinel-1 operational epoch (April 2014) must be rejected."""
    provider = CopernicusSARProvider()
    pre_epoch_query = SARQuery(
        bbox=test_bbox,
        start_time=datetime(2010, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2010, 1, 2, tzinfo=timezone.utc),
    )
    with pytest.raises(ProviderCoverageError):
        provider.search_scenes(pre_epoch_query)


# ---------------------------------------------------------------------------
# 7. Ocean Current & Wind Provider Coverage and Provenance
# ---------------------------------------------------------------------------

def test_copernicus_marine_currents_provenance_and_coverage(test_env_query):
    """CMEMS provider delivers current vectors with verified provenance."""
    provider = CopernicusMarineCurrentProvider()
    data = provider.fetch_currents(test_env_query)

    assert "mean_u_velocity_mps" in data
    assert "mean_v_velocity_mps" in data
    assert "current_speed_knots" in data
    assert "provenance" in data

    prov = data["provenance"]
    assert prov["provider"] == provider.name
    assert "request_time_utc" in prov
    assert prov["resolution"] == "0.083 deg"


def test_openmeteo_wind_provenance_and_vector_conversion(test_env_query):
    """Wind provider calculates valid wind speeds, directions, and provenance."""
    provider = OpenMeteoMarineWindProvider()
    data = provider.fetch_winds(test_env_query)

    assert "wind_speed_mps" in data
    assert "wind_speed_knots" in data
    assert "wind_direction_deg" in data
    assert "mean_u_wind_mps" in data
    assert "mean_v_wind_mps" in data
    assert "provenance" in data

    prov = data["provenance"]
    assert prov["provider"] == provider.name


# ---------------------------------------------------------------------------
# 8. Vessel Identity Enrichment
# ---------------------------------------------------------------------------

def test_vessel_identity_lookup_and_provenance():
    """Vessel identity adapter correctly retrieves records by MMSI, IMO, and name with provenance."""
    adapter = MaritimeVesselIdentityAdapter()

    # Lookup by MMSI
    rec = adapter.lookup_by_mmsi("412000001")
    assert rec is not None
    assert rec["vessel_name"] == "NEW DIAMOND"
    assert rec["imo"] == "9191424"
    assert "provenance" in rec
    assert rec["provenance"]["provider"] == adapter.name

    # Lookup by IMO
    rec_imo = adapter.lookup_by_imo("9191424")
    assert rec_imo is not None
    assert rec_imo["mmsi"] == "412000001"

    # Lookup by Name substring
    matches = adapter.lookup_by_name("DIAMOND")
    assert len(matches) >= 1
    assert matches[0]["vessel_name"] == "NEW DIAMOND"

    # Non-existent vessel
    assert adapter.lookup_by_mmsi("999999999") is None


# ---------------------------------------------------------------------------
# 9. Provider Registry Health & API Endpoints
# ---------------------------------------------------------------------------

def test_provider_registry_health_summary():
    """Provider registry aggregates health from all registered providers."""
    summary = provider_registry.get_health_summary()

    assert "overall_status" in summary
    assert "providers" in summary
    assert "sar" in summary["providers"]
    assert "ais" in summary["providers"]
    assert "ocean_current" in summary["providers"]
    assert "wind" in summary["providers"]
    assert "vessel_identity" in summary["providers"]


def test_api_data_sources_endpoint(client):
    """GET /api/data-sources returns list of registered providers."""
    res = client.get("/api/data-sources")
    assert res.status_code == 200
    providers = res.json()
    assert isinstance(providers, list)
    assert len(providers) >= 4
    types = [p["provider_type"] for p in providers]
    assert "SAR" in types
    assert "AIS" in types
    assert "OCEAN_CURRENT" in types
    assert "WIND" in types


def test_api_data_sources_health_endpoint(client):
    """GET /api/data-sources/health returns health telemetry."""
    res = client.get("/api/data-sources/health")
    assert res.status_code == 200
    data = res.json()
    assert "overall_status" in data
    assert "providers" in data


def test_api_data_sources_coverage_endpoint(client):
    """GET /api/data-sources/{provider}/coverage tests spatiotemporal coverage."""
    res = client.get("/api/data-sources/sar/coverage?min_lon=80&min_lat=5&max_lon=85&max_lat=10")
    assert res.status_code == 200
    data = res.json()
    assert data["provider_type"] == "SAR"
    assert data["within_coverage"] is True


def test_api_sar_search_no_observation(client):
    """GET /api/sar/search returns 404 when no observation exists."""
    with patch("backend.app.providers.copernicus_sar.CopernicusSARProvider.search_scenes", side_effect=NoSARObservationError("No SAR observation available.")):
        res = client.get(
            "/api/sar/search?min_lon=82.0&min_lat=7.0&max_lon=83.0&max_lat=8.0&start_time_iso=2020-09-02T00:00:00Z&end_time_iso=2020-09-03T00:00:00Z"
        )
        assert res.status_code == 404
        assert "No SAR observation available" in res.json()["detail"]
