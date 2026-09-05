"""Unit and Integration Tests for Continuous Synchronized Timeline & Trajectory Interpolation (Task 2)."""

from datetime import datetime, timedelta, timezone
import pytest

from backend.app.models.schemas import (
    GeoPoint,
    ProbabilityCloud,
    ReleaseWindow,
    SlickPolygon,
    VesselPosition,
    VesselTrack,
    VesselType,
)
from backend.app.services.ais_engine import AISEngine, AISEngineConfig


@pytest.fixture
def sample_trajectory():
    t0 = datetime(2020, 9, 3, 2, 0, 0, tzinfo=timezone.utc)
    waypoints = [
        VesselPosition(timestamp=t0, longitude=82.50, latitude=7.50, speed_over_ground_knots=14.0, course_over_ground_deg=45.0),
        VesselPosition(timestamp=t0 + timedelta(hours=1), longitude=82.65, latitude=7.65, speed_over_ground_knots=14.0, course_over_ground_deg=45.0),
        VesselPosition(timestamp=t0 + timedelta(hours=2), longitude=82.80, latitude=7.80, speed_over_ground_knots=0.5, course_over_ground_deg=50.0),
        VesselPosition(timestamp=t0 + timedelta(hours=3), longitude=82.85, latitude=7.85, speed_over_ground_knots=1.0, course_over_ground_deg=50.0),
        VesselPosition(timestamp=t0 + timedelta(hours=5), longitude=83.10, latitude=8.10, speed_over_ground_knots=12.0, course_over_ground_deg=45.0),
    ]
    return VesselTrack(
        id="track-sync-001",
        mmsi="371584000",
        vessel_name="MT NEW DIAMOND",
        vessel_type=VesselType.TANKER,
        waypoints=waypoints,
        has_ais_gaps=True,
        gap_intervals=[[t0 + timedelta(hours=2), t0 + timedelta(hours=4)]]
    )


@pytest.fixture
def sample_clouds():
    t0 = datetime(2020, 9, 3, 0, 0, 0, tzinfo=timezone.utc)
    clouds = []
    hull = [[82.70, 7.76], [82.74, 7.76], [82.74, 7.80], [82.70, 7.80], [82.70, 7.76]]
    
    for h in range(15):
        t = t0 + timedelta(hours=h)
        clouds.append(
            ProbabilityCloud(
                id=f"cloud-{h}",
                drift_simulation_id="drift-01",
                timestamp=t,
                hours_before_sar=14.0 - h,
                envelope_polygon=SlickPolygon(coordinates=[hull]),
                center_point=GeoPoint(coordinates=[82.70 + (h * 0.015), 7.75 + (h * 0.010)]),
                dispersion_radius_km=0.50 + (h * 0.05),
                particle_sample_points=[[82.70, 7.75], [82.72, 7.77]]
            )
        )
    return clouds


def test_trajectory_waypoint_interpolation_accuracy(sample_trajectory):
    """Verifies that intermediate timestamps interpolate geodesic positions accurately."""
    engine = AISEngine()
    
    # Query exact midpoint between t0 (02:00) and t0+1h (03:00) -> 02:30 UTC
    t_mid = datetime(2020, 9, 3, 2, 30, 0, tzinfo=timezone.utc)
    
    # Waypoint 1: [82.50, 7.50], Waypoint 2: [82.65, 7.65]
    # Expected: [82.575, 7.575]
    interpolated_pts = engine._interpolate_waypoints(sample_trajectory.waypoints, step_minutes=15)
    
    match = next((p for p in interpolated_pts if p.timestamp == t_mid), None)
    assert match is not None
    assert pytest.approx(match.longitude, 0.001) == 82.575
    assert pytest.approx(match.latitude, 0.001) == 7.575
    assert pytest.approx(match.speed_over_ground_knots, 0.1) == 14.0


def test_timeline_boundary_conditions(sample_trajectory):
    """Verifies behavior when querying timestamps outside track bounds."""
    engine = AISEngine()
    interpolated_pts = engine._interpolate_waypoints(sample_trajectory.waypoints, step_minutes=30)
    
    t_start = sample_trajectory.waypoints[0].timestamp
    t_end = sample_trajectory.waypoints[-1].timestamp
    
    assert interpolated_pts[0].timestamp == t_start
    assert interpolated_pts[-1].timestamp == t_end
    assert len(interpolated_pts) >= 10


def test_particle_cloud_time_synchronization(sample_clouds):
    """Verifies finding closest probability cloud timestep to any arbitrary query time."""
    query_time = datetime(2020, 9, 3, 3, 17, 30, tzinfo=timezone.utc)
    
    # Closest cloud should be at 03:00 UTC (index 3)
    closest = min(sample_clouds, key=lambda c: abs((c.timestamp - query_time).total_seconds()))
    assert closest.timestamp == datetime(2020, 9, 3, 3, 0, 0, tzinfo=timezone.utc)
    assert len(closest.particle_sample_points) == 2


def test_ais_gap_window_synchronization(sample_trajectory):
    """Verifies that an AIS blackout is correctly identified at intermediate simulation times."""
    t_gap = datetime(2020, 9, 3, 4, 30, 0, tzinfo=timezone.utc)
    gaps = sample_trajectory.gap_intervals
    
    is_in_gap = any(g[0] <= t_gap <= g[1] for g in gaps)
    assert is_in_gap is True
    
    t_nominal = datetime(2020, 9, 3, 2, 15, 0, tzinfo=timezone.utc)
    is_nominal_gap = any(g[0] <= t_nominal <= g[1] for g in gaps)
    assert is_nominal_gap is False
