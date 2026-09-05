"""Real Historical Ocean Current Data Adapter (CMEMS Physics Reanalysis).

Ingests Copernicus Marine Service (CMEMS) hydrodynamic velocity field datasets,
enforces strict spatial and temporal coverage boundaries, performs bilinear spatial
interpolation, and returns canonical current models for the backward drift engine.
"""

from datetime import datetime, timezone
import json
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dateutil import parser as dt_parser

from backend.app.models.schemas import ensure_utc, validate_latitude, validate_longitude
from backend.app.providers.base import BoundingBox, EnvironmentalQuery, OceanCurrentProvider

logger = logging.getLogger("maritime-oil-attribution.providers.ocean")


class HistoricalOceanCurrentAdapter(OceanCurrentProvider):
    """Adapter for historical CMEMS Global Ocean Physics Analysis & Forecast reanalysis files."""

    def __init__(self, data_file_path: Optional[str] = None):
        self.data_file_path = data_file_path or "data/ocean/new_diamond_currents_cmems.json"

    def load_dataset(self, file_path: str) -> Dict[str, Any]:
        """Loads and parses the raw JSON / NetCDF abstraction dataset file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Ocean current data file not found: '{file_path}'")

        with open(file_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def validate_spatial_coverage(self, query_bbox: BoundingBox, data_bounds: Dict[str, float]):
        """Validates that the query bounding box is completely enclosed within dataset bounds.
        
        Raises ValueError immediately if query extends outside available coverage (no silent fabrication).
        """
        d_min_lon = data_bounds["min_longitude"]
        d_max_lon = data_bounds["max_longitude"]
        d_min_lat = data_bounds["min_latitude"]
        d_max_lat = data_bounds["max_latitude"]

        # 0.05 degree tolerance for numerical precision
        tol = 0.05
        if (query_bbox.min_lon < (d_min_lon - tol) or
            query_bbox.max_lon > (d_max_lon + tol) or
            query_bbox.min_lat < (d_min_lat - tol) or
            query_bbox.max_lat > (d_max_lat + tol)):
            raise ValueError(
                f"Spatial coverage error: Query bounding box "
                f"[{query_bbox.min_lon:.4f}, {query_bbox.min_lat:.4f}, {query_bbox.max_lon:.4f}, {query_bbox.max_lat:.4f}] "
                f"extends outside CMEMS dataset coverage "
                f"[{d_min_lon:.4f}, {d_min_lat:.4f}, {d_max_lon:.4f}, {d_max_lat:.4f}]."
            )

    def validate_temporal_coverage(
        self,
        query_start: datetime,
        query_end: datetime,
        data_coverage: Dict[str, str],
    ):
        """Validates that the query time range is completely within dataset time limits."""
        q_start = ensure_utc(query_start)
        q_end = ensure_utc(query_end)

        d_start = dt_parser.parse(data_coverage["start_time_utc"]).astimezone(timezone.utc)
        d_end = dt_parser.parse(data_coverage["end_time_utc"]).astimezone(timezone.utc)

        if q_start < d_start or q_end > d_end:
            raise ValueError(
                f"Temporal coverage error: Query time window "
                f"[{q_start.isoformat()} to {q_end.isoformat()}] "
                f"extends outside CMEMS dataset coverage "
                f"[{d_start.isoformat()} to {d_end.isoformat()}]."
            )

    def interpolate_point_velocity(
        self,
        lon: float,
        lat: float,
        grid_points: List[Dict[str, float]],
    ) -> Tuple[float, float]:
        """Performs inverse-distance weighted 2D spatial interpolation across nearest grid nodes.
        
        Interpolation Method:
        Given regular CMEMS grid points {(x_i, y_i, u_i, v_i)}, computes:
            w_i = 1.0 / (dist_i + 1e-6)^2
            u_interp = sum(w_i * u_i) / sum(w_i)
            v_interp = sum(w_i * v_i) / sum(w_i)
        """
        validate_longitude(lon)
        validate_latitude(lat)

        if not grid_points:
            raise ValueError("No grid points available for current vector interpolation.")

        weights: List[float] = []
        u_vals: List[float] = []
        v_vals: List[float] = []

        for pt in grid_points:
            d_lon = lon - pt["lon"]
            d_lat = lat - pt["lat"]
            dist = math.sqrt(d_lon * d_lon + d_lat * d_lat)
            if dist < 1e-5:
                return (pt["u"], pt["v"])
            
            w = 1.0 / (dist * dist)
            weights.append(w)
            u_vals.append(pt["u"])
            v_vals.append(pt["v"])

        total_w = sum(weights)
        if total_w == 0:
            return (u_vals[0], v_vals[0])

        u_out = sum(w * u for w, u in zip(weights, u_vals)) / total_w
        v_out = sum(w * v for w, v in zip(weights, v_vals)) / total_w
        return (round(u_out, 4), round(v_out, 4))

    def fetch_currents(self, query: EnvironmentalQuery) -> Dict[str, Any]:
        """Ingests, validates, and returns canonical CMEMS ocean current models."""
        raw_data = self.load_dataset(self.data_file_path)

        # 1. Strict Boundary Validations
        self.validate_spatial_coverage(query.bbox, raw_data["spatial_bounds"])
        self.validate_temporal_coverage(query.start_time, query.end_time, raw_data["time_coverage"])

        # 2. Extract Sub-Region Mean / Centered Interpolation
        grid_points = raw_data.get("grid_points", [])
        center_lon = (query.bbox.min_lon + query.bbox.max_lon) / 2.0
        center_lat = (query.bbox.min_lat + query.bbox.max_lat) / 2.0
        u_interp, v_interp = self.interpolate_point_velocity(center_lon, center_lat, grid_points)

        speed_mps = math.sqrt(u_interp * u_interp + v_interp * v_interp)
        speed_knots = speed_mps * 1.94384
        dir_deg = (math.degrees(math.atan2(u_interp, v_interp)) + 360.0) % 360.0

        return {
            "dataset_source": raw_data["dataset_source"],
            "data_classification": raw_data.get("data_classification", "OBSERVED_HISTORICAL_REANALYSIS"),
            "product_id": raw_data.get("product_id", "CMEMS_PHY"),
            "reference_timestamp_utc": query.start_time.isoformat(),
            "valid_interval_utc": [query.start_time.isoformat(), query.end_time.isoformat()],
            "spatial_bounds": {
                "min_longitude": query.bbox.min_lon,
                "max_longitude": query.bbox.max_lon,
                "min_latitude": query.bbox.min_lat,
                "max_latitude": query.bbox.max_lat,
            },
            "grid_resolution_deg": raw_data.get("grid_resolution_deg", 0.083),
            "mean_current_vectors": {
                "u_eastward_m_per_s": u_interp,
                "v_northward_m_per_s": v_interp,
                "speed_m_per_s": round(speed_mps, 3),
                "speed_knots": round(speed_knots, 2),
                "direction_deg": round(dir_deg, 1),
            },
            "grid_points": grid_points,
            "interpolation_metadata": {
                "method": "Inverse Distance Weighted (IDW) 2D Grid Interpolation",
                "center_query_point": [round(center_lon, 4), round(center_lat, 4)],
                "interpolated_at": datetime.now(timezone.utc).isoformat(),
            }
        }
