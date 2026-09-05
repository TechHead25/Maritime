"""Real Historical AIS Data Adapter.

Parses, validates, normalizes, and transforms raw AIS CSV/JSON datasets into canonical
VesselTrack models with chronological waypoints, transponder gap analysis, and strict audit logging.
"""

import csv
from datetime import datetime, timezone
import io
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from dateutil import parser as dt_parser

from backend.app.models.schemas import (
    VesselPosition,
    VesselTrack,
    VesselType,
    ensure_utc,
    validate_latitude,
    validate_longitude,
    validate_mmsi,
)
from backend.app.providers.base import AISDataProvider, AISQuery

logger = logging.getLogger("maritime-oil-attribution.providers.ais")


# ---------------------------------------------------------------------------
# AIS Numeric Code to Canonical VesselType Mapping (ITU-R M.1371)
# ---------------------------------------------------------------------------

def map_ais_type_code(raw_type: Any) -> VesselType:
    """Maps ITU-R M.1371 numeric AIS ship type codes to canonical VesselType enum."""
    if raw_type is None:
        return VesselType.OTHER
    
    # If already a string representation
    s_val = str(raw_type).strip().upper()
    if "TANKER" in s_val:
        return VesselType.TANKER
    elif "CARGO" in s_val or "CONTAINER" in s_val or "BULK" in s_val:
        return VesselType.CARGO
    elif "BUNKER" in s_val or "TUG" in s_val or "SUPPLY" in s_val:
        return VesselType.BUNKER
    elif "FISHING" in s_val:
        return VesselType.FISHING
    elif "PASSENGER" in s_val or "FERRY" in s_val or "CRUISE" in s_val:
        return VesselType.PASSENGER

    try:
        code = int(float(raw_type))
        if 80 <= code <= 89:
            return VesselType.TANKER
        elif 70 <= code <= 79:
            return VesselType.CARGO
        elif code in (31, 32, 52):
            return VesselType.BUNKER
        elif code == 30:
            return VesselType.FISHING
        elif 60 <= code <= 69:
            return VesselType.PASSENGER
        else:
            return VesselType.OTHER
    except (ValueError, TypeError):
        return VesselType.OTHER


# ---------------------------------------------------------------------------
# Historical AIS CSV/JSON Adapter
# ---------------------------------------------------------------------------

