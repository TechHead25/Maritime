"""Unit and Integration tests for Historical SAR Adapter and MT New Diamond case."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import SARScene, SlickDetection
from backend.app.providers.base import BoundingBox, SARQuery
from backend.app.providers.sar_adapter import HistoricalSARAdapter
from backend.app.services.case_service import case_service
from backend.app.services.pipeline_service import pipeline_service, PipelineOptions

client = TestClient(app)


@pytest.fixture
def new_diamond_sar_query():
    return SARQuery(
        bbox=BoundingBox(min_lon=82.0, min_lat=7.0, max_lon=83.5, max_lat=8.5),
        start_time=datetime(2020, 9, 3, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2020, 9, 3, 18, 0, tzinfo=timezone.utc),
        satellite_platform="Sentinel-1A",
        sensor_mode="IW",
        polarization="VV",
    )


# ---------------------------------------------------------------------------
# 1. Historical SAR Adapter Unit Tests
# ---------------------------------------------------------------------------

def test_historical_sar_adapter_search_scenes(new_diamond_sar_query):
    adapter = HistoricalSARAdapter()
    scenes = adapter.search_scenes(new_diamond_sar_query)

    assert len(scenes) == 1
    scene = scenes[0]
    assert scene.satellite_platform == "Sentinel-1A"
    assert scene.sensor_mode == "IW"
    assert scene.polarization == "VV"
    assert scene.acquisition_timestamp.isoformat() == "2020-09-03T12:45:00+00:00"


def test_historical_sar_adapter_fetch_raster(new_diamond_sar_query):
    adapter = HistoricalSARAdapter()
    scenes = adapter.search_scenes(new_diamond_sar_query)
    raster = adapter.fetch_raster(scenes[0])

    assert raster.data_db.shape == (300, 300)
    assert raster.top_left_lon == 82.20
    assert raster.top_left_lat == 8.10
    assert raster.pixel_resolution_meters == 220.0


def test_historical_sar_spatial_out_of_bounds():
    adapter = HistoricalSARAdapter()
    invalid_query = SARQuery(
        bbox=BoundingBox(min_lon=70.0, min_lat=15.0, max_lon=75.0, max_lat=18.0),
        start_time=datetime(2020, 9, 3, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2020, 9, 3, 18, 0, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError) as excinfo:
        adapter.search_scenes(invalid_query)
    assert "Spatial coverage error" in str(excinfo.value)


# ---------------------------------------------------------------------------
# 2. Complete Investigation Pipeline on MT New Diamond Historical Case
# ---------------------------------------------------------------------------

def test_pipeline_on_historical_case_new_diamond():
    # Reload cases from disk to ensure case_new_diamond_2020 is in case_service
    case_service.reload_cases_from_disk()

    assert "case_new_diamond_2020" in case_service.cases

    opts = PipelineOptions(
        time_step_minutes=30,
        max_hours_backward=18.0,
        particle_count=500,
        random_seed=42,
        estimated_release_hours_ago=9.25,  # Incident at 03:30, SAR at 12:45 -> 9.25h ago
        release_window_half_width_hours=2.0,
        use_synthetic_slick=False,
    )

    response = pipeline_service.run_pipeline("case_new_diamond_2020", options=opts)

    # 1. Slick Detection
    assert len(response.slicks) >= 1
    slick = response.slicks[0]
    assert slick.confidence_score >= 0.70

    # 2. Origin & Drift
    assert len(response.probability_clouds) > 0
    origin = response.origin_centroid.coordinates
    # Reconstructed origin should be near MT New Diamond fire coordinates (82.50E, 7.75N)
    assert abs(origin[0] - 82.50) < 0.40
    assert abs(origin[1] - 7.75) < 0.40

    # 3. Attribution & Candidate Ranking
    assert len(response.candidate_vessels) >= 3
    assert len(response.attribution_scores) >= 3

    top_candidate = response.attribution_scores[0]
    assert top_candidate.rank == 1
    assert top_candidate.candidate_name == "MT NEW DIAMOND"
    assert top_candidate.mmsi == "371584000"
    assert top_candidate.total_score >= 50.0
    assert "MT NEW DIAMOND" in response.summary_verdict


# ---------------------------------------------------------------------------
# 3. API Test for MT New Diamond Historical Case
# ---------------------------------------------------------------------------

def test_api_investigate_historical_case_new_diamond():
    case_service.reload_cases_from_disk()

    response = client.post(
        "/api/cases/case_new_diamond_2020/investigate",
        json={
            "estimated_release_hours_ago": 9.25,
            "max_hours_backward": 18.0,
            "random_seed": 42,
            "use_synthetic_slick": False,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case"]["id"] == "case_new_diamond_2020"
    assert data["attribution_scores"][0]["candidate_name"] == "MT NEW DIAMOND"
