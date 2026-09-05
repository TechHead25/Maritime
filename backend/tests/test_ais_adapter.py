"""Unit and Integration tests for Historical AIS CSV Adapter and Validation Tool."""

from datetime import datetime, timezone
import pytest

from backend.app.models.schemas import VesselTrack, VesselType
from backend.app.providers.ais_adapter import (
    HistoricalAISCSVAdapter,
    map_ais_type_code,
)
from backend.app.providers.base import AISQuery, BoundingBox
from backend.app.providers.synthetic import SyntheticAISProvider
from backend.app.utils.validate_ais_dataset import audit_ais_file


SAMPLE_RAW_CSV = """MMSI,IMO,VesselName,VesselType,BaseDateTime,LAT,LON,SOG,COG,Heading,Status,FlagCountry
371584000,9199347,MT NEW DIAMOND,80,2020-09-02T22:00:00Z,7.3521,82.0124,14.2,48.5,49,under way,Panama
371584000,9199347,MT NEW DIAMOND,80,2020-09-03T00:00:00Z,7.6045,82.2987,13.9,48.2,48,under way,Panama
371584000,9199347,MT NEW DIAMOND,80,2020-09-03T03:25:00Z,8.0298,82.7892,12.1,45.0,45,not under command,Panama
371584000,9199347,MT NEW DIAMOND,80,2020-09-03T08:30:00Z,8.0412,82.8124,0.4,120.0,115,not under command,Panama
353130000,9467419,MSC LAUREN,70,2020-09-03T01:00:00Z,7.2014,82.1054,18.5,52.0,52,under way,Panama
353130000,9467419,MSC LAUREN,70,2020-09-03T03:00:00Z,7.5684,82.5364,18.5,51.8,52,under way,Panama
371584000,9199347,MT NEW DIAMOND,80,2020-09-03T00:00:00Z,7.6045,82.2987,13.9,48.2,48,under way,Panama
999999999,0,TEST BUOY,99,2020-09-03T03:00:00Z,7.5000,82.5000,0.0,0.0,0,stationery,Unknown
371584000,9199347,MT NEW DIAMOND,80,2020-09-03T04:00:00Z,95.0000,82.0000,12.0,45.0,45,under way,Panama
INVALID_MMSI,9199347,CORRUPT SHIP,80,2020-09-03T04:30:00Z,7.8000,82.5000,10.0,45.0,45,under way,Panama
"""


# ---------------------------------------------------------------------------
# 1. Type Code Mapping Tests
# ---------------------------------------------------------------------------

def test_map_ais_type_code():
    assert map_ais_type_code(80) == VesselType.TANKER
    assert map_ais_type_code(89) == VesselType.TANKER
    assert map_ais_type_code("Tanker") == VesselType.TANKER
    assert map_ais_type_code(70) == VesselType.CARGO
    assert map_ais_type_code(74) == VesselType.CARGO
    assert map_ais_type_code("Container Ship") == VesselType.CARGO
    assert map_ais_type_code(31) == VesselType.BUNKER
    assert map_ais_type_code(30) == VesselType.FISHING
    assert map_ais_type_code(60) == VesselType.PASSENGER
    assert map_ais_type_code(99) == VesselType.OTHER
    assert map_ais_type_code(None) == VesselType.OTHER


# ---------------------------------------------------------------------------
# 2. Historical CSV Adapter Unit Tests
# ---------------------------------------------------------------------------

def test_load_from_csv_string_normalization():
    adapter = HistoricalAISCSVAdapter()
    tracks = adapter.load_from_csv_string(SAMPLE_RAW_CSV)

    # Should only create valid vessels: MT NEW DIAMOND (371584000) and MSC LAUREN (353130000)
    assert len(tracks) == 2

    mmsi_map = {t.mmsi: t for t in tracks}
    assert "371584000" in mmsi_map
    assert "353130000" in mmsi_map

    # Validate MT NEW DIAMOND
    nd_track = mmsi_map["371584000"]
    assert nd_track.vessel_name == "MT NEW DIAMOND"
    assert nd_track.vessel_type == VesselType.TANKER
    assert nd_track.flag_country == "Panama"
    # Valid waypoints should be 4 (22:00, 00:00, 03:25, 08:30)
    assert len(nd_track.waypoints) == 4

    # Check chronological ordering
    for i in range(len(nd_track.waypoints) - 1):
        assert nd_track.waypoints[i].timestamp < nd_track.waypoints[i + 1].timestamp

    # Check UTC timezone
    for wp in nd_track.waypoints:
        assert wp.timestamp.tzinfo is not None
        assert wp.latitude <= 90.0
        assert wp.longitude <= 180.0

    # Check AIS Gap detection (> 60 min between 03:25 and 08:30)
    assert nd_track.has_ais_gaps is True
    assert len(nd_track.gap_intervals) >= 1


def test_fetch_vessel_tracks_query_filtering():
    adapter = HistoricalAISCSVAdapter(data_file_path="data/ais/new_diamond_ais_raw.csv")
    query = AISQuery(
        bbox=BoundingBox(min_lon=82.0, min_lat=7.0, max_lon=83.5, max_lat=8.5),
        start_time=datetime(2020, 9, 2, 20, 0, tzinfo=timezone.utc),
        end_time=datetime(2020, 9, 3, 16, 0, tzinfo=timezone.utc),
    )

    tracks = adapter.fetch_vessel_tracks(query)
    assert len(tracks) >= 3
    mmsis = [t.mmsi for t in tracks]
    assert "371584000" in mmsis


# ---------------------------------------------------------------------------
# 3. Preservation of Synthetic Provider
# ---------------------------------------------------------------------------

def test_synthetic_ais_provider_unbroken():
    provider = SyntheticAISProvider()
    query = AISQuery(
        bbox=BoundingBox(min_lon=101.5, min_lat=2.0, max_lon=102.5, max_lat=3.5),
        start_time=datetime(2026, 8, 31, 18, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc),
    )
    tracks = provider.fetch_vessel_tracks(query)
    assert len(tracks) >= 1
    assert isinstance(tracks[0], VesselTrack)


# ---------------------------------------------------------------------------
# 4. Data Validation Script Execution Test
# ---------------------------------------------------------------------------

def test_audit_ais_file_report():
    report = audit_ais_file("data/ais/new_diamond_ais_raw.csv")

    assert report["total_rows_parsed"] == 29
    assert report["valid_positions_count"] == 25
    assert report["rejected_records_count"] == 4
    assert report["unique_mmsi_count"] == 5
    assert report["duplicate_records_count"] == 1
    assert report["invalid_coordinates_count"] == 1
    assert report["invalid_mmsi_count"] == 2
    assert report["time_range"]["duration_hours"] > 0