class HistoricalAISCSVAdapter(AISDataProvider):
    """Data adapter for loading and validating historical AIS CSV data files."""

    def __init__(self, data_file_path: Optional[str] = None):
        self.data_file_path = data_file_path

    def parse_timestamp(self, raw_ts: str) -> datetime:
        """Parses various date string formats and strictly ensures UTC."""
        dt = dt_parser.parse(str(raw_ts))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def load_from_csv(self, file_path: str) -> List[VesselTrack]:
        """Loads and converts raw AIS CSV rows into validated VesselTrack entities."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"AIS CSV file not found at path: '{file_path}'")

        with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return self.load_from_csv_string(content, source_name=file_path)

    def load_from_csv_string(self, csv_text: str, source_name: str = "memory") -> List[VesselTrack]:
        """Parses CSV text, filters invalid rows, groups by MMSI, and constructs VesselTrack objects."""
        reader = csv.DictReader(io.StringIO(csv_text))
        
        # Intermediate storage grouped by MMSI
        vessel_meta: Dict[str, Dict[str, Any]] = {}
        vessel_waypoints: Dict[str, List[VesselPosition]] = {}
        seen_timestamps: Dict[str, Set[str]] = {}

        rejected_rows = 0

        for row_idx, row in enumerate(reader, start=2):
            # 1. Normalize Column Keys
            norm_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            # 2. Extract & Validate MMSI
            raw_mmsi = norm_row.get("mmsi")
            if not raw_mmsi:
                rejected_rows += 1
                continue
            
            # Clean MMSI
            raw_mmsi = re.sub(r"[^\d]", "", raw_mmsi)
            if len(raw_mmsi) != 9 or raw_mmsi.startswith("0") or raw_mmsi == "999999999":
                rejected_rows += 1
                continue

            # 3. Extract & Validate Coordinates
            raw_lat = norm_row.get("lat") or norm_row.get("latitude")
            raw_lon = norm_row.get("lon") or norm_row.get("longitude") or norm_row.get("long")
            if not raw_lat or not raw_lon:
                rejected_rows += 1
                continue

            try:
                lat = float(raw_lat)
                lon = float(raw_lon)
                validate_latitude(lat)
                validate_longitude(lon)
            except (ValueError, TypeError):
                rejected_rows += 1
                continue

            # 4. Extract & Normalize UTC Timestamp
            raw_ts = norm_row.get("basedatetime") or norm_row.get("timestamp") or norm_row.get("date_time_utc") or norm_row.get("time")
            if not raw_ts:
                rejected_rows += 1
                continue

            try:
                ts_utc = self.parse_timestamp(raw_ts)
            except Exception:
                rejected_rows += 1
                continue

            # 5. Check duplicate ping for the same MMSI and timestamp
            ts_iso = ts_utc.isoformat()
            if raw_mmsi not in seen_timestamps:
                seen_timestamps[raw_mmsi] = set()
            if ts_iso in seen_timestamps[raw_mmsi]:
                # Duplicate ping; ignore
                continue
            seen_timestamps[raw_mmsi].add(ts_iso)

            # 6. SOG and COG
            sog = None
            raw_sog = norm_row.get("sog") or norm_row.get("speed") or norm_row.get("speed_over_ground_knots")
            if raw_sog:
                try:
                    sog_val = float(raw_sog)
                    if 0.0 <= sog_val <= 102.2:
                        sog = sog_val
                except ValueError:
                    pass

            cog = None
            raw_cog = norm_row.get("cog") or norm_row.get("course") or norm_row.get("course_over_ground_deg")
            if raw_cog:
                try:
                    cog_val = float(raw_cog)
                    if 0.0 <= cog_val <= 360.0:
                        cog = cog_val
                except ValueError:
                    pass

            nav_status = norm_row.get("status") or norm_row.get("navigationalstatus") or norm_row.get("nav_status") or "under way using engine"

            # 7. Store metadata
            if raw_mmsi not in vessel_meta:
                v_name = norm_row.get("vessel_name") or norm_row.get("vesselname") or norm_row.get("name") or f"VESSEL-{raw_mmsi}"
                raw_type = norm_row.get("vessel_type") or norm_row.get("vesseltype") or norm_row.get("type") or norm_row.get("shiptype")
                v_type = map_ais_type_code(raw_type)
                flag = norm_row.get("flagcountry") or norm_row.get("flag") or "Unknown"

                vessel_meta[raw_mmsi] = {
                    "vessel_name": v_name,
                    "vessel_type": v_type,
                    "flag_country": flag,
                }
                vessel_waypoints[raw_mmsi] = []

            wp = VesselPosition(
                timestamp=ts_utc,
                longitude=round(lon, 6),
                latitude=round(lat, 6),
                speed_over_ground_knots=sog if sog is not None else 0.0,
                course_over_ground_deg=cog if cog is not None else 0.0,
                navigational_status=nav_status,
            )
            vessel_waypoints[raw_mmsi].append(wp)

        logger.info(f"Loaded AIS data from '{source_name}': {len(vessel_meta)} vessels, {rejected_rows} invalid rows rejected.")

        # 8. Construct VesselTrack models with chronological sorting and gap detection
        tracks: List[VesselTrack] = []
        for mmsi, meta in vessel_meta.items():
            wps = vessel_waypoints[mmsi]
            if len(wps) == 0:
                continue

            # Sort chronologically
            wps.sort(key=lambda x: x.timestamp)

            # Detect AIS Gaps (> 60 minutes)
            has_gaps = False
            gap_intervals: List[Tuple[str, str]] = []

            for i in range(len(wps) - 1):
                delta_sec = (wps[i + 1].timestamp - wps[i].timestamp).total_seconds()
                if delta_sec > 3600.0:  # > 60 minutes
                    has_gaps = True
                    gap_intervals.append((wps[i].timestamp.isoformat(), wps[i + 1].timestamp.isoformat()))

            track = VesselTrack(
                id=f"trk-{mmsi}",
                mmsi=mmsi,
                vessel_name=meta["vessel_name"],
                vessel_type=meta["vessel_type"],
                flag_country=meta["flag_country"],
                waypoints=wps,
                has_ais_gaps=has_gaps,
                gap_intervals=gap_intervals,
            )
            tracks.append(track)

        return tracks

    def fetch_vessel_tracks(self, query: AISQuery) -> List[VesselTrack]:
        """Loads and filters vessel tracks matching the query bounding box and time envelope."""
        file_path = self.data_file_path or "data/ais/new_diamond_ais_raw.csv"
        all_tracks = self.load_from_csv(file_path)

        filtered: List[VesselTrack] = []
        for track in all_tracks:
            # Filter waypoints within query spatiotemporal window
            matching_wps = [
                wp for wp in track.waypoints
                if query.bbox.min_lon <= wp.longitude <= query.bbox.max_lon
                and query.bbox.min_lat <= wp.latitude <= query.bbox.max_lat
                and query.start_time <= wp.timestamp <= query.end_time
            ]

            if len(matching_wps) >= 2:
                # Reconstruct track with matching window waypoints
                filtered_track = VesselTrack(
                    id=track.id,
                    mmsi=track.mmsi,
                    vessel_name=track.vessel_name,
                    vessel_type=track.vessel_type,
                    flag_country=track.flag_country,
                    waypoints=matching_wps,
                    has_ais_gaps=track.has_ais_gaps,
                    gap_intervals=track.gap_intervals,
                )
                filtered.append(filtered_track)
            elif len(track.waypoints) >= 2 and not query.bbox:
                filtered.append(track)

        return filtered if filtered else all_tracks
