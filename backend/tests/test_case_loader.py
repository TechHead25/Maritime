"""Unit tests for the Case Loader service."""

from pathlib import Path
import pytest

from backend.app.models.schemas import VesselType, CaseStatus
from backend.app.services.case_loader import load_case_from_disk, LoadedCase


def test_load_demo_case_001():
    case_dir = Path("data/cases/demo_case_001")
    assert case_dir.exists(), "demo_case_001 directory must exist"

    loaded: LoadedCase = load_case_from_disk(case_dir)

    # 1. Verify InvestigationCase
    assert loaded.case.id == "demo-case-001"
    assert loaded.case.title.startswith("Malacca Strait")
    assert loaded.case.status == CaseStatus.CREATED
    assert loaded.case.region_of_interest is not None
    assert loaded.case.metadata.get("synthetic") is True

    # 2. Verify SARScene
    assert loaded.sar_scene.id == "sar-scene-demo-001"
    assert loaded.sar_scene.case_id == "demo-case-001"
    assert "Sentinel-1A" in loaded.sar_scene.satellite_platform
    assert loaded.sar_scene.pixel_resolution_meters == 10.0

    # 3. Verify SlickDetection
    assert loaded.slick_detection.id == "slick-demo-001"
    assert loaded.slick_detection.area_sq_km == 14.85
    assert loaded.slick_detection.centroid.longitude == 102.14
    assert loaded.slick_detection.centroid.latitude == 2.877
    assert loaded.slick_detection.confidence_score == 0.94

    # 4. Verify VesselTracks (4 Vessels)
    assert len(loaded.vessel_tracks) == 4
    mmsi_map = {v.mmsi: v for v in loaded.vessel_tracks}

    # Vessel A (Culprit Tanker)
    vessel_a = mmsi_map.get("538009912")
    assert vessel_a is not None
    assert vessel_a.vessel_name == "MT PACIFIC GLORY"
    assert vessel_a.vessel_type == VesselType.TANKER
    assert len(vessel_a.waypoints) == 6
    assert vessel_a.has_ais_gaps is True
    assert len(vessel_a.gap_intervals) == 1

    # Vessel B (Wrong Time Cargo)
    vessel_b = mmsi_map.get("352001140")
    assert vessel_b is not None
    assert vessel_b.vessel_name == "MV ATLANTIC TRANSIT"
    assert vessel_b.vessel_type == VesselType.CARGO
    assert len(vessel_b.waypoints) == 3

    # Vessel C (Distant Passenger)
    vessel_c = mmsi_map.get("211889900")
    assert vessel_c is not None
    assert vessel_c.vessel_name == "STAR VOYAGER"
    assert vessel_c.vessel_type == VesselType.PASSENGER

    # Vessel D (AIS Gap Cargo)
    vessel_d = mmsi_map.get("636015522")
    assert vessel_d is not None
    assert vessel_d.vessel_name == "NEPTUNE TRADER"
    assert vessel_d.has_ais_gaps is True

    # 5. Verify Environmental Data
    assert loaded.environment.ocean_currents["synthetic"] is True
    assert "mean_current_vectors" in loaded.environment.ocean_currents
    assert loaded.environment.wind_data["synthetic"] is True
    assert "mean_wind_vectors" in loaded.environment.wind_data


def test_load_case_nonexistent_directory():
    with pytest.raises(FileNotFoundError):
        load_case_from_disk("data/cases/non_existent_folder_xyz")


def test_load_case_missing_required_file(tmp_path):
    # Empty directory missing case.json
    with pytest.raises(FileNotFoundError, match="Missing case.json"):
        load_case_from_disk(tmp_path)
