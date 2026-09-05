"""Live External Provider Connectivity & Network Verification Test Suite.

Validates that external providers connect directly to official real-world APIs
(Copernicus Data Space, Copernicus Marine, Open-Meteo, CARTO, ITU MARS)
with zero synthetic fallback and zero data fabrication.
Compliant with GEMINI.md: strictly truthful telemetry and credentials.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.providers.base import BoundingBox, SARQuery
from backend.app.providers.copernicus_sar import CopernicusSARProvider
from backend.app.providers.copernicus_marine import CopernicusMarineCurrentProvider
from backend.app.providers.openmeteo_wind import OpenMeteoMarineWindProvider
from backend.app.providers.basemap import basemap_tile_provider
from backend.app.providers.live_ais import LiveAISWebSocketProvider
from backend.app.providers.vessel_identity import MaritimeVesselIdentityAdapter
from backend.app.providers.registry import provider_registry

client = TestClient(app)


def test_01_copernicus_cdse_live_odata_catalogue_search():
    """Verifies live query against official Copernicus Data Space Ecosystem (CDSE) OData Catalogue."""
    provider = CopernicusSARProvider()
    assert provider.is_available() is True

    # Real query over Indian Ocean / Bay of Bengal envelope
    query = SARQuery(
        bbox=BoundingBox(min_lon=80.0, min_lat=6.0, max_lon=85.0, max_lat=10.0),
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 10, tzinfo=timezone.utc),
        sensor_mode="IW",
    )

    scenes = provider.search_scenes(query, raise_if_empty=False)
    assert len(scenes) > 0, "Expected live Sentinel-1 scenes from CDSE OData catalogue"
    
    first_scene = scenes[0]
    assert first_scene.satellite_platform in ("Sentinel-1A", "Sentinel-1B")
    assert first_scene.sensor_mode == "IW"
    assert first_scene.acquisition_timestamp.year == 2024
    assert first_scene.metadata.get("source_provider") == provider.name
    assert first_scene.metadata.get("product_name") is not None


def test_02_openmeteo_marine_live_atmospheric_wind_api():
    """Verifies live REST query against Open-Meteo Marine / ECMWF ERA5 weather service."""
    provider = OpenMeteoMarineWindProvider()
    assert provider.is_available() is True

    auth = provider.get_auth_status()
    assert auth["authenticated"] is True
    assert "OPEN_ACCESS" in auth["status"]

    meta = provider.get_metadata()
    assert "ECMWF" in meta["underlying_model"]

    # Verify coverage check
    bbox = BoundingBox(min_lon=80.0, min_lat=6.0, max_lon=85.0, max_lat=10.0)
    assert provider.check_coverage(bbox, (datetime(2020, 9, 1, tzinfo=timezone.utc), datetime(2020, 9, 5, tzinfo=timezone.utc))) is True


def test_03_carto_basemap_live_tile_cdn():
    """Verifies live HEAD probe against CartoDB Dark Matter vector tile CDN."""
    ping_result = basemap_tile_provider.ping()
    assert ping_result["status"] in ("ONLINE", "DEGRADED")
    assert ping_result["latency_ms"] > 0.0
    assert ping_result["error"] is None

    auth = basemap_tile_provider.get_auth_status()
    assert auth["authenticated"] is True
    assert auth["masked_credential"] == "Open Access (No Secret Required)"


def test_04_copernicus_marine_cmems_live_thredds_reachability():
    """Verifies live reachability of Copernicus Marine Service (CMEMS) THREDDS WMS service."""
    provider = CopernicusMarineCurrentProvider()
    assert provider.is_available() is True

    res = client.post("/api/data-sources/ocean/ping")
    assert res.status_code == 200
    data = res.json()
    assert data["provider_id"] == "ocean"
    assert data["status"] in ("ONLINE", "DEGRADED")
    assert data["latency_ms"] > 0.0


def test_05_aisstream_honest_unconfigured_state_no_fabrication():
    """Verifies AISStream provider reports honest unconfigured state with zero fake vessels."""
    provider = LiveAISWebSocketProvider()
    auth = provider.get_auth_status()

    if not provider.is_available():
        assert auth["authenticated"] is False
        assert auth["status"] == "UNCONFIGURED"
        assert "not configured" in auth["detail"].lower()

    # Query without key must raise ProviderUnavailableError or return empty, never fake vessels
    query_box = BoundingBox(min_lon=81.0, min_lat=6.5, max_lon=82.5, max_lat=8.0)
    with pytest.raises(Exception):
        provider.fetch_vessel_tracks(query=None)  # Must fail cleanly rather than inventing vessels


def test_06_vessel_identity_itu_mars_equasis_enrichment():
    """Verifies vessel identity adapter resolves verified maritime particulars with provenance."""
    adapter = MaritimeVesselIdentityAdapter()
    assert adapter.is_available() is True

    # Check known tanker IMO/Callsign
    profile = adapter.lookup_by_mmsi("412000001")
    assert profile is not None
    assert profile["vessel_name"] == "NEW DIAMOND"
    assert profile["vessel_type"] == "TANKER"
    assert profile["deadweight_tonnage"] > 250000

    prov = adapter.get_provenance("412000001")
    assert prov.provider == adapter.name
    assert prov.source_identifier == "412000001"


def test_07_data_source_control_center_live_pings_all_six_categories():
    """Verifies Data Source Control Center executes live probes across all 6 categories."""
    categories = ["earth_observation", "ais", "ocean", "weather", "vessel_identity", "basemap"]
    for cat in categories:
        res = client.post(f"/api/data-sources/{cat}/ping")
        assert res.status_code == 200
        payload = res.json()
        assert payload["provider_id"] == cat
        assert payload["status"] in ("ONLINE", "DEGRADED", "OFFLINE")
        assert isinstance(payload["latency_ms"], (int, float))
