"""Domain Models for Maritime Oil-Spill Attribution Intelligence.

These models define the core domain entities and value objects with strict Pydantic v2 validation,
universal UTC timestamps, coordinate boundaries, and clear docstrings.
No scientific or business logic algorithms are embedded within these models.
"""

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


def utc_now() -> datetime:
    """Helper to return current UTC timezone-aware datetime."""
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """Validates that a datetime has timezone information and standardizes it to UTC."""
    if dt.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware (expected UTC / timezone.utc).")
    return dt.astimezone(timezone.utc)


def validate_longitude(val: float) -> float:
    """Ensures longitude is within valid WGS84 bounds [-180.0, 180.0]."""
    if not -180.0 <= val <= 180.0:
        raise ValueError(f"Longitude {val} is out of bounds [-180.0, 180.0].")
    return val


def validate_latitude(val: float) -> float:
    """Ensures latitude is within valid WGS84 bounds [-90.0, 90.0]."""
    if not -90.0 <= val <= 90.0:
        raise ValueError(f"Latitude {val} is out of bounds [-90.0, 90.0].")
    return val


def validate_mmsi(val: str) -> str:
    """Ensures MMSI is a valid 9-digit numerical string starting with standard MID."""
    clean = re.sub(r"[^\d]", "", str(val))
    if len(clean) != 9 or clean.startswith("0") or clean == "999999999":
        raise ValueError(f"Invalid MMSI '{val}'. Must be 9 numerical digits.")
    return clean


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CaseStatus(str, Enum):
    """Lifecycle status of an investigation case."""
    CREATED = "CREATED"
    SAR_PROCESSED = "SAR_PROCESSED"
    DRIFT_SIMULATED = "DRIFT_SIMULATED"
    AIS_INTERCEPTED = "AIS_INTERCEPTED"
    ATTRIBUTION_COMPLETED = "ATTRIBUTION_COMPLETED"
    CLOSED = "CLOSED"


class VesselType(str, Enum):
    """Vessel classification types relevant to maritime spill risk."""
    TANKER = "TANKER"
    CARGO = "CARGO"
    BUNKER = "BUNKER"
    FISHING = "FISHING"
    PASSENGER = "PASSENGER"
    OTHER = "OTHER"


class RiskLevel(str, Enum):
    """Attribution risk classification brackets."""
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NEGLIGIBLE = "NEGLIGIBLE"


class EvidenceCategory(str, Enum):
    """Categorization of discrete forensic evidence items."""
    SUPPORTING_EVIDENCE = "SUPPORTING_EVIDENCE"
    CONTRADICTING_EVIDENCE = "CONTRADICTING_EVIDENCE"
    EXCULPATORY_EVIDENCE = "EXCULPATORY_EVIDENCE"
    DATA_QUALITY = "DATA_QUALITY"
    UNCERTAINTY = "UNCERTAINTY"


class FactorCategory(str, Enum):
    """The forensic attribution factor and data provenance categories."""
    PROXIMITY = "PROXIMITY"
    ALIGNMENT = "ALIGNMENT"
    VESSEL_TYPE = "VESSEL_TYPE"
    BEHAVIOR = "BEHAVIOR"
    AIS_INTEGRITY = "AIS_INTEGRITY"
    DATA_QUALITY = "DATA_QUALITY"
    UNCERTAINTY = "UNCERTAINTY"


class ParticleStatus(str, Enum):
    """State of an individual Lagrangian drift particle."""
    ACTIVE = "ACTIVE"
    STRANDED = "STRANDED"
    DISPERSED = "DISPERSED"


# ---------------------------------------------------------------------------
# Geometric Value Objects
# ---------------------------------------------------------------------------

