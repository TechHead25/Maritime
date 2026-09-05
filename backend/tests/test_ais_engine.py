"""Unit and integration tests for the AIS Candidate Identification Engine."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from backend.app.models.schemas import (
    CandidateVessel,
    GeoPoint,
    ReleaseWindow,
    VesselPosition,
    VesselTrack,
    VesselType,
)
from backend.app.services.ais_engine import (
    AISEngine,
    AISEngineConfig,
    VesselNavigationalProfile,
)
from backend.app.services.case_loader import load_case_from_disk
from backend.app.services.drift_engine import DriftEngine, DriftEngineConfig


# ---------------------------------------------------------------------------
# 1. Unit Tests for AIS Helper Methods
# ---------------------------------------------------------------------------

def test_ais_waypoint_interpolation():
    engine = AISEngine(config=AISEngineConfig(interpolation_step_minutes=10.0))
    t1 = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 1, 1, 0, tzinfo=timezone.utc)

    wp = [
        VesselPosition(timestamp=t1, longitude=101.0, latitude=2.0, speed_over_ground_knots=10.0),
        VesselPosition(timestamp=t2, longitude=102.0, latitude=3.0, speed_over_ground_knots=10.0),
    ]

    dense = engine._interpolate_waypoints(wp, step_minutes=10.0)
    # 0, 10, 20, 30, 40, 50, 60 minutes -> 7 points
    assert len(dense) == 7
    assert dense[0].longitude == 101.0
    assert dense[-1].longitude == 102.0
    assert dense[3].timestamp == t1 + timedelta(minutes=30)
    assert abs(dense[3].longitude - 101.5) < 0.01


def test_ais_gap_detection():
    engine = AISEngine(config=AISEngineConfig(gap_threshold_minutes=60.0))
    t1 = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 1, 3, 0, tzinfo=timezone.utc)  # 3 hour gap

    track = VesselTrack(
        mmsi="123456789",
        vessel_name="GAP TESTER",
        waypoints=[
            VesselPosition(timestamp=t1, longitude=101.0, latitude=2.0),
            VesselPosition(timestamp=t2, longitude=101.5, latitude=2.5),
        ]
    )

    has_gap, intervals = engine._detect_ais_gaps(track)
    assert has_gap is True
    assert len(intervals) == 1
    assert intervals[0][0] == t1
    assert intervals[0][1] == t2


# ---------------------------------------------------------------------------
# 2. Integration Tests on Synthetic Benchmark (demo_case_001)
# ---------------------------------------------------------------------------

def test_identify_candidates_demo_case_001():
    # 1. Load case
    loaded = load_case_from_disk(Path("data/cases/demo_case_001"))

    # 2. Run drift engine to produce realistic probability clouds & release window
    drift_res = DriftEngine().run_backward_drift(
        slick_detection=loaded.slick_detection,
        observation_timestamp=loaded.sar_scene.acquisition_timestamp,
        ocean_current_data=loaded.environment.ocean_currents,
        wind_data=loaded.environment.wind_data,
        estimated_release_hours_ago=14.0,
        release_window_half_width_hours=2.0
    )

    # 3. Intercept AIS candidates
    engine = AISEngine(config=AISEngineConfig(max_cpa_distance_km=50.0))
    candidates: list[CandidateVessel] = engine.identify_candidates(
        case_id=loaded.case.id,
        vessel_tracks=loaded.vessel_tracks,
        release_window=drift_res.release_window,
        probability_clouds=drift_res.probability_clouds
    )

    # 4 candidates should be identified within 50 km
    assert len(candidates) == 4
    cand_map = {c.mmsi: c for c in candidates}

    # -----------------------------------------------------------------------
    # Vessel A (MT PACIFIC GLORY - Culprit Tanker)
    # Expected: Strong spatial (< 1 km) and timing evidence, in envelope
    # -----------------------------------------------------------------------
    cand_a = cand_map.get("538009912")
    assert cand_a is not None
    assert cand_a.vessel_name == "MT PACIFIC GLORY"
    assert cand_a.vessel_type == VesselType.TANKER
    assert cand_a.closest_point_of_approach_km < 1.0, f"Vessel A CPA was {cand_a.closest_point_of_approach_km} km"
    assert cand_a.is_in_release_envelope is True
    assert cand_a.has_ais_gaps is True
    # Closest approach should be near peak release time 00:45 UTC
    assert cand_a.time_of_closest_approach.hour == 0

    # -----------------------------------------------------------------------
    # Vessel B (MV ATLANTIC TRANSIT - Wrong Time)
    # Expected: Passes near origin spatial coordinate (< 2 km), but 11h late
    # -----------------------------------------------------------------------
    cand_b = cand_map.get("352001140")
    assert cand_b is not None
    assert cand_b.vessel_name == "MV ATLANTIC TRANSIT"
    assert cand_b.closest_point_of_approach_km < 2.0
    assert cand_b.is_in_release_envelope is False  # Outside release window cloud
    assert cand_b.time_of_closest_approach.hour == 11

    # -----------------------------------------------------------------------
    # Vessel C (STAR VOYAGER - Distant Passenger)
    # Expected: Correct time window (00:30 UTC), but far distance (> 25 km)
    # -----------------------------------------------------------------------
    cand_c = cand_map.get("211889900")
    assert cand_c is not None
    assert cand_c.vessel_name == "STAR VOYAGER"
    assert cand_c.vessel_type == VesselType.PASSENGER
    assert cand_c.closest_point_of_approach_km > 20.0
    assert cand_c.is_in_release_envelope is False
    assert drift_res.release_window.estimated_start_time <= cand_c.time_of_closest_approach <= drift_res.release_window.estimated_end_time

    # -----------------------------------------------------------------------
    # Vessel D (NEPTUNE TRADER - AIS Gap, Weak Proximity)
    # Expected: Exhibits AIS gap, but moderate distance (> 10 km)
    # -----------------------------------------------------------------------
    cand_d = cand_map.get("636015522")
    assert cand_d is not None
    assert cand_d.vessel_name == "NEPTUNE TRADER"
    assert cand_d.has_ais_gaps is True
    assert cand_d.closest_point_of_approach_km > 10.0
    assert cand_d.is_in_release_envelope is False
