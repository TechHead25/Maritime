"""Unit and Integration tests for Historical Ocean Current & Wind Adapters."""

from datetime import datetime, timezone
import pytest

from backend.app.providers.base import BoundingBox, EnvironmentalQuery
from backend.app.providers.ocean_adapter import HistoricalOceanCurrentAdapter
from backend.app.providers.wind_adapter import HistoricalWindAdapter
from backend.app.providers.synthetic import (
    SyntheticOceanCurrentProvider,
    SyntheticWindProvider,
)
from backend.app.utils.validate_environmental_datasets import audit_environmental_dataset


@pytest.fixture
def valid_env_query():
    """Query completely inside MT New Diamond dataset coverage (81.5-84.5E, 6.5-9.0N, Sept 2-4 2020)."""
    return EnvironmentalQuery(
        bbox=BoundingBox(min_lon=82.0, min_lat=7.0, max_lon=83.5, max_lat=8.5),
        start_time=datetime(2020, 9, 2, 12, 0, tzinfo=timezone.utc),
        end_time=datetime(2020, 9, 3, 18, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# 1. Historical Ocean Current Adapter Tests (CMEMS)
# ---------------------------------------------------------------------------

def test_historical_ocean_current_adapter_success(valid_env_query):
    adapter = HistoricalOceanCurrentAdapter()
    result = adapter.fetch_currents(valid_env_query)

    assert "CMEMS" in result["dataset_source"]
    assert result["data_classification"] == "OBSERVED_HISTORICAL_REANALYSIS"
    assert "mean_current_vectors" in result

    vec = result["mean_current_vectors"]
    assert 0.20 <= vec["u_eastward_m_per_s"] <= 0.35
    assert 0.15 <= vec["v_northward_m_per_s"] <= 0.30
    assert vec["speed_m_per_s"] > 0.0
    assert 40.0 <= vec["direction_deg"] <= 60.0
    assert "Inverse Distance" in result["interpolation_metadata"]["method"]


def test_historical_ocean_current_spatial_out_of_bounds():
    adapter = HistoricalOceanCurrentAdapter()
    # Query extends far west into Arabian Sea outside 81.5E dataset bounds
    invalid_query = EnvironmentalQuery(
        bbox=BoundingBox(min_lon=70.0, min_lat=7.0, max_lon=75.0, max_lat=8.5),
        start_time=datetime(2020, 9, 2, 12, 0, tzinfo=timezone.utc),
        end_time=datetime(2020, 9, 3, 18, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError) as excinfo:
        adapter.fetch_currents(invalid_query)
    assert "Spatial coverage error" in str(excinfo.value)
    assert "extends outside CMEMS dataset coverage" in str(excinfo.value)


def test_historical_ocean_current_temporal_out_of_bounds():
    adapter = HistoricalOceanCurrentAdapter()
    # Query extends to October 2020 outside Sept 2-4 2020 dataset window
    invalid_query = EnvironmentalQuery(
        bbox=BoundingBox(min_lon=82.0, min_lat=7.0, max_lon=83.5, max_lat=8.5),
        start_time=datetime(2020, 10, 1, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2020, 10, 2, 0, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError) as excinfo:
        adapter.fetch_currents(invalid_query)
    assert "Temporal coverage error" in str(excinfo.value)
    assert "extends outside CMEMS dataset coverage" in str(excinfo.value)


# ---------------------------------------------------------------------------
# 2. Historical Surface Wind Adapter Tests (ERA5)
# ---------------------------------------------------------------------------

def test_historical_wind_adapter_success(valid_env_query):
    adapter = HistoricalWindAdapter()
    result = adapter.fetch_winds(valid_env_query)

    assert "ERA5" in result["dataset_source"]
    assert result["data_classification"] == "OBSERVED_HISTORICAL_REANALYSIS"
    assert "mean_wind_vectors" in result

    vec = result["mean_wind_vectors"]
    assert 3.5 <= vec["u_eastward_m_per_s"] <= 4.5
    assert 4.0 <= vec["v_northward_m_per_s"] <= 5.5
    assert vec["wind_speed_m_per_s"] > 5.0
    # Southwest monsoon blows from ~215-230 deg
    assert 210.0 <= vec["wind_direction_from_deg"] <= 235.0


def test_historical_wind_spatial_out_of_bounds():
    adapter = HistoricalWindAdapter()
    invalid_query = EnvironmentalQuery(
        bbox=BoundingBox(min_lon=82.0, min_lat=15.0, max_lon=83.5, max_lat=18.0),
        start_time=datetime(2020, 9, 2, 12, 0, tzinfo=timezone.utc),
        end_time=datetime(2020, 9, 3, 18, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError) as excinfo:
        adapter.fetch_winds(invalid_query)
    assert "Spatial coverage error" in str(excinfo.value)
    assert "extends outside ERA5 dataset coverage" in str(excinfo.value)


def test_historical_wind_temporal_out_of_bounds():
    adapter = HistoricalWindAdapter()
    invalid_query = EnvironmentalQuery(
        bbox=BoundingBox(min_lon=82.0, min_lat=7.0, max_lon=83.5, max_lat=8.5),
        start_time=datetime(2019, 1, 1, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2019, 1, 2, 0, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError) as excinfo:
        adapter.fetch_winds(invalid_query)
    assert "Temporal coverage error" in str(excinfo.value)


# ---------------------------------------------------------------------------
# 3. Preservation of Synthetic Providers
# ---------------------------------------------------------------------------

def test_synthetic_environmental_providers_unbroken(valid_env_query):
    p_ocean = SyntheticOceanCurrentProvider()
    p_wind = SyntheticWindProvider()

    res_ocean = p_ocean.fetch_currents(valid_env_query)
    res_wind = p_wind.fetch_winds(valid_env_query)

    assert "SYNTHETIC_DATA" in res_ocean["data_classification"]
    assert "SYNTHETIC_DATA" in res_wind["data_classification"]


# ---------------------------------------------------------------------------
# 4. Environmental Dataset Audit Tool Execution Test
# ---------------------------------------------------------------------------

def test_audit_environmental_datasets():
    ocean_rep = audit_environmental_dataset("data/ocean/new_diamond_currents_cmems.json", modality="ocean")
    wind_rep = audit_environmental_dataset("data/wind/new_diamond_wind_era5.json", modality="wind")

    assert ocean_rep["quality_audit"]["has_valid_bounds"] is True
    assert ocean_rep["quality_audit"]["has_valid_time_window"] is True
    assert len(ocean_rep["quality_audit"]["errors"]) == 0

    assert wind_rep["quality_audit"]["has_valid_bounds"] is True
    assert wind_rep["quality_audit"]["has_valid_time_window"] is True
    assert len(wind_rep["quality_audit"]["errors"]) == 0