class GeoPoint(BaseModel):
    """GeoJSON Point geometry [longitude, latitude]."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    type: Literal["Point"] = Field(default="Point")
    coordinates: List[float] = Field(
        ...,
        description="[longitude, latitude] in decimal degrees (WGS84)",
        min_length=2,
        max_length=2
    )

    @field_validator("coordinates")
    @classmethod
    def validate_coords(cls, coords: List[float]) -> List[float]:
        validate_longitude(coords[0])
        validate_latitude(coords[1])
        return coords

    @property
    def longitude(self) -> float:
        return self.coordinates[0]

    @property
    def latitude(self) -> float:
        return self.coordinates[1]


class SlickPolygon(BaseModel):
    """GeoJSON Polygon geometry representing an oil slick boundary or region of interest."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    type: Literal["Polygon"] = Field(default="Polygon")
    coordinates: List[List[List[float]]] = Field(
        ...,
        description="GeoJSON polygon linear rings. Outer ring must have at least 4 coordinates and be closed."
    )

    @field_validator("coordinates")
    @classmethod
    def validate_polygon_rings(cls, rings: List[List[List[float]]]) -> List[List[List[float]]]:
        if not rings or len(rings) < 1:
            raise ValueError("Polygon must contain at least one linear ring.")
        for ring_idx, ring in enumerate(rings):
            if len(ring) < 4:
                raise ValueError(f"Ring {ring_idx} must contain at least 4 coordinate pairs.")
            # Check closure (first and last coordinate must match)
            if ring[0] != ring[-1]:
                raise ValueError(f"Ring {ring_idx} is not closed (first coordinate {ring[0]} != last coordinate {ring[-1]}).")
            for pt in ring:
                if len(pt) != 2:
                    raise ValueError(f"Coordinate pair {pt} in ring {ring_idx} must have exactly 2 values [lon, lat].")
                validate_longitude(pt[0])
                validate_latitude(pt[1])
        return rings


GeoPolygon = SlickPolygon


# ---------------------------------------------------------------------------
# 1. InvestigationCase
# ---------------------------------------------------------------------------

class InvestigationCase(BaseModel):
    """Root aggregate representing an official maritime spill forensic investigation."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique UUID for the case.")
    title: str = Field(..., min_length=1, max_length=255, description="Human-readable case title.")
    status: CaseStatus = Field(default=CaseStatus.CREATED, description="Lifecycle status.")
    region_of_interest: Optional[SlickPolygon] = Field(default=None, description="Spatial bounding polygon.")
    created_at: datetime = Field(default_factory=utc_now, description="UTC timestamp of case creation.")
    updated_at: datetime = Field(default_factory=utc_now, description="UTC timestamp of last update.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary (analysts, notes, tags).")

    @field_validator("created_at", "updated_at")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)


# ---------------------------------------------------------------------------
# 2. SARScene
# ---------------------------------------------------------------------------

class SARScene(BaseModel):
    """Metadata and geometry reference for a Synthetic Aperture Radar satellite overpass."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique SAR scene UUID.")
    case_id: str = Field(..., min_length=1, description="Parent InvestigationCase UUID.")
    satellite_platform: str = Field(default="Sentinel-1A", description="Satellite platform name.")
    sensor_mode: str = Field(default="IW", description="Sensor imaging mode (e.g., IW, EW, Stripmap).")
    polarization: str = Field(default="VV", description="Radar polarization channel (e.g., VV, VH, VV+VH).")
    acquisition_timestamp: datetime = Field(default_factory=utc_now, description="Observation UTC timestamp (T_obs).")
    footprint_polygon: Optional[SlickPolygon] = Field(default=None, description="Ground swath footprint polygon.")
    image_path: Optional[str] = Field(default=None, description="Local or remote path to the raster image.")
    pixel_resolution_meters: float = Field(default=10.0, gt=0.0, description="Spatial pixel resolution in meters.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary (granule_id, orbit, quicklook).")

    @field_validator("acquisition_timestamp")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)


# ---------------------------------------------------------------------------
# 3. SlickDetection
# ---------------------------------------------------------------------------

