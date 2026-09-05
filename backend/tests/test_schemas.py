"""Comprehensive unit tests for all 14 backend domain models."""

from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError

from backend.app.models.schemas import (
    InvestigationCase,
    SARScene,
    SlickDetection,
    SlickPolygon,
    DriftSimulation,
    Particle,
    ProbabilityCloud,
    ReleaseWindow,
    VesselTrack,
    VesselPosition,
    CandidateVessel,
    AttributionScore,
    AttributionScoreSubScores,
    EvidenceItem,
    InvestigationResult,
    CaseStatus,
    VesselType,
    RiskLevel,
    FactorCategory,
    ParticleStatus,
    GeoPoint,
    ensure_utc,
    validate_longitude,
    validate_latitude,
)


@pytest.fixture
def sample_utc_now():
    return datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def valid_polygon_coords():
    return [
        [
            [101.0, 2.0],
            [102.0, 2.0],
            [102.0, 3.0],
            [101.0, 3.0],
            [101.0, 2.0],
        ]
    ]


# ---------------------------------------------------------------------------
# 1. GeoPoint & SlickPolygon Tests
# ---------------------------------------------------------------------------

def test_geopoint_valid():
    pt = GeoPoint(coordinates=[102.5, 2.8])
    assert pt.longitude == 102.5
    assert pt.latitude == 2.8
    assert pt.type == "Point"


def test_geopoint_invalid_coordinates():
    # Longitude > 180
    with pytest.raises(ValidationError):
        GeoPoint(coordinates=[185.0, 2.8])

    # Latitude < -90
    with pytest.raises(ValidationError):
        GeoPoint(coordinates=[102.0, -95.0])

    # Insufficient elements
    with pytest.raises(ValidationError):
        GeoPoint(coordinates=[102.0])


def test_slick_polygon_valid(valid_polygon_coords):
    poly = SlickPolygon(coordinates=valid_polygon_coords)
    assert poly.type == "Polygon"
    assert len(poly.coordinates[0]) == 5


def test_slick_polygon_unclosed():
    # Last coordinate does not match first
    unclosed = [
        [
            [101.0, 2.0],
            [102.0, 2.0],
            [102.0, 3.0],
            [101.0, 3.0],
        ]
    ]
    with pytest.raises(ValidationError, match="not closed"):
        SlickPolygon(coordinates=unclosed)


def test_slick_polygon_too_few_vertices():
    # Less than 4 vertices
    short_ring = [
        [
            [101.0, 2.0],
            [102.0, 2.0],
            [101.0, 2.0],
        ]
    ]
    with pytest.raises(ValidationError, match="at least 4 coordinate pairs"):
        SlickPolygon(coordinates=short_ring)


def test_slick_polygon_invalid_coordinate_bounds():
    out_of_bounds = [
        [
            [205.0, 2.0],
            [102.0, 2.0],
            [102.0, 3.0],
            [101.0, 3.0],
            [205.0, 2.0],
        ]
    ]
    with pytest.raises(ValidationError, match="Longitude 205.0 is out of bounds"):
        SlickPolygon(coordinates=out_of_bounds)


# ---------------------------------------------------------------------------
# 2. InvestigationCase Tests
# ---------------------------------------------------------------------------

def test_investigation_case_valid(sample_utc_now, valid_polygon_coords):
    case = InvestigationCase(
        title="Malacca Case Alpha",
        status=CaseStatus.CREATED,
        region_of_interest=SlickPolygon(coordinates=valid_polygon_coords),
        created_at=sample_utc_now,
        updated_at=sample_utc_now,
        metadata={"analyst": "Dr. Smith", "synthetic": True}
    )
    assert case.title == "Malacca Case Alpha"
    assert case.status == CaseStatus.CREATED
    assert case.metadata["synthetic"] is True


def test_investigation_case_missing_required():
    with pytest.raises(ValidationError):
        # title is required
        InvestigationCase()


def test_investigation_case_naive_datetime():
    naive_dt = datetime(2026, 9, 1, 12, 0, 0)  # No timezone
    with pytest.raises(ValidationError, match="Datetime must be timezone-aware"):
        InvestigationCase(title="Naive Case", created_at=naive_dt)


# ---------------------------------------------------------------------------
# 3. SARScene Tests
# ---------------------------------------------------------------------------

def test_sar_scene_valid(sample_utc_now, valid_polygon_coords):
    scene = SARScene(
        case_id="case-123",
        satellite_platform="Sentinel-1B",
        sensor_mode="IW",
        polarization="VV",
        acquisition_timestamp=sample_utc_now,
        footprint_polygon=SlickPolygon(coordinates=valid_polygon_coords),
        pixel_resolution_meters=10.0
    )
    assert scene.satellite_platform == "Sentinel-1B"
    assert scene.pixel_resolution_meters == 10.0


def test_sar_scene_invalid_resolution(sample_utc_now):
    with pytest.raises(ValidationError):
        SARScene(
            case_id="case-123",
            acquisition_timestamp=sample_utc_now,
            pixel_resolution_meters=0.0  # Must be > 0
        )


