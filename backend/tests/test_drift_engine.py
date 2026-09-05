"""Unit and integration tests for the Backward Particle Drift Engine."""

from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pytest

from backend.app.models.schemas import (
    GeoPoint,
    SlickDetection,
    SlickPolygon,
)
from backend.app.services.case_loader import load_case_from_disk
from backend.app.services.drift_engine import (
    DriftEngine,
    DriftEngineConfig,
    DriftSimulationResult,
)
from backend.app.utils.geo_utils import haversine_distance_km


@pytest.fixture
def sample_slick():
    poly = [
        [
            [102.12, 2.85],
            [102.18, 2.88],
            [102.16, 2.91],
            [102.10, 2.87],
            [102.12, 2.85]
        ]
    ]
    return SlickDetection(
        sar_scene_id="sar-1",
        slick_polygon=SlickPolygon(coordinates=poly),
        centroid=GeoPoint(coordinates=[102.14, 2.877]),
        area_sq_km=14.85,
        perimeter_km=18.4,
        major_axis_orientation_deg=48.5,
        confidence_score=0.94
    )


@pytest.fixture
def sample_ocean_current():
    return {
        "mean_current_vectors": {
            "u_eastward_m_per_s": 0.22,
            "v_northward_m_per_s": 0.12
        }
    }


@pytest.fixture
def sample_wind_data():
    return {
        "mean_wind_vectors": {
            "u_eastward_m_per_s": -3.5,
            "v_northward_m_per_s": -3.5
        }
    }


# ---------------------------------------------------------------------------
# 1. Determinism & Particle Count Tests
# ---------------------------------------------------------------------------

def test_drift_engine_determinism(sample_slick, sample_ocean_current, sample_wind_data):
    obs_time = datetime(2026, 9, 1, 14, 30, tzinfo=timezone.utc)
    config = DriftEngineConfig(
        time_step_minutes=30,
        max_hours_backward=12.0,
        particle_count=200,
        random_seed=42
    )

    engine1 = DriftEngine(config=config)
    res1 = engine1.run_backward_drift(
        slick_detection=sample_slick,
        observation_timestamp=obs_time,
        ocean_current_data=sample_ocean_current,
        wind_data=sample_wind_data
    )

    engine2 = DriftEngine(config=config)
    res2 = engine2.run_backward_drift(
        slick_detection=sample_slick,
        observation_timestamp=obs_time,
        ocean_current_data=sample_ocean_current,
        wind_data=sample_wind_data
    )

    # Centroid and dispersion must be 100% identical
    assert res1.origin_centroid.coordinates == res2.origin_centroid.coordinates
    assert res1.origin_uncertainty_radius_km == res2.origin_uncertainty_radius_km
    assert len(res1.probability_clouds) == len(res2.probability_clouds)


def test_drift_engine_configurable_timestep(sample_slick, sample_ocean_current):
    obs_time = datetime(2026, 9, 1, 14, 30, tzinfo=timezone.utc)
    
    # 60 min timestep over 12 hours -> 12 steps + 1 initial = 13 clouds
    config_60 = DriftEngineConfig(time_step_minutes=60, max_hours_backward=12.0, particle_count=100)
    res_60 = DriftEngine(config=config_60).run_backward_drift(
        slick_detection=sample_slick,
        observation_timestamp=obs_time,
        ocean_current_data=sample_ocean_current
    )
    assert len(res_60.probability_clouds) == 13

    # 15 min timestep over 6 hours -> 24 steps + 1 initial = 25 clouds
    config_15 = DriftEngineConfig(time_step_minutes=15, max_hours_backward=6.0, particle_count=100)
    res_15 = DriftEngine(config=config_15).run_backward_drift(
        slick_detection=sample_slick,
        observation_timestamp=obs_time,
        ocean_current_data=sample_ocean_current
    )
    assert len(res_15.probability_clouds) == 25


# ---------------------------------------------------------------------------
# 2. Particle Seeding & Cloud Envelope Tests
# ---------------------------------------------------------------------------

def test_particle_seeding_bounds(sample_slick):
    engine = DriftEngine(config=DriftEngineConfig(particle_count=300, random_seed=99))
    rng = np.random.default_rng(99)
    particles = engine._seed_particles(sample_slick, count=300, rng=rng)

    assert particles.shape == (300, 2)
    # Ensure all particles lie within bounding box + margin
    lons = particles[:, 0]
    lats = particles[:, 1]
    assert np.all(lons >= 102.05) and np.all(lons <= 102.25)
    assert np.all(lats >= 2.80) and np.all(lats <= 2.95)


def test_probability_clouds_structure(sample_slick, sample_ocean_current, sample_wind_data):
    obs_time = datetime(2026, 9, 1, 14, 30, tzinfo=timezone.utc)
    config = DriftEngineConfig(time_step_minutes=30, max_hours_backward=6.0, particle_count=200)
    res = DriftEngine(config=config).run_backward_drift(
        slick_detection=sample_slick,
        observation_timestamp=obs_time,
        ocean_current_data=sample_ocean_current,
        wind_data=sample_wind_data
    )

    for cloud in res.probability_clouds:
        assert cloud.center_point is not None
        assert cloud.envelope_polygon is not None
        assert cloud.dispersion_radius_km > 0.0
        assert len(cloud.particle_sample_points) > 0
        assert cloud.hours_before_sar >= 0.0


# ---------------------------------------------------------------------------
# 3. Integration with Synthetic Demo Case (demo_case_001)
# ---------------------------------------------------------------------------

def test_reconstruct_origin_on_demo_case_001():
    loaded = load_case_from_disk(Path("data/cases/demo_case_001"))
    
    engine = DriftEngine(
        config=DriftEngineConfig(
            time_step_minutes=30,
            max_hours_backward=24.0,
            particle_count=1000,
            wind_leeway_factor=0.03,
            current_advection_factor=1.00,
            random_seed=42
        )
    )

    result: DriftSimulationResult = engine.run_backward_drift(
        slick_detection=loaded.slick_detection,
        observation_timestamp=loaded.sar_scene.acquisition_timestamp,
        ocean_current_data=loaded.environment.ocean_currents,
        wind_data=loaded.environment.wind_data,
        estimated_release_hours_ago=14.0,
        release_window_half_width_hours=2.0
    )

    # 1. Check release window
    rw = result.release_window
    expected_peak = datetime(2026, 9, 1, 0, 30, tzinfo=timezone.utc)
    assert rw.peak_probability_time == expected_peak
    assert rw.estimated_start_time < rw.peak_probability_time < rw.estimated_end_time

    # 2. Check that reconstructed origin center is near the ground truth origin [101.83, 2.61]
    target_lon, target_lat = 101.83, 2.61
    calc_lon = result.origin_centroid.longitude
    calc_lat = result.origin_centroid.latitude

    dist_km = haversine_distance_km(calc_lon, calc_lat, target_lon, target_lat)
    
    # Distance to ground truth origin should be within reasonable proximity (< 3.0 km)
    assert dist_km < 3.0, f"Reconstructed origin [{calc_lon}, {calc_lat}] is {dist_km:.2f} km from ground truth [{target_lon}, {target_lat}]"

    # 3. Check dispersion radius
    assert result.origin_uncertainty_radius_km >= 0.5
    assert result.origin_uncertainty_radius_km < 10.0