class SlickDetection(BaseModel):
    """A segmented dark formation extracted from SAR imagery and classified as an oil slick."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique slick detection UUID.")
    sar_scene_id: str = Field(..., min_length=1, description="Associated SARScene UUID.")
    slick_polygon: SlickPolygon = Field(..., description="Vector boundary polygon of the segmented slick.")
    centroid: GeoPoint = Field(..., description="Calculated center of mass of the slick.")
    area_sq_km: float = Field(..., gt=0.0, description="Surface area in square kilometers.")
    perimeter_km: float = Field(..., gt=0.0, description="Outer perimeter length in kilometers.")
    major_axis_orientation_deg: float = Field(..., ge=0.0, lt=360.0, description="Major axis orientation [0, 360) deg from True North.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Classification confidence (0.0 to 1.0).")
    lookalike_probability: float = Field(default=0.0, ge=0.0, le=1.0, description="Probability of being a biogenic/low-wind lookalike.")


class SARLookalikeClass(str, Enum):
    """Classification classes for SAR dark patch candidates."""
    MINERAL_OIL = "MINERAL_OIL"
    LOOKALIKE_LOW_WIND = "LOOKALIKE_LOW_WIND"
    LOOKALIKE_BIOGENIC = "LOOKALIKE_BIOGENIC"
    LOOKALIKE_COASTAL_SHADOW = "LOOKALIKE_COASTAL_SHADOW"
    LOOKALIKE_UPWELLING = "LOOKALIKE_UPWELLING"
    LOOKALIKE_RAIN_CELL = "LOOKALIKE_RAIN_CELL"
    BACKGROUND_SEA_CLUTTER = "BACKGROUND_SEA_CLUTTER"


class SARFeatureVector(BaseModel):
    """Explainable morphological, radiometric, and contextual features of a SAR dark patch."""
    model_config = ConfigDict(extra="forbid")

    area_sq_km: float = Field(..., gt=0.0, description="Surface area in square kilometers.")
    perimeter_km: float = Field(..., gt=0.0, description="Perimeter length in kilometers.")
    compactness: float = Field(..., ge=1.0, description="Isoperimetric quotient P^2 / (4*pi*A) (1.0 = perfect circle).")
    elongation_ratio: float = Field(..., ge=1.0, description="Ratio of major to minor principal axis lengths.")
    major_axis_orientation_deg: float = Field(..., ge=0.0, lt=360.0, description="Orientation angle in degrees.")
    mean_contrast_db: float = Field(..., description="Damping contrast: Ambient sea background mean dB minus patch mean dB.")
    std_dev_db: float = Field(..., ge=0.0, description="Internal backscatter standard deviation in dB.")
    coeff_of_variation: float = Field(..., ge=0.0, description="Coefficient of variation (std / mean).")
    edge_gradient_db_per_pixel: float = Field(..., ge=0.0, description="Mean sharpness of edge gradient transition in dB/pixel.")
    min_backscatter_db: float = Field(..., description="Minimum backscatter level within patch in dB.")
    distance_to_land_km: Optional[float] = Field(default=None, ge=0.0, description="Distance from centroid to nearest land/coastline in km.")
    ambient_wind_speed_ms: Optional[float] = Field(default=None, ge=0.0, description="Ambient sea surface wind speed in m/s.")


class SARCandidatePatch(BaseModel):
    """A candidate dark patch segmented from SAR imagery with classification and rejection audit trail."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Candidate patch unique UUID.")
    sar_scene_id: str = Field(..., min_length=1, description="Associated SAR scene UUID.")
    polygon: SlickPolygon = Field(..., description="Vector boundary polygon.")
    centroid: GeoPoint = Field(..., description="Geographic centroid.")
    classification: SARLookalikeClass = Field(..., description="Classified category.")
    is_accepted: bool = Field(..., description="True if accepted as mineral oil slick; False if rejected as lookalike/noise.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Classification confidence (0.0 - 1.0).")
    lookalike_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of lookalike occurrence.")
    rejection_reason: Optional[str] = Field(default=None, description="Detailed explanation for rejection if not accepted.")
    features: SARFeatureVector = Field(..., description="Complete explainable feature vector.")
    created_at: datetime = Field(default_factory=utc_now, description="UTC creation timestamp.")

    @field_validator("created_at")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)


class SARCandidateCollectionResponse(BaseModel):
    """API response model exposing accepted slicks and rejected candidate lookalikes."""
    case_id: str
    sar_scene_id: str
    total_candidates: int
    accepted_count: int
    rejected_count: int
    accepted_slicks: List[SARCandidatePatch]
    rejected_candidates: List[SARCandidatePatch]
    classifier_metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# 5. DriftSimulation & 6. Particle
# ---------------------------------------------------------------------------