# ---------------------------------------------------------------------------
# 4. SlickDetection Tests
# ---------------------------------------------------------------------------

def test_slick_detection_valid(valid_polygon_coords):
    slick = SlickDetection(
        sar_scene_id="sar-456",
        slick_polygon=SlickPolygon(coordinates=valid_polygon_coords),
        centroid=GeoPoint(coordinates=[101.5, 2.5]),
        area_sq_km=12.4,
        perimeter_km=15.8,
        major_axis_orientation_deg=45.0,
        confidence_score=0.92,
        lookalike_probability=0.08
    )
    assert slick.area_sq_km == 12.4
    assert slick.confidence_score == 0.92


def test_slick_detection_invalid_score(valid_polygon_coords):
    # Confidence score > 1.0
    with pytest.raises(ValidationError):
        SlickDetection(
            sar_scene_id="sar-456",
            slick_polygon=SlickPolygon(coordinates=valid_polygon_coords),
            centroid=GeoPoint(coordinates=[101.5, 2.5]),
            area_sq_km=12.4,
            perimeter_km=15.8,
            major_axis_orientation_deg=45.0,
            confidence_score=1.5  # Invalid
        )

    # Negative area
    with pytest.raises(ValidationError):
        SlickDetection(
            sar_scene_id="sar-456",
            slick_polygon=SlickPolygon(coordinates=valid_polygon_coords),
            centroid=GeoPoint(coordinates=[101.5, 2.5]),
            area_sq_km=-5.0,  # Invalid
            perimeter_km=15.8,
            major_axis_orientation_deg=45.0,
            confidence_score=0.8
        )


# ---------------------------------------------------------------------------
# 5. DriftSimulation & Particle Tests
# ---------------------------------------------------------------------------

def test_particle_valid(sample_utc_now):
    p = Particle(
        particle_index=0,
        longitude=102.1,
        latitude=2.9,
        timestamp=sample_utc_now,
        age_hours=2.5,
        status=ParticleStatus.ACTIVE
    )
    assert p.particle_index == 0
    assert p.status == ParticleStatus.ACTIVE


def test_particle_invalid_coordinates(sample_utc_now):
    with pytest.raises(ValidationError):
        Particle(
            particle_index=0,
            longitude=190.0,  # Out of bounds
            latitude=2.9,
            timestamp=sample_utc_now
        )


def test_drift_simulation_valid(sample_utc_now):
    t_start = sample_utc_now
    t_end = sample_utc_now - timedelta(hours=24)
    drift = DriftSimulation(
        slick_detection_id="slick-001",
        simulation_start_time=t_start,
        simulation_end_time=t_end,
        time_step_minutes=30,
        particle_count=2000,
        wind_leeway_factor=0.03,
        current_advection_factor=1.00
    )
    assert drift.particle_count == 2000
    assert drift.simulation_mode == "BACKWARD_LAGRANGIAN"


def test_drift_simulation_invalid_time_order(sample_utc_now):
    t_start = sample_utc_now
    t_end = sample_utc_now + timedelta(hours=24)  # Wrong direction: end is after start
    with pytest.raises(ValidationError, match="simulation_end_time must be earlier than simulation_start_time"):
        DriftSimulation(
            slick_detection_id="slick-001",
            simulation_start_time=t_start,
            simulation_end_time=t_end
        )


# ---------------------------------------------------------------------------
# 6. ProbabilityCloud & ReleaseWindow Tests
# ---------------------------------------------------------------------------

def test_probability_cloud_valid(sample_utc_now, valid_polygon_coords):
    cloud = ProbabilityCloud(
        drift_simulation_id="drift-001",
        timestamp=sample_utc_now,
        hours_before_sar=12.0,
        envelope_polygon=SlickPolygon(coordinates=valid_polygon_coords),
        center_point=GeoPoint(coordinates=[101.5, 2.5]),
        dispersion_radius_km=3.5,
        particle_sample_points=[[101.4, 2.4], [101.6, 2.6]]
    )
    assert cloud.hours_before_sar == 12.0
    assert cloud.dispersion_radius_km == 3.5


def test_release_window_valid(sample_utc_now):
    rw = ReleaseWindow(
        drift_simulation_id="drift-001",
        estimated_start_time=sample_utc_now - timedelta(hours=18),
        estimated_end_time=sample_utc_now - timedelta(hours=10),
        peak_probability_time=sample_utc_now - timedelta(hours=14),
        confidence_interval=0.90
    )
    assert rw.confidence_interval == 0.90


def test_release_window_invalid_peak(sample_utc_now):
    # Peak probability time outside [start, end]
    with pytest.raises(ValidationError, match="peak_probability_time must lie within"):
        ReleaseWindow(
            drift_simulation_id="drift-001",
            estimated_start_time=sample_utc_now - timedelta(hours=18),
            estimated_end_time=sample_utc_now - timedelta(hours=10),
            peak_probability_time=sample_utc_now - timedelta(hours=5),  # Outside bounds
        )


# ---------------------------------------------------------------------------
# 7. VesselPosition & VesselTrack Tests
# ---------------------------------------------------------------------------

