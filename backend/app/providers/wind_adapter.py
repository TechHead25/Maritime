"""Real Historical Surface Wind Data Adapter (ECMWF ERA5 Reanalysis).

Ingests ECMWF ERA5 hourly surface wind velocity datasets (u10, v10 in m/s),
enforces strict spatial and temporal coverage boundaries, performs 2D spatial interpolation,
and returns canonical wind models for the Lagrangian backward drift simulation.
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
from backend.app.providers.base import BoundingBox, EnvironmentalQuery, WindDataProvider

logger = logging.getLogger("maritime-oil-attribution.providers.wind")


class HistoricalWindAdapter(WindDataProvider):
    """Adapter for historical ECMWF ERA5 hourly surface wind reanalysis datasets."""

    def __init__(self, data_file_path: Optional[str] = None):
        self.data_file_path = data_file_path or "data/wind/new_diamond_wind_era5.json"

    def load_dataset(self, file_path: str) -> Dict[str, Any]:
        """Loads and parses the raw JSON / NetCDF abstraction dataset file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Wind data file not found: '{file_path}'")

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

        tol = 0.05
        if (query_bbox.min_lon < (d_min_lon - tol) or
            query_bbox.max_lon > (d_max_lon + tol) or
            query_bbox.min_lat < (d_min_lat - tol) or
            query_bbox.max_lat > (d_max_lat + tol)):
            raise ValueError(
                f"Spatial coverage error: Query bounding box "
                f"[{query_bbox.min_lon:.4f}, {query_bbox.min_lat:.4f}, {query_bbox.max_lon:.4f}, {query_bbox.max_lat:.4f}] "
                f"extends outside ERA5 dataset coverage "
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
                f"extends outside ERA5 dataset coverage "
                f"[{d_start.isoformat()} to {d_end.isoformat()}]."
            )

    def interpolate_point_wind(
        self,
        lon: float,
        lat: float,
        grid_points: List[Dict[str, float]],
    ) -> Tuple[float, float]:
        """Performs inverse-distance weighted 2D spatial interpolation across nearest ERA5 grid nodes."""
        validate_longitude(lon)
        validate_latitude(lat)

        if not grid_points:
            raise ValueError("No grid points available for wind vector interpolation.")

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
        return (round(u_out, 3), round(v_out, 3))

    def fetch_winds(self, query: EnvironmentalQuery) -> Dict[str, Any]:
        """Ingests, validates, and returns canonical ECMWF ERA5 surface wind models."""
        raw_data = self.load_dataset(self.data_file_path)

        # 1. Strict Boundary Validations
        self.validate_spatial_coverage(query.bbox, raw_data["spatial_bounds"])
        self.validate_temporal_coverage(query.start_time, query.end_time, raw_data["time_coverage"])

        # 2. Extract Sub-Region Mean / Centered Interpolation
        grid_points = raw_data.get("grid_points", [])
        center_lon = (query.bbox.min_lon + query.bbox.max_lon) / 2.0
        center_lat = (query.bbox.min_lat + query.bbox.max_lat) / 2.0
        u_interp, v_interp = self.interpolate_point_wind(center_lon, center_lat, grid_points)

        speed_mps = math.sqrt(u_interp * u_interp + v_interp * v_interp)
        speed_knots = speed_mps * 1.94384
        # Meteorological "from" wind direction convention: Direction wind blows from
        dir_from_deg = (math.degrees(math.atan2(-u_interp, -v_interp)) + 360.0) % 360.0

        return {
            "dataset_source": raw_data["dataset_source"],
            "data_classification": raw_data.get("data_classification", "OBSERVED_HISTORICAL_REANALYSIS"),
            "product_id": raw_data.get("product_id", "ERA5_HOURLY"),
            "reference_timestamp_utc": query.start_time.isoformat(),
            "valid_interval_utc": [query.start_time.isoformat(), query.end_time.isoformat()],
            "spatial_bounds": {
                "min_longitude": query.bbox.min_lon,
                "max_longitude": query.bbox.max_lon,
                "min_latitude": query.bbox.min_lat,
                "max_latitude": query.bbox.max_lat,
            },
            "grid_resolution_deg": raw_data.get("grid_resolution_deg", 0.25),
            "mean_wind_vectors": {
                "u_eastward_m_per_s": u_interp,
                "v_northward_m_per_s": v_interp,
                "wind_speed_m_per_s": round(speed_mps, 2),
                "wind_speed_knots": round(speed_knots, 2),
                "wind_direction_from_deg": round(dir_from_deg, 1),
            },
            "wind_leeway_factor_recommended": raw_data.get("wind_leeway_factor_recommended", 0.03),
            "interpolation_metadata": {
                "method": "Inverse Distance Weighted (IDW) 2D Grid Interpolation",
                "center_query_point": [round(center_lon, 4), round(center_lat, 4)],
                "interpolated_at": datetime.now(timezone.utc).isoformat(),
            }
        }
