"""Unit and Integration tests for Data Provider Adapters and Registry."""

from datetime import datetime, timezone
import pytest

from backend.app.models.schemas import SARScene, VesselTrack
from backend.app.providers.base import (
    AISDataProvider,
    AISQuery,
    BoundingBox,
    EnvironmentalQuery,
    OceanCurrentProvider,
    SARDataProvider,
    SARQuery,
    WindDataProvider,
)
from backend.app.providers.factory import (
    ProviderMode,
    ProviderRegistry,
    default_provider_registry,
)
from backend.app.providers.synthetic import (
    SyntheticAISProvider,
    SyntheticOceanCurrentProvider,
    SyntheticSARProvider,
    SyntheticWindProvider,
)
from backend.app.services.sar_detector import SARRaster


@pytest.fixture
def sample_bbox():
    return BoundingBox(min_lon=101.5, min_lat=2.3, max_lon=102.5, max_lat=3.2)


@pytest.fixture
def sar_query(sample_bbox):
    return SARQuery(
        bbox=sample_bbox,
        start_time=datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc),
        satellite_platform="Sentinel-1A",
    )


@pytest.fixture
def ais_query(sample_bbox):
    return AISQuery(
        bbox=sample_bbox,
        start_time=datetime(2026, 8, 31, 18, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def env_query(sample_bbox):
    return EnvironmentalQuery(
        bbox=sample_bbox,
        start_time=datetime(2026, 8, 31, 18, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# 1. Synthetic SAR Provider Tests
# ---------------------------------------------------------------------------

def test_synthetic_sar_provider(sar_query):
    provider: SARDataProvider = SyntheticSARProvider()
    scenes = provider.search_scenes(sar_query)

    assert len(scenes) >= 1
    scene = scenes[0]
    assert isinstance(scene, SARScene)
    assert scene.satellite_platform == "Sentinel-1A (Synthetic SAR)"
    assert scene.acquisition_timestamp.tzinfo is not None

    raster = provider.fetch_raster(scene)
    assert isinstance(raster, SARRaster)
    assert raster.data_db.shape == (300, 300)


# ---------------------------------------------------------------------------
# 2. Synthetic AIS Provider Tests
# ---------------------------------------------------------------------------

def test_synthetic_ais_provider(ais_query):
    provider: AISDataProvider = SyntheticAISProvider()
    tracks = provider.fetch_vessel_tracks(ais_query)

    assert len(tracks) >= 1
    track = tracks[0]
    assert isinstance(track, VesselTrack)
    assert len(track.waypoints) >= 2
    assert track.mmsi is not None


# ---------------------------------------------------------------------------
# 3. Synthetic Ocean Current & Wind Provider Tests
# ---------------------------------------------------------------------------

def test_synthetic_ocean_current_provider(env_query):
    provider: OceanCurrentProvider = SyntheticOceanCurrentProvider()
    currents = provider.fetch_currents(env_query)

    assert "CMEMS" in currents["dataset_source"]
    assert currents["data_classification"] == "SYNTHETIC_DATA"
    assert "mean_u_velocity_mps" in currents
    assert "mean_v_velocity_mps" in currents


def test_synthetic_wind_provider(env_query):
    provider: WindDataProvider = SyntheticWindProvider()
    winds = provider.fetch_winds(env_query)

    assert "ERA5" in winds["dataset_source"]
    assert winds["data_classification"] == "SYNTHETIC_DATA"
    assert "mean_u_wind_mps" in winds
    assert "mean_v_wind_mps" in winds


# ---------------------------------------------------------------------------
# 4. Provider Registry and Factory Tests
# ---------------------------------------------------------------------------

def test_provider_registry_default_mode():
    registry = ProviderRegistry(mode=ProviderMode.SYNTHETIC)
    assert isinstance(registry.get_sar_provider(), SyntheticSARProvider)
    assert isinstance(registry.get_ais_provider(), SyntheticAISProvider)
    assert isinstance(registry.get_ocean_provider(), SyntheticOceanCurrentProvider)
    assert isinstance(registry.get_wind_provider(), SyntheticWindProvider)


def test_custom_provider_injection(sar_query):
    class CustomSARProvider(SARDataProvider):
        def search_scenes(self, query):
            return []

        def fetch_raster(self, scene):
            raise NotImplementedError()

    registry = ProviderRegistry()
    custom_sar = CustomSARProvider()
    registry.set_providers(sar=custom_sar)

    assert registry.get_sar_provider() == custom_sar
    assert registry.get_sar_provider().search_scenes(sar_query) == []