class Particle(BaseModel):
    """An individual numerical particle tracked in a Lagrangian drift simulation."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    particle_index: int = Field(..., ge=0, description="Unique index within the simulation swarm.")
    longitude: float = Field(..., description="Current longitude in decimal degrees.")
    latitude: float = Field(..., description="Current latitude in decimal degrees.")
    timestamp: datetime = Field(..., description="UTC timestamp of the particle state.")
    age_hours: float = Field(default=0.0, ge=0.0, description="Particle age in hours backward from T_obs.")
    status: ParticleStatus = Field(default=ParticleStatus.ACTIVE, description="Particle lifecycle state.")

    @field_validator("longitude")
    @classmethod
    def check_lon(cls, v: float) -> float:
        return validate_longitude(v)

    @field_validator("latitude")
    @classmethod
    def check_lat(cls, v: float) -> float:
        return validate_latitude(v)

    @field_validator("timestamp")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)


class DriftSimulation(BaseModel):
    """Metadata and configuration for a backward Lagrangian drift simulation."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique simulation UUID.")
    slick_detection_id: str = Field(..., min_length=1, description="Associated SlickDetection UUID.")
    simulation_mode: str = Field(default="BACKWARD_LAGRANGIAN", description="Advection simulation mode.")
    simulation_start_time: datetime = Field(..., description="Observation timestamp T_obs.")
    simulation_end_time: datetime = Field(..., description="Historical limit T_obs - Delta_t.")
    time_step_minutes: int = Field(default=30, gt=0, le=120, description="Numerical integration timestep in minutes.")
    particle_count: int = Field(default=2000, ge=10, le=50000, description="Number of Monte Carlo particles.")
    wind_leeway_factor: float = Field(default=0.03, ge=0.0, le=0.10, description="Wind leeway coefficient (standard: 0.03).")
    current_advection_factor: float = Field(default=1.00, ge=0.5, le=1.5, description="Current advection scale factor.")
    created_at: datetime = Field(default_factory=utc_now, description="UTC execution timestamp.")

    @field_validator("simulation_start_time", "simulation_end_time", "created_at")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)

    @model_validator(mode="after")
    def validate_time_order(self) -> "DriftSimulation":
        if self.simulation_end_time >= self.simulation_start_time:
            raise ValueError("simulation_end_time must be earlier than simulation_start_time for backward drift.")
        return self


# ---------------------------------------------------------------------------
# 7. ProbabilityCloud & 8. ReleaseWindow
# ---------------------------------------------------------------------------

class ProbabilityCloud(BaseModel):
    """The spatial dispersion envelope of drift particles at a specific historical timestep."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique cloud UUID.")
    drift_simulation_id: str = Field(..., min_length=1, description="Associated DriftSimulation UUID.")
    timestamp: datetime = Field(..., description="UTC historical timestamp of this slice.")
    hours_before_sar: float = Field(..., ge=0.0, description="Hours elapsed backward from SAR observation.")
    envelope_polygon: SlickPolygon = Field(..., description="Convex hull / 95% confidence boundary.")
    center_point: GeoPoint = Field(..., description="Weighted mean center of the particle swarm.")
    dispersion_radius_km: float = Field(..., ge=0.0, description="Standard deviation dispersion radius in km.")
    particle_sample_points: List[List[float]] = Field(default_factory=list, description="Sample coordinates [[lon, lat], ...].")

    @field_validator("timestamp")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)


class ReleaseWindow(BaseModel):
    """The estimated temporal interval during which the oil release occurred."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique release window UUID.")
    drift_simulation_id: str = Field(..., min_length=1, description="Associated DriftSimulation UUID.")
    estimated_start_time: datetime = Field(..., description="Earliest probable release UTC timestamp.")
    estimated_end_time: datetime = Field(..., description="Latest probable release UTC timestamp.")
    peak_probability_time: datetime = Field(..., description="Peak likelihood release UTC timestamp.")
    confidence_interval: float = Field(default=0.90, ge=0.50, le=0.99, description="Statistical confidence bound (e.g., 0.90).")

    @field_validator("estimated_start_time", "estimated_end_time", "peak_probability_time")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)

    @model_validator(mode="after")
    def validate_window_bounds(self) -> "ReleaseWindow":
        if self.estimated_start_time >= self.estimated_end_time:
            raise ValueError("estimated_start_time must be earlier than estimated_end_time.")
        if not (self.estimated_start_time <= self.peak_probability_time <= self.estimated_end_time):
            raise ValueError("peak_probability_time must lie within [estimated_start_time, estimated_end_time].")
        return self


# ---------------------------------------------------------------------------
# 9. VesselTrack & 10. VesselPosition
# ---------------------------------------------------------------------------

