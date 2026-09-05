"""Standalone AIS Data Validation and Quality Audit Tool.

Inspects raw historical AIS CSV datasets and generates a structured audit report detailing:
- Total records and unique vessel count (MMSIs)
- Valid vs rejected position counts
- Spatiotemporal bounding envelope (Time range, Bounding box)
- Missing / null value counts per field
- Duplicate records (identical MMSI and timestamp)
- Out-of-bounds / invalid coordinates
- Detailed anomaly logs without silent repair
"""

import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Set, Tuple

from dateutil import parser as dt_parser


def audit_ais_file(file_path: str) -> Dict[str, Any]:
    """Performs a comprehensive data validation audit on a raw AIS CSV file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"AIS file not found: '{file_path}'")

    report: Dict[str, Any] = {
        "file_analyzed": file_path,
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_rows_parsed": 0,
        "valid_positions_count": 0,
        "rejected_records_count": 0,
        "unique_mmsi_count": 0,
        "unique_vessels": [],
        "time_range": {
            "earliest_timestamp_utc": None,
            "latest_timestamp_utc": None,
            "duration_hours": 0.0,
        },
        "geographic_bounds": {
            "min_longitude": None,
            "max_longitude": None,
            "min_latitude": None,
            "max_latitude": None,
        },
        "missing_values_count": {
            "mmsi": 0,
            "latitude": 0,
            "longitude": 0,
            "timestamp": 0,
            "speed_over_ground": 0,
            "course_over_ground": 0,
            "vessel_name": 0,
            "vessel_type": 0,
        },
        "duplicate_records_count": 0,
        "invalid_coordinates_count": 0,
        "invalid_mmsi_count": 0,
        "rejection_audit_log": [],
    }

    seen_pings: Set[Tuple[str, str]] = set()
    vessel_mmsis: Set[str] = set()
    vessel_names: Dict[str, str] = {}
    timestamps: List[datetime] = []
    lons: List[float] = []
    lats: List[float] = []

    with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=2):
            report["total_rows_parsed"] += 1
            norm_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            reasons: List[str] = []

            # 1. MMSI Audit
            raw_mmsi = norm_row.get("mmsi")
            clean_mmsi = None
            if not raw_mmsi:
                report["missing_values_count"]["mmsi"] += 1
                reasons.append("Missing MMSI value")
            else:
                clean_mmsi = re.sub(r"[^\d]", "", raw_mmsi)
                if len(clean_mmsi) != 9 or clean_mmsi.startswith("0") or clean_mmsi == "999999999":
                    report["invalid_mmsi_count"] += 1
                    reasons.append(f"Invalid/Test MMSI code '{raw_mmsi}' (expected 9 digits)")

            # 2. Coordinates Audit
            raw_lat = norm_row.get("lat") or norm_row.get("latitude")
            raw_lon = norm_row.get("lon") or norm_row.get("longitude") or norm_row.get("long")
            lat_val, lon_val = None, None

            if not raw_lat:
                report["missing_values_count"]["latitude"] += 1
                reasons.append("Missing latitude coordinate")
            if not raw_lon:
                report["missing_values_count"]["longitude"] += 1
                reasons.append("Missing longitude coordinate")

            if raw_lat and raw_lon:
                try:
                    lat_val = float(raw_lat)
                    lon_val = float(raw_lon)
                    if not (-90.0 <= lat_val <= 90.0) or not (-180.0 <= lon_val <= 180.0):
                        report["invalid_coordinates_count"] += 1
                        reasons.append(f"Out-of-bounds coordinates: Lat={lat_val}, Lon={lon_val}")
                except (ValueError, TypeError):
                    report["invalid_coordinates_count"] += 1
                    reasons.append(f"Non-numeric coordinates: Lat='{raw_lat}', Lon='{raw_lon}'")

            # 3. Timestamp Audit
            raw_ts = norm_row.get("basedatetime") or norm_row.get("timestamp") or norm_row.get("date_time_utc") or norm_row.get("time")
            ts_val = None
            if not raw_ts:
                report["missing_values_count"]["timestamp"] += 1
                reasons.append("Missing timestamp")
            else:
                try:
                    ts_val = dt_parser.parse(str(raw_ts))
                    if ts_val.tzinfo is None:
                        ts_val = ts_val.replace(tzinfo=timezone.utc)
                    ts_val = ts_val.astimezone(timezone.utc)
                except Exception:
                    reasons.append(f"Unparseable datetime format: '{raw_ts}'")

            # 4. SOG / COG Null Checks
            if not norm_row.get("sog") and not norm_row.get("speed"):
                report["missing_values_count"]["speed_over_ground"] += 1
            if not norm_row.get("cog") and not norm_row.get("course"):
                report["missing_values_count"]["course_over_ground"] += 1
            if not norm_row.get("vesselname") and not norm_row.get("name"):
                report["missing_values_count"]["vessel_name"] += 1
            if not norm_row.get("vesseltype") and not norm_row.get("type"):
                report["missing_values_count"]["vessel_type"] += 1

            # 5. Duplicate Check
            if clean_mmsi and ts_val:
                ping_key = (clean_mmsi, ts_val.isoformat())
                if ping_key in seen_pings:
                    report["duplicate_records_count"] += 1
                    reasons.append(f"Duplicate ping for MMSI {clean_mmsi} at timestamp {ts_val.isoformat()}")
                else:
                    seen_pings.add(ping_key)

            # Record Decision
            if reasons:
                report["rejected_records_count"] += 1
                if len(report["rejection_audit_log"]) < 50:
                    report["rejection_audit_log"].append({
                        "row_index": row_idx,
                        "raw_data": row,
                        "rejection_reasons": reasons,
                    })
            else:
                report["valid_positions_count"] += 1
                vessel_mmsis.add(clean_mmsi)
                v_name = norm_row.get("vesselname") or norm_row.get("name") or clean_mmsi
                vessel_names[clean_mmsi] = v_name
                timestamps.append(ts_val)
                lons.append(lon_val)
                lats.append(lat_val)

    # Summarize Bounds & Vessels
    report["unique_mmsi_count"] = len(vessel_mmsis)
    report["unique_vessels"] = [{"mmsi": m, "vessel_name": vessel_names[m]} for m in sorted(vessel_mmsis)]

    if timestamps:
        t_min = min(timestamps)
        t_max = max(timestamps)
        report["time_range"]["earliest_timestamp_utc"] = t_min.isoformat()
        report["time_range"]["latest_timestamp_utc"] = t_max.isoformat()
        report["time_range"]["duration_hours"] = round((t_max - t_min).total_seconds() / 3600.0, 2)

    if lons and lats:
        report["geographic_bounds"]["min_longitude"] = round(min(lons), 4)
        report["geographic_bounds"]["max_longitude"] = round(max(lons), 4)
        report["geographic_bounds"]["min_latitude"] = round(min(lats), 4)
        report["geographic_bounds"]["max_latitude"] = round(max(lats), 4)

    return report


def print_audit_summary(report: Dict[str, Any]):
    """Pretty prints the validation audit summary to stdout."""
    print("=" * 70)
    print("  MARITIME AIS DATASET VALIDATION & INTEGRITY AUDIT REPORT")
    print("=" * 70)
    print(f"File Path:                {report['file_analyzed']}")
    print(f"Audit Timestamp (UTC):    {report['audit_timestamp_utc']}")
    print(f"Total Rows Ingested:      {report['total_rows_parsed']}")
    print(f"Valid Position Reports:   {report['valid_positions_count']}")
    print(f"Rejected Invalid Rows:    {report['rejected_records_count']}")
    print(f"Unique Vessels (MMSIs):   {report['unique_mmsi_count']}")
    print("-" * 70)
    print("TIME ENVELOPE (UTC):")
    print(f"  Earliest Timestamp:     {report['time_range']['earliest_timestamp_utc']}")
    print(f"  Latest Timestamp:       {report['time_range']['latest_timestamp_utc']}")
    print(f"  Span Duration:          {report['time_range']['duration_hours']} hours")
    print("-" * 70)
    print("GEOGRAPHIC BOUNDING BOX:")
    print(f"  Longitude:              [{report['geographic_bounds']['min_longitude']}°E, {report['geographic_bounds']['max_longitude']}°E]")
    print(f"  Latitude:               [{report['geographic_bounds']['min_latitude']}°N, {report['geographic_bounds']['max_latitude']}°N]")
    print("-" * 70)
    print("DATA QUALITY AUDIT:")
    print(f"  Duplicate Records:      {report['duplicate_records_count']}")
    print(f"  Invalid Coordinates:    {report['invalid_coordinates_count']}")
    print(f"  Invalid/Test MMSIs:     {report['invalid_mmsi_count']}")
    print(f"  Missing SOG/COG:        {report['missing_values_count']['speed_over_ground']} / {report['missing_values_count']['course_over_ground']}")
    print("-" * 70)
    print("UNIQUE VESSELS IDENTIFIED:")
    for v in report["unique_vessels"]:
        print(f"  • MMSI: {v['mmsi']} | Vessel: {v['vessel_name']}")
    print("=" * 70)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/ais/new_diamond_ais_raw.csv"
    rep = audit_ais_file(target)
    print_audit_summary(rep)
