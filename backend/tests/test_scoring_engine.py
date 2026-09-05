"""Unit and integration tests for the Multi-Factor Attribution Scoring Engine."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from backend.app.models.schemas import (
    CandidateVessel,
    EvidenceItem,
    FactorCategory,
    GeoPoint,
    ReleaseWindow,
    RiskLevel,
    SlickDetection,
    SlickPolygon,
    VesselPosition,
    VesselTrack,
    VesselType,
)
from backend.app.services.ais_engine import AISEngine, AISEngineConfig
from backend.app.services.case_loader import load_case_from_disk
from backend.app.services.drift_engine import DriftEngine, DriftEngineConfig
from backend.app.services.scoring_engine import ScoringEngine, ScoringWeights


@pytest.fixture
def sample_setup():
    peak_time = datetime(2026, 9, 1, 0, 30, tzinfo=timezone.utc)
    rw = ReleaseWindow(
        drift_simulation_id="sim-1",
        estimated_start_time=peak_time - timedelta(hours=2),
        estimated_end_time=peak_time + timedelta(hours=2),
        peak_probability_time=peak_time
    )

    poly = [
        [[102.10, 2.80], [102.18, 2.88], [102.16, 2.91], [102.08, 2.83], [102.10, 2.80]]
    ]
    slick = SlickDetection(
        sar_scene_id="sar-1",
        slick_polygon=SlickPolygon(coordinates=poly),
        centroid=GeoPoint(coordinates=[102.14, 2.87]),
        area_sq_km=14.85,
        perimeter_km=18.0,
        major_axis_orientation_deg=48.0,
        confidence_score=0.95
    )

    return rw, slick, peak_time


# ---------------------------------------------------------------------------
# 1. Integration Tests on Synthetic Benchmark (demo_case_001)
# ---------------------------------------------------------------------------

def test_score_candidates_demo_case_001():
    # 1. Load case
    loaded = load_case_from_disk(Path("data/cases/demo_case_001"))

    # 2. Run drift engine
    drift_res = DriftEngine().run_backward_drift(
        slick_detection=loaded.slick_detection,
        observation_timestamp=loaded.sar_scene.acquisition_timestamp,
        ocean_current_data=loaded.environment.ocean_currents,
        wind_data=loaded.environment.wind_data,
        estimated_release_hours_ago=14.0,
        release_window_half_width_hours=2.0
    )

    # 3. Intercept AIS candidates
    candidates = AISEngine().identify_candidates(
        case_id=loaded.case.id,
        vessel_tracks=loaded.vessel_tracks,
        release_window=drift_res.release_window,
        probability_clouds=drift_res.probability_clouds
    )

    # 4. Score candidates
    scoring_engine = ScoringEngine()
    ranked_scores = scoring_engine.score_candidates(
        candidates=candidates,
        vessel_tracks=loaded.vessel_tracks,
        slick_detection=loaded.slick_detection,
        release_window=drift_res.release_window,
        probability_clouds=drift_res.probability_clouds
    )

    assert len(ranked_scores) == 4

    # -----------------------------------------------------------------------
    # Rank #1 Must be Vessel A (MT PACIFIC GLORY - Culprit Tanker)
    # -----------------------------------------------------------------------
    top_candidate = ranked_scores[0]
    assert top_candidate.rank == 1
    assert top_candidate.candidate_name == "MT PACIFIC GLORY"
    assert top_candidate.mmsi == "538009912"
    assert top_candidate.total_score >= 80.0, f"Expected score >= 80, got {top_candidate.total_score}"
    assert top_candidate.risk_level == RiskLevel.VERY_HIGH

    # Verify breakdown of Sub-Scores for Rank 1
    subs = top_candidate.sub_scores
    assert subs.proximity_score >= 35.0   # Out of 40 (passed within 450m)
    assert subs.trajectory_alignment_score >= 20.0  # Out of 25 (timing in window)
    assert subs.vessel_type_risk_score == 10.0      # Out of 10 (Tanker)
    assert subs.ais_integrity_penalty == 10.0       # Out of 10 (Gap in zone)
    assert subs.navigational_anomaly_score >= 10.0  # Out of 15 (Heading match & speed drop)

    # Verify evidence items
    assert len(top_candidate.evidence_items) >= 4
    categories = [e.factor_category for e in top_candidate.evidence_items]
    assert FactorCategory.PROXIMITY in categories
    assert FactorCategory.AIS_INTEGRITY in categories

    # -----------------------------------------------------------------------
    # Remaining candidates must score significantly lower
    # -----------------------------------------------------------------------
    for other in ranked_scores[1:]:
        assert other.total_score < 45.0, f"Innocent/control vessel {other.candidate_name} scored too high: {other.total_score}"
        assert other.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.NEGLIGIBLE]


# ---------------------------------------------------------------------------
# 2. Factor Sensitivity & Isolation Tests
# ---------------------------------------------------------------------------

def test_proximity_factor_isolation(sample_setup):
    rw, slick, peak_time = sample_setup
    engine = ScoringEngine()

    cand_close = CandidateVessel(
        case_id="case-1",
        vessel_track_id="t-1",
        mmsi="123456789",
        vessel_name="CLOSE SHIP",
        vessel_type=VesselType.CARGO,
        closest_point_of_approach_km=0.2,
        time_of_closest_approach=peak_time
    )

    cand_far = CandidateVessel(
        case_id="case-1",
        vessel_track_id="t-2",
        mmsi="987654321",
        vessel_name="FAR SHIP",
        vessel_type=VesselType.CARGO,
        closest_point_of_approach_km=15.0,
        time_of_closest_approach=peak_time
    )

    # Close vessel (0.2 km) vs Distant vessel (15.0 km)
    s_close, _ = engine._score_proximity(
        score_id="1",
        candidate=cand_close,
        track=None,
        probability_clouds=[],
        release_window=rw,
        dispersion_sigma=1.5
    )
    s_far, _ = engine._score_proximity(
        score_id="2",
        candidate=cand_far,
        track=None,
        probability_clouds=[],
        release_window=rw,
        dispersion_sigma=1.5
    )

    assert s_close > 35.0
    assert s_far < 1.0
    assert s_close > s_far


def test_timing_factor_isolation(sample_setup):
    rw, slick, peak_time = sample_setup
    engine = ScoringEngine()

    # In window (00:30 UTC) vs Late transit (12:30 UTC - 12h later)
    s_ontime, _ = engine._score_timing(score_id="1", cpa_time=peak_time, release_window=rw)
    s_late, _ = engine._score_timing(score_id="2", cpa_time=peak_time + timedelta(hours=12), release_window=rw)

    assert s_ontime >= 24.0
    assert s_late < 2.0
    assert s_ontime > s_late


def test_vessel_relevance_isolation():
    engine = ScoringEngine()

    s_tanker, _ = engine._score_vessel_relevance("1", VesselType.TANKER)
    s_cargo, _ = engine._score_vessel_relevance("2", VesselType.CARGO)
    s_passenger, _ = engine._score_vessel_relevance("3", VesselType.PASSENGER)

    assert s_tanker == 10.0
    assert s_cargo == 6.0
    assert s_passenger == 1.0
    assert s_tanker > s_cargo > s_passenger


def test_ais_continuity_isolation(sample_setup):
    rw, slick, peak_time = sample_setup
    engine = ScoringEngine()

    cand_with_gap = CandidateVessel(
        case_id="case-1",
        vessel_track_id="trk-1",
        mmsi="111222333",
        vessel_name="GAP SHIP",
        vessel_type=VesselType.CARGO,
        closest_point_of_approach_km=1.0,
        time_of_closest_approach=peak_time,
        has_ais_gaps=True,
        gap_intervals=[[peak_time - timedelta(hours=1), peak_time + timedelta(hours=1)]]
    )

    cand_clean = CandidateVessel(
        case_id="case-1",
        vessel_track_id="trk-2",
        mmsi="444555666",
        vessel_name="CLEAN SHIP",
        vessel_type=VesselType.CARGO,
        closest_point_of_approach_km=1.0,
        time_of_closest_approach=peak_time,
        has_ais_gaps=False,
        gap_intervals=[]
    )

    s_gap, ev_gap = engine._score_ais_continuity("1", cand_with_gap, None, rw)
    s_clean, ev_clean = engine._score_ais_continuity("2", cand_clean, None, rw)

    assert s_gap == 10.0
    assert s_clean == 0.0
    assert "AIS transponder was deactivated" in ev_gap.description
    assert "Continuous" in ev_clean.title