class VesselPosition(BaseModel):
    """A single timestamped GPS navigation ping from a vessel transponder."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    timestamp: datetime = Field(..., description="UTC timestamp of the GPS ping.")
    longitude: float = Field(..., description="Longitude in decimal degrees.")
    latitude: float = Field(..., description="Latitude in decimal degrees.")
    speed_over_ground_knots: float = Field(default=0.0, ge=0.0, le=100.0, description="Speed Over Ground in knots.")
    course_over_ground_deg: float = Field(default=0.0, ge=0.0, lt=360.0, description="Course Over Ground [0, 360) deg.")
    navigational_status: str = Field(default="Under way using engine", description="AIS navigational status string.")

    @field_validator("timestamp")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)

    @field_validator("longitude")
    @classmethod
    def check_lon(cls, v: float) -> float:
        return validate_longitude(v)

    @field_validator("latitude")
    @classmethod
    def check_lat(cls, v: float) -> float:
        return validate_latitude(v)


class VesselTrack(BaseModel):
    """The historical GPS trajectory of a single vessel across the investigation period."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique vessel track UUID.")
    mmsi: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$", description="9-digit Maritime Mobile Service Identity.")
    imo: Optional[str] = Field(default=None, pattern=r"^\d{7}$", description="7-digit International Maritime Organization number.")
    vessel_name: str = Field(..., min_length=1, max_length=100, description="Vessel name.")
    vessel_type: VesselType = Field(default=VesselType.CARGO, description="Vessel classification type.")
    flag_country: str = Field(default="Unknown", description="Flag state administration.")
    waypoints: List[VesselPosition] = Field(default_factory=list, description="Ordered time-series list of GPS positions.")
    has_ais_gaps: bool = Field(default=False, description="Flag indicating transponder outage gaps inside ROI.")
    gap_intervals: List[List[datetime]] = Field(default_factory=list, description="List of [start_utc, end_utc] outage windows.")

    @field_validator("gap_intervals")
    @classmethod
    def check_gap_intervals(cls, intervals: List[List[datetime]]) -> List[List[datetime]]:
        validated = []
        for pair in intervals:
            if len(pair) != 2:
                raise ValueError("Each gap interval must contain exactly [start_datetime, end_datetime].")
            start = ensure_utc(pair[0])
            end = ensure_utc(pair[1])
            if start >= end:
                raise ValueError("Gap start timestamp must be strictly earlier than gap end timestamp.")
            validated.append([start, end])
        return validated


# ---------------------------------------------------------------------------
# 11. CandidateVessel
# ---------------------------------------------------------------------------

class CandidateVessel(BaseModel):
    """A vessel flagged for forensic evaluation due to spatiotemporal intersection with the release zone."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique candidate record UUID.")
    case_id: str = Field(..., min_length=1, description="Associated InvestigationCase UUID.")
    vessel_track_id: str = Field(..., min_length=1, description="Associated VesselTrack UUID.")
    mmsi: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$", description="9-digit MMSI.")
    vessel_name: str = Field(..., min_length=1, description="Vessel name.")
    vessel_type: VesselType = Field(..., description="Vessel classification type.")
    flag_country: str = Field(default="Unknown", description="Flag state.")
    closest_point_of_approach_km: float = Field(..., ge=0.0, description="Minimum distance to release centroid in km.")
    time_of_closest_approach: datetime = Field(..., description="UTC timestamp at closest approach.")
    interpolated_position_at_cpa: Optional[GeoPoint] = Field(default=None, description="Interpolated coordinates at CPA.")
    is_in_release_envelope: bool = Field(default=False, description="Whether vessel entered the 95% probability cloud.")
    has_ais_gaps: bool = Field(default=False, description="Whether vessel had transponder gaps near release window.")
    gap_intervals: List[List[datetime]] = Field(default_factory=list, description="Specific transponder outage windows.")

    @field_validator("time_of_closest_approach")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)


# ---------------------------------------------------------------------------
# 12. AttributionScore & 13. EvidenceItem
# ---------------------------------------------------------------------------

class AttributionScoreSubScores(BaseModel):
    """Individual breakdown of the 5 explainable attribution factors."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    proximity_score: float = Field(..., ge=0.0, le=40.0, description="Spatial proximity score [0.0, 40.0].")
    trajectory_alignment_score: float = Field(..., ge=0.0, le=25.0, description="Timing and trajectory alignment score [0.0, 25.0].")
    vessel_type_risk_score: float = Field(..., ge=0.0, le=15.0, description="Vessel cargo/type relevance weighting [0.0, 15.0].")
    navigational_anomaly_score: float = Field(..., ge=0.0, le=15.0, description="Navigational and behavioral anomaly score [0.0, 15.0].")
    ais_integrity_penalty: float = Field(..., ge=0.0, le=10.0, description="AIS continuity and transponder gap score [0.0, 10.0].")