def test_vessel_position_valid(sample_utc_now):
    pos = VesselPosition(
        timestamp=sample_utc_now,
        longitude=101.5,
        latitude=2.5,
        speed_over_ground_knots=12.5,
        course_over_ground_deg=45.0
    )
    assert pos.speed_over_ground_knots == 12.5


def test_vessel_position_invalid_speed(sample_utc_now):
    with pytest.raises(ValidationError):
        VesselPosition(
            timestamp=sample_utc_now,
            longitude=101.5,
            latitude=2.5,
            speed_over_ground_knots=-2.0  # Cannot be negative
        )


def test_vessel_track_valid(sample_utc_now):
    track = VesselTrack(
        mmsi="538009912",
        imo="9312345",
        vessel_name="PACIFIC GLORY",
        vessel_type=VesselType.TANKER,
        flag_country="Liberia",
        waypoints=[
            VesselPosition(
                timestamp=sample_utc_now,
                longitude=101.5,
                latitude=2.5,
                speed_over_ground_knots=12.0,
                course_over_ground_deg=48.0
            )
        ],
        has_ais_gaps=True,
        gap_intervals=[[sample_utc_now - timedelta(hours=2), sample_utc_now]]
    )
    assert track.mmsi == "538009912"
    assert track.vessel_type == VesselType.TANKER


def test_vessel_track_invalid_mmsi():
    with pytest.raises(ValidationError):
        VesselTrack(
            mmsi="123",  # Must be 9 digits
            vessel_name="BAD MMSI"
        )


# ---------------------------------------------------------------------------
# 8. CandidateVessel Tests
# ---------------------------------------------------------------------------

def test_candidate_vessel_valid(sample_utc_now):
    cand = CandidateVessel(
        case_id="case-1",
        vessel_track_id="trk-1",
        mmsi="538009912",
        vessel_name="PACIFIC GLORY",
        vessel_type=VesselType.TANKER,
        closest_point_of_approach_km=0.45,
        time_of_closest_approach=sample_utc_now,
        interpolated_position_at_cpa=GeoPoint(coordinates=[101.83, 2.61]),
        is_in_release_envelope=True
    )
    assert cand.closest_point_of_approach_km == 0.45
    assert cand.is_in_release_envelope is True


# ---------------------------------------------------------------------------
# 9. AttributionScore & EvidenceItem Tests
# ---------------------------------------------------------------------------

def test_attribution_score_valid():
    score = AttributionScore(
        candidate_vessel_id="cand-001",
        candidate_name="MT OCEAN MARAUDER",
        mmsi="538009912",
        vessel_type=VesselType.TANKER,
        rank=1,
        total_score=88.5,
        risk_level=RiskLevel.VERY_HIGH,
        sub_scores=AttributionScoreSubScores(
            proximity_score=33.2,
            trajectory_alignment_score=23.5,
            vessel_type_risk_score=15.0,
            navigational_anomaly_score=7.0,
            ais_integrity_penalty=9.8
        ),
        evidence_items=[
            EvidenceItem(
                attribution_score_id="score-001",
                factor_category=FactorCategory.PROXIMITY,
                title="Within 450m of Drift Origin",
                description="Intercepted within 450 meters.",
                score_impact=33.2,
                verifiable_data={"cpa_m": 450}
            )
        ]
    )
    assert score.total_score == 88.5
    assert score.sub_scores.proximity_score == 33.2
    assert len(score.evidence_items) == 1


def test_attribution_score_out_of_bounds():
    # total_score > 100.0
    with pytest.raises(ValidationError):
        AttributionScore(
            candidate_vessel_id="cand-001",
            candidate_name="MT OCEAN MARAUDER",
            mmsi="538009912",
            vessel_type=VesselType.TANKER,
            total_score=105.0,  # Out of bounds
            sub_scores=AttributionScoreSubScores(
                proximity_score=30.0,
                trajectory_alignment_score=20.0,
                vessel_type_risk_score=15.0,
                navigational_anomaly_score=5.0,
                ais_integrity_penalty=5.0
            )
        )

    # Sub-score proximity > 40.0
    with pytest.raises(ValidationError):
        AttributionScoreSubScores(
            proximity_score=45.0,  # Max is 40.0
            trajectory_alignment_score=20.0,
            vessel_type_risk_score=15.0,
            navigational_anomaly_score=5.0,
            ais_integrity_penalty=5.0
        )


# ---------------------------------------------------------------------------
# 10. InvestigationResult Tests
# ---------------------------------------------------------------------------

def test_investigation_result_valid(sample_utc_now, valid_polygon_coords):
    case = InvestigationCase(
        title="Complete Case",
        region_of_interest=SlickPolygon(coordinates=valid_polygon_coords),
        created_at=sample_utc_now,
        updated_at=sample_utc_now
    )
    result = InvestigationResult(
        case=case,
        sar_scenes=[],
        slicks=[],
        drift_simulations=[],
        probability_clouds=[],
        release_windows=[],
        candidate_vessels=[],
        attribution_scores=[],
        generated_at=sample_utc_now,
        summary_verdict="Investigation concluded. One primary candidate identified."
    )
    assert result.case.title == "Complete Case"
    assert "One primary candidate" in result.summary_verdict
