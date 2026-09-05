"""Case Loader service for reading and validating investigation cases from disk."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union

from backend.app.models.schemas import (
    InvestigationCase,
    SARScene,
    SlickDetection,
    SlickPolygon,
    GeoPoint,
    VesselTrack,
    VesselPosition,
    VesselType,
    CaseStatus,
)


class EnvironmentalData(NamedTuple):
    """Container for parsed hydrodynamic current and surface wind data."""
    ocean_currents: Dict[str, Any]
    wind_data: Dict[str, Any]


class LoadedCase(NamedTuple):
    """Aggregate bundle of typed models loaded from a case directory."""
    case: InvestigationCase
    sar_scene: SARScene
    slick_detection: SlickDetection
    vessel_tracks: List[VesselTrack]
    environment: EnvironmentalData


def _parse_iso_utc(ts_str: str) -> datetime:
    """Parse ISO formatted timestamp string and ensure UTC timezone."""
    # Handle 'Z' suffix
    clean_str = ts_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_case_from_disk(case_dir: Union[str, Path]) -> LoadedCase:
    """Loads and validates a complete case directory from disk into typed Pydantic models.
    
    Args:
        case_dir: Path to the case directory (e.g., 'data/cases/demo_case_001')
        
    Returns:
        LoadedCase containing typed domain models.
        
    Raises:
        FileNotFoundError: If any required JSON file is missing.
        pydantic.ValidationError: If data does not conform to schemas.
    """
    path = Path(case_dir)
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Case directory not found: {path}")

    # 1. Load case.json
    case_file = path / "case.json"
    if not case_file.exists():
        raise FileNotFoundError(f"Missing case.json in {path}")
    with open(case_file, "r", encoding="utf-8") as f:
        case_raw = json.load(f)
    
    roi = None
    if "region_of_interest" in case_raw and case_raw["region_of_interest"]:
        roi = SlickPolygon(**case_raw["region_of_interest"])

    metadata = case_raw.get("metadata", {})
    if "synthetic" in case_raw:
        metadata["synthetic"] = case_raw["synthetic"]
    if "data_classification" in case_raw:
        metadata["data_classification"] = case_raw["data_classification"]

    case = InvestigationCase(
        id=case_raw.get("id"),
        title=case_raw.get("title") or case_raw.get("name") or f"Investigation Case {case_raw.get('id')}",
        status=CaseStatus(case_raw.get("status", CaseStatus.CREATED)),
        region_of_interest=roi,
        created_at=_parse_iso_utc(case_raw["created_at"]),
        updated_at=_parse_iso_utc(case_raw["updated_at"]),
        metadata=metadata
    )

    # 2. Load sar_scene.json
    sar_file = path / "sar_scene.json"
    if not sar_file.exists():
        raise FileNotFoundError(f"Missing sar_scene.json in {path}")
    with open(sar_file, "r", encoding="utf-8") as f:
        sar_raw = json.load(f)
    
    footprint = None
    if "footprint_polygon" in sar_raw and sar_raw["footprint_polygon"]:
        footprint = SlickPolygon(**sar_raw["footprint_polygon"])

    sar_scene = SARScene(
        id=sar_raw.get("id"),
        case_id=sar_raw["case_id"],
        satellite_platform=sar_raw.get("satellite_platform", "Sentinel-1A"),
        sensor_mode=sar_raw.get("sensor_mode", "IW"),
        polarization=sar_raw.get("polarization", "VV"),
        acquisition_timestamp=_parse_iso_utc(sar_raw["acquisition_timestamp"]),
        footprint_polygon=footprint,
        image_path=sar_raw.get("image_path"),
        pixel_resolution_meters=float(sar_raw.get("pixel_resolution_meters", 10.0))
    )

    # 3. Load slick_detection.json
    slick_file = path / "slick_detection.json"
    if not slick_file.exists():
        raise FileNotFoundError(f"Missing slick_detection.json in {path}")
    with open(slick_file, "r", encoding="utf-8") as f:
        slick_raw = json.load(f)

    slick_detection = SlickDetection(
        id=slick_raw.get("id"),
        sar_scene_id=slick_raw["sar_scene_id"],
        slick_polygon=SlickPolygon(**slick_raw["slick_polygon"]),
        centroid=GeoPoint(**slick_raw["centroid"]),
        area_sq_km=float(slick_raw["area_sq_km"]),
        perimeter_km=float(slick_raw["perimeter_km"]),
        major_axis_orientation_deg=float(slick_raw["major_axis_orientation_deg"]),
        confidence_score=float(slick_raw["confidence_score"]),
        lookalike_probability=float(slick_raw.get("lookalike_probability", 0.0))
    )

    # 4. Load vessels.json
    vessels_file = path / "vessels.json"
    if not vessels_file.exists():
        raise FileNotFoundError(f"Missing vessels.json in {path}")
    with open(vessels_file, "r", encoding="utf-8") as f:
        vessels_raw = json.load(f)

    vessel_tracks: List[VesselTrack] = []
    vessels_list = vessels_raw.get("vessels", []) if isinstance(vessels_raw, dict) else (vessels_raw if isinstance(vessels_raw, list) else [])
    for v in vessels_list:
        waypoints: List[VesselPosition] = []
        for wp in v.get("waypoints", []):
            speed_val = wp.get("speed_over_ground_knots", wp.get("speed_knots", 0.0))
            course_val = wp.get("course_over_ground_deg", wp.get("course_over_ground", 0.0))
            waypoints.append(
                VesselPosition(
                    timestamp=_parse_iso_utc(wp["timestamp"]),
                    longitude=float(wp["longitude"]),
                    latitude=float(wp["latitude"]),
                    speed_over_ground_knots=float(speed_val),
                    course_over_ground_deg=float(course_val),
                    navigational_status=wp.get("navigational_status", "Under way using engine")
                )
            )
        
        gap_intervals: List[List[datetime]] = []
        for gap in v.get("gap_intervals", []):
            if len(gap) == 2:
                gap_intervals.append([_parse_iso_utc(gap[0]), _parse_iso_utc(gap[1])])

        track = VesselTrack(
            mmsi=str(v["mmsi"]),
            imo=str(v["imo"]) if v.get("imo") else None,
            vessel_name=v["vessel_name"],
            vessel_type=VesselType(v.get("vessel_type", "CARGO")),
            flag_country=v.get("flag_country", "Unknown"),
            waypoints=waypoints,
            has_ais_gaps=bool(v.get("has_ais_gaps", False)),
            gap_intervals=gap_intervals
        )
        vessel_tracks.append(track)

    # 5. Load environmental data (ocean currents and wind)
    ocean_file = path / "ocean_currents.json"
    wind_file = path / "wind_data.json"
    env_file = path / "environment.json"
    
    ocean_data = {}
    wind_data = {}

    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            env_raw = json.load(f)
            ocean_data = env_raw.get("ocean_currents", {})
            wind_data = env_raw.get("wind_data", {})

    if ocean_file.exists() and not ocean_data:
        with open(ocean_file, "r", encoding="utf-8") as f:
            ocean_data = json.load(f)

    if wind_file.exists() and not wind_data:
        with open(wind_file, "r", encoding="utf-8") as f:
            wind_data = json.load(f)

    environment = EnvironmentalData(
        ocean_currents=ocean_data,
        wind_data=wind_data
    )

    return LoadedCase(
        case=case,
        sar_scene=sar_scene,
        slick_detection=slick_detection,
        vessel_tracks=vessel_tracks,
        environment=environment
    )