class EvidenceItem(BaseModel):
    """A discrete, verifiable forensic fact supporting or contradicting an attribution score."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique evidence item UUID.")
    attribution_score_id: str = Field(..., min_length=1, description="Associated AttributionScore UUID.")
    candidate_vessel: str = Field(default="", description="Target candidate vessel name or MMSI.")
    category: EvidenceCategory = Field(default=EvidenceCategory.SUPPORTING_EVIDENCE, description="Evidence polarity/type.")
    factor_category: FactorCategory = Field(..., description="Attribution factor category.")
    title: str = Field(..., min_length=1, max_length=200, description="Concise evidence heading.")
    description: str = Field(..., min_length=1, description="Detailed explanatory text citing metrics and timestamps.")
    severity: str = Field(default="INFORMATIONAL", description="Evidence strength or severity (HIGH, MEDIUM, LOW, INFORMATIONAL).")
    source: str = Field(default="Historical AIS Ingestion", description="Sensor or model data source.")
    source_timestamp_start: Optional[datetime] = Field(default=None, description="Start timestamp of observed telemetry interval.")
    source_timestamp_end: Optional[datetime] = Field(default=None, description="End timestamp of observed telemetry interval.")
    calculated_value: Optional[str] = Field(default=None, description="Direct computed scientific value (e.g. '7.80 km', '14.2 -> 0.4 kts').")
    threshold_used: Optional[str] = Field(default=None, description="Decision threshold applied in evaluation.")
    calculation_reference: Optional[str] = Field(default=None, description="Methodological formula or reference.")
    confidence: float = Field(default=0.90, ge=0.0, le=1.0, description="Confidence in this evidence measurement.")
    uncertainty: Optional[str] = Field(default=None, description="Uncertainty range or margin of error.")
    score_impact: float = Field(default=0.0, ge=-50.0, le=50.0, description="Points contributed by this piece of evidence.")
    verifiable_data: Dict[str, Any] = Field(default_factory=dict, description="Raw supporting telemetry data.")


class AttributionScore(BaseModel):
    """The composite explainable liability rating and evidence chain for a candidate vessel."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique score UUID.")
    candidate_vessel_id: str = Field(..., min_length=1, description="Associated CandidateVessel UUID.")
    candidate_name: str = Field(..., min_length=1, description="Vessel name.")
    mmsi: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$", description="9-digit MMSI.")
    vessel_type: VesselType = Field(..., description="Vessel classification.")
    rank: int = Field(default=1, ge=1, description="Ordinal rank (1 = highest candidate).")
    total_score: float = Field(..., ge=0.0, le=100.0, description="Total composite attribution score [0.0, 100.0].")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Categorical risk classification.")
    sub_scores: AttributionScoreSubScores = Field(..., description="Breakdown of the 5 factor scores.")
    supporting_evidence: List[EvidenceItem] = Field(default_factory=list, description="Evidence items correlating candidate with release.")
    contradicting_evidence: List[EvidenceItem] = Field(default_factory=list, description="Evidence items reducing attribution likelihood.")
    exculpatory_evidence: List[EvidenceItem] = Field(default_factory=list, description="Evidence items strongly excluding or exonerating candidate.")
    data_quality_items: List[EvidenceItem] = Field(default_factory=list, description="Data quality assessment logs.")
    uncertainty_items: List[EvidenceItem] = Field(default_factory=list, description="Explicit scientific uncertainty boundaries.")
    evidence_items: List[EvidenceItem] = Field(default_factory=list, description="Consolidated list of all verifiable evidence logs.")


# ---------------------------------------------------------------------------
# 14. InvestigationResult
# ---------------------------------------------------------------------------

class InvestigationResult(BaseModel):
    """Aggregate forensic report container containing the complete evidence chain for a case."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    case: InvestigationCase = Field(..., description="The parent investigation case.")
    sar_scenes: List[SARScene] = Field(default_factory=list, description="SAR satellite passes analyzed.")
    slicks: List[SlickDetection] = Field(default_factory=list, description="Detected oil slick features.")
    drift_simulations: List[DriftSimulation] = Field(default_factory=list, description="Backward Lagrangian drift simulations.")
    probability_clouds: List[ProbabilityCloud] = Field(default_factory=list, description="Particle dispersion probability clouds.")
    release_windows: List[ReleaseWindow] = Field(default_factory=list, description="Estimated discharge temporal windows.")
    candidate_vessels: List[CandidateVessel] = Field(default_factory=list, description="Intercepted candidate vessels.")
    attribution_scores: List[AttributionScore] = Field(default_factory=list, description="Ranked attribution scores with evidence.")
    generated_at: datetime = Field(default_factory=utc_now, description="UTC timestamp of report generation.")
    summary_verdict: str = Field(
        default="Analysis completed. Review the ranked candidate evidence items.",
        description="Objective, evidence-based summary statement."
    )

    @field_validator("generated_at")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)
