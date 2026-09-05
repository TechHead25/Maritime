"""Unit and Integration Tests for Structured Forensic Evidence Engine (Task 1)."""

from datetime import datetime, timezone
import pytest

from backend.app.models.schemas import (
    AttributionScore,
    CandidateVessel,
    EvidenceCategory,
    EvidenceItem,
    FactorCategory,
    GeoPoint,
    ProbabilityCloud,
    ReleaseWindow,
    RiskLevel,
    SlickDetection,
    SlickPolygon,
    VesselPosition,
    VesselTrack,
    VesselType,
)
from backend.app.services.scoring_engine import ScoringEngine, ScoringWeights


@pytest.fixture
def sample_slick_detection():
    coords = [
        [82.90, 7.85],
        [83.00, 7.85],
        [83.00, 7.95],
        [82.90, 7.95],
        [82.90, 7.85]
    ]
    return SlickDetection(
        id="slick-001",
        sar_scene_id="sar-001",
        slick_polygon=SlickPolygon(coordinates=[coords]),
        centroid=GeoPoint(coordinates=[82.95, 7.90]),
        area_sq_km=4.8,
        perimeter_km=14.2,
        major_axis_orientation_deg=48.0,
        confidence_score=0.94
    )


@pytest.fixture
def sample_release_window():
    return ReleaseWindow(
        id="rw-001",
        drift_simulation_id="drift-001",
        estimated_start_time=datetime(2020, 9, 3, 1, 0, 0, tzinfo=timezone.utc),
        estimated_end_time=datetime(2020, 9, 3, 5, 0, 0, tzinfo=timezone.utc),
        peak_probability_time=datetime(2020, 9, 3, 3, 15, 0, tzinfo=timezone.utc),
        confidence_interval=0.90
    )


@pytest.fixture
def sample_probability_clouds():
    hull = [
        [82.70, 7.76],
        [82.74, 7.76],
        [82.74, 7.80],
        [82.70, 7.80],
        [82.70, 7.76]
    ]
    return [
        ProbabilityCloud(
            id="cloud-001",
            drift_simulation_id="drift-001",
            timestamp=datetime(2020, 9, 3, 3, 15, 0, tzinfo=timezone.utc),
            hours_before_sar=9.25,
            envelope_polygon=SlickPolygon(coordinates=[hull]),
            center_point=GeoPoint(coordinates=[82.72, 7.78]),
            dispersion_radius_km=0.58
        )
    ]


def test_supporting_evidence_generation(sample_slick_detection, sample_release_window, sample_probability_clouds):
    """Verifies that high-risk candidates generate detailed supporting evidence."""
    engine = ScoringEngine()

    candidate = CandidateVessel(
        id="cand-tanker-01",
        case_id="case-001",
        vessel_track_id="track-01",
        mmsi="371584000",
        vessel_name="HIGH RISK TANKER",
        vessel_type=VesselType.TANKER,
        closest_point_of_approach_km=0.8,
        time_of_closest_approach=datetime(2020, 9, 3, 3, 20, 0, tzinfo=timezone.utc),
        is_in_release_envelope=True,
        has_ais_gaps=True,
        gap_intervals=[[
            datetime(2020, 9, 3, 3, 0, 0, tzinfo=timezone.utc),
            datetime(2020, 9, 3, 8, 0, 0, tzinfo=timezone.utc),
        ]]
    )

    track = VesselTrack(
        id="track-01",
        mmsi="371584000",
        vessel_name="HIGH RISK TANKER",
        vessel_type=VesselType.TANKER,
        waypoints=[
            VesselPosition(timestamp=datetime(2020, 9, 3, 2, 0, tzinfo=timezone.utc), longitude=82.60, latitude=7.60, speed_over_ground_knots=14.0, course_over_ground_deg=45.0),
            VesselPosition(timestamp=datetime(2020, 9, 3, 3, 0, tzinfo=timezone.utc), longitude=82.70, latitude=7.75, speed_over_ground_knots=0.5, course_over_ground_deg=48.0),
        ],
        has_ais_gaps=True,
        gap_intervals=[[
            datetime(2020, 9, 3, 3, 0, 0, tzinfo=timezone.utc),
            datetime(2020, 9, 3, 8, 0, 0, tzinfo=timezone.utc),
        ]]
    )

    scores = engine.score_candidates(
        candidates=[candidate],
        vessel_tracks=[track],
        slick_detection=sample_slick_detection,
        release_window=sample_release_window,
        probability_clouds=sample_probability_clouds
    )

    assert len(scores) == 1
    score = scores[0]
    assert score.total_score >= 75.0
    assert score.risk_level == RiskLevel.VERY_HIGH
    assert len(score.supporting_evidence) >= 4
    
    # Check supporting evidence items
    categories = [ev.category for ev in score.supporting_evidence]
    assert all(c == EvidenceCategory.SUPPORTING_EVIDENCE for c in categories)

    # Check proximity evidence
    prox_ev = next(e for e in score.supporting_evidence if e.factor_category == FactorCategory.PROXIMITY)
    assert prox_ev.calculated_value is not None
    assert "Direct Origin Intersection" in prox_ev.title
    assert prox_ev.score_impact > 0.0


