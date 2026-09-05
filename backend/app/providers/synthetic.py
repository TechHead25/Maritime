"""Synthetic Data Provider Implementations for Offline Testing & CI/CD.

Returns canonical typed domain models without requiring external network connectivity or API credentials.
Strictly labeled as SYNTHETIC in compliance with GEMINI.md rules.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from backend.app.models.schemas import (
    GeoPoint,
    SARScene,
    SlickPolygon,
    VesselPosition,
    VesselTrack,
    VesselType,
)
from backend.app.providers.base import (
    AISDataProvider,
    AISQuery,
    BoundingBox,
    EnvironmentalQuery,
    OceanCurrentProvider,
    SARDataProvider,
    SARQuery,
    WindDataProvider,
)
from backend.app.services.case_service import case_service
from backend.app.services.sar_detector import SARRaster, SyntheticSARGenerator

logger = logging.getLogger("maritime-oil-attribution.providers.synthetic")


class SyntheticSARProvider(SARDataProvider):
    """Synthetic SAR satellite data provider returning reproducible synthetic Sentinel-1 scenes."""

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed

    def search_scenes(self, query: SARQuery) -> List[SARScene]:
        """Returns synthetic Sentinel-1A scene metadata matching the query."""
        logger.info(f"SyntheticSARProvider: Searching scenes for bbox={query.bbox.as_tuple}")
        ring = [
            [query.bbox.min_lon, query.bbox.min_lat],
            [query.bbox.max_lon, query.bbox.min_lat],
            [query.bbox.max_lon, query.bbox.max_lat],
            [query.bbox.min_lon, query.bbox.max_lat],
            [query.bbox.min_lon, query.bbox.min_lat],
        ]
        scene = SARScene(
            id=f"sar-synthetic-{uuid.uuid4().hex[:8]}",
            case_id="synthetic-query-case",
            satellite_platform="Sentinel-1A (Synthetic SAR)",
            sensor_mode=query.sensor_mode or "IW",
            polarization=query.polarization or "VV",
            acquisition_timestamp=query.start_time,
            footprint_polygon=SlickPolygon(type="Polygon", coordinates=[ring]),
            pixel_resolution_meters=20.0,
        )
        return [scene]

    def fetch_raster(self, scene: SARScene) -> SARRaster:
        """Generates a synthetic calibrated SAR backscatter raster in dB."""
        logger.info(f"SyntheticSARProvider: Generating synthetic raster for scene='{scene.id}'")
        return SyntheticSARGenerator.create_synthetic_scene(
            width=300,
            height=300,
            top_left_lon=101.8,
            top_left_lat=3.1,
            seed=self.random_seed,
        )


class SyntheticAISProvider(AISDataProvider):
    """Synthetic AIS provider returning calibrated multi-candidate vessel tracks."""

    def fetch_vessel_tracks(self, query: AISQuery) -> List[VesselTrack]:
        """Returns synthetic benchmark vessel tracks intersecting the query envelope."""
        logger.info(f"SyntheticAISProvider: Fetching tracks for bbox={query.bbox.as_tuple}")
        # Load from default demo case if available
        tracks = case_service.vessel_tracks.get("demo-case-001", [])
        if tracks:
            return tracks

        # Fallback inline synthetic benchmark track
        t1 = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 9, 1, 1, 0, tzinfo=timezone.utc)
        return [
            VesselTrack(
                id="trk-synthetic-001",
                mmsi="538009912",
                vessel_name="MT PACIFIC GLORY",
                vessel_type=VesselType.TANKER,
                flag_country="Marshall Islands",
                waypoints=[
                    VesselPosition(timestamp=t1, longitude=101.78, latitude=2.58, speed_over_ground_knots=13.5, course_over_ground_deg=48.0),
                    VesselPosition(timestamp=t2, longitude=101.88, latitude=2.64, speed_over_ground_knots=13.2, course_over_ground_deg=48.0),
                ],
                has_ais_gaps=True,
                gap_intervals=[(t1.isoformat(), t2.isoformat())]
            )
        ]


class SyntheticOceanCurrentProvider(OceanCurrentProvider):
    """Synthetic oceanographic hydrodynamic current data provider."""

    def fetch_currents(self, query: EnvironmentalQuery) -> Dict[str, Any]:
        """Returns canonical ocean surface current vectors."""
        logger.info(f"SyntheticOceanCurrentProvider: Fetching currents for bbox={query.bbox.as_tuple}")
        return {
            "dataset_source": "CMEMS Global Ocean Physics Analysis and Forecast (Synthetic Fixture)",
            "data_classification": "SYNTHETIC_DATA",
            "spatial_resolution_deg": 0.083,
            "temporal_resolution_hours": 1.0,
            "depth_level_meters": 0.0,
            "mean_u_velocity_mps": 0.28,
            "mean_v_velocity_mps": 0.22,
            "current_speed_knots": 0.69,
            "current_direction_deg": 51.8,
            "description": "Synthetic calibrated steady coastal current vector for Straits of Malacca."
        }


class SyntheticWindProvider(WindDataProvider):
    """Synthetic atmospheric surface wind reanalysis provider."""

    def fetch_winds(self, query: EnvironmentalQuery) -> Dict[str, Any]:
        """Returns canonical atmospheric surface wind vectors."""
        logger.info(f"SyntheticWindProvider: Fetching winds for bbox={query.bbox.as_tuple}")
        return {
            "dataset_source": "ECMWF ERA5 Surface Wind Reanalysis (Synthetic Fixture)",
            "data_classification": "SYNTHETIC_DATA",
            "spatial_resolution_deg": 0.25,
            "temporal_resolution_hours": 1.0,
            "reference_height_meters": 10.0,
            "mean_u_wind_mps": 4.10,
            "mean_v_wind_mps": 4.80,
            "wind_speed_mps": 6.31,
            "wind_speed_knots": 12.27,
            "wind_direction_deg": 220.5,
            "description": "Synthetic southwest monsoon surface wind reanalysis."
        }