def test_exculpatory_evidence_generation(sample_slick_detection, sample_release_window, sample_probability_clouds):
    """Verifies that distant vessels generate exculpatory evidence."""
    engine = ScoringEngine()

    candidate = CandidateVessel(
        id="cand-distant-01",
        case_id="case-001",
        vessel_track_id="track-02",
        mmsi="123456789",
        vessel_name="EXONERATED CARRIER",
        vessel_type=VesselType.OTHER,
        closest_point_of_approach_km=38.5,
        time_of_closest_approach=datetime(2020, 9, 3, 10, 0, 0, tzinfo=timezone.utc),
        is_in_release_envelope=False,
        has_ais_gaps=False,
        gap_intervals=[]
    )

    track = VesselTrack(
        id="track-02",
        mmsi="123456789",
        vessel_name="EXONERATED CARRIER",
        vessel_type=VesselType.OTHER,
        waypoints=[
            VesselPosition(timestamp=datetime(2020, 9, 3, 9, 0, tzinfo=timezone.utc), longitude=83.50, latitude=8.50, speed_over_ground_knots=15.0, course_over_ground_deg=180.0),
            VesselPosition(timestamp=datetime(2020, 9, 3, 11, 0, tzinfo=timezone.utc), longitude=83.50, latitude=8.00, speed_over_ground_knots=15.2, course_over_ground_deg=180.0),
        ],
        has_ais_gaps=False,
        gap_intervals=[]
    )

    scores = engine.score_candidates(
        candidates=[candidate],
        vessel_tracks=[track],
        slick_detection=sample_slick_detection,
        release_window=sample_release_window,
        probability_clouds=sample_probability_clouds
    )

    assert len(scores) == 1
    score = scores[0]
    assert score.total_score <= 15.0
    assert len(score.exculpatory_evidence) >= 3

    # Check exculpatory items
    exculp_titles = [e.title for e in score.exculpatory_evidence]
    assert any("Significant Distance" in t for t in exculp_titles)
    assert any("Temporal Non-Overlap" in t for t in exculp_titles)
    assert any("Continuous 100% AIS" in t for t in exculp_titles)


def test_data_quality_and_uncertainty_items(sample_slick_detection, sample_release_window, sample_probability_clouds):
    """Verifies that data quality and uncertainty evidence items are systematically produced."""
    engine = ScoringEngine()

    candidate = CandidateVessel(
        id="cand-01",
        case_id="case-001",
        vessel_track_id="track-01",
        mmsi="371584000",
        vessel_name="SAMPLE VESSEL",
        vessel_type=VesselType.CARGO,
        closest_point_of_approach_km=5.0,
        time_of_closest_approach=datetime(2020, 9, 3, 3, 0, 0, tzinfo=timezone.utc),
        is_in_release_envelope=False,
        has_ais_gaps=False
    )

    track = VesselTrack(
        id="track-01",
        mmsi="371584000",
        vessel_name="SAMPLE VESSEL",
        vessel_type=VesselType.CARGO,
        waypoints=[
            VesselPosition(timestamp=datetime(2020, 9, 3, 2, 0, tzinfo=timezone.utc), longitude=82.7, latitude=7.7, speed_over_ground_knots=12.0, course_over_ground_deg=50.0),
            VesselPosition(timestamp=datetime(2020, 9, 3, 4, 0, tzinfo=timezone.utc), longitude=82.8, latitude=7.8, speed_over_ground_knots=12.0, course_over_ground_deg=50.0),
        ]
    )

    scores = engine.score_candidates(
        candidates=[candidate],
        vessel_tracks=[track],
        slick_detection=sample_slick_detection,
        release_window=sample_release_window,
        probability_clouds=sample_probability_clouds
    )

    score = scores[0]
    assert len(score.data_quality_items) >= 1
    assert len(score.uncertainty_items) >= 2

    # Check uncertainty item contents
    spatial_unc = next(e for e in score.uncertainty_items if "Spatial Dispersion" in e.title)
    assert "+/- 0.58 km" in spatial_unc.calculated_value

    temporal_unc = next(e for e in score.uncertainty_items if "Release Time Uncertainty" in e.title)
    assert "4.0 hours span" in temporal_unc.calculated_value
