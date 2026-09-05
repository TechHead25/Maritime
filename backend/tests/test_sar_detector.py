"""Unit and Integration tests for the SAR Oil-Spill Detection and Lookalike Discrimination Subsystem."""

from datetime import datetime, timezone
import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import (
    SARScene,
    SlickDetection,
    SARLookalikeClass,
    SARFeatureVector,
    SARCandidatePatch,
)
from backend.app.services.sar_detector import (
    BaseSARDetector,
    BaseSARClassifier,
    ExplainableRuleSARClassifier,
    DeterministicSARDetector,
    DetectorConfig,
    SARRaster,
    SyntheticSARGenerator,
)

client = TestClient(app)


@pytest.fixture
def synthetic_sar_scene():
    """Generates a reproducible synthetic SAR raster."""
    return SyntheticSARGenerator.create_synthetic_scene(
        width=250,
        height=250,
        seed=42,
    )


@pytest.fixture
def mock_sar_scene_metadata():
    """Returns a valid SARScene metadata object."""
    return SARScene(
        id="sar-scene-synthetic-001",
        case_id="case-test-sar-001",
        satellite_platform="Sentinel-1A (Synthetic SAR)",
        sensor_mode="IW",
        polarization="VV",
        acquisition_timestamp=datetime(2026, 9, 1, 14, 30, tzinfo=timezone.utc),
        pixel_resolution_meters=20.0,
    )


# ---------------------------------------------------------------------------
# 1. Synthetic Generator Tests
# ---------------------------------------------------------------------------

def test_synthetic_sar_generator_structure(synthetic_sar_scene):
    assert synthetic_sar_scene.data_db.shape == (250, 250)
    assert synthetic_sar_scene.pixel_resolution_meters > 0
    assert synthetic_sar_scene.acquisition_timestamp.tzinfo is not None
    # Verify sea clutter average backscatter is around -14 dB
    mean_val = np.mean(synthetic_sar_scene.data_db)
    assert -20.0 < mean_val < -10.0


# ---------------------------------------------------------------------------
# 2. Preprocessing & Speckle Filter Tests
# ---------------------------------------------------------------------------

def test_speckle_filter_reduces_variance(synthetic_sar_scene):
    detector = DeterministicSARDetector()
    raw = synthetic_sar_scene.data_db
    filtered = detector.preprocess_speckle_filter(raw, window_size=5)

    assert filtered.shape == raw.shape
    # Filtered image should have lower standard deviation than raw noisy speckle
    assert np.std(filtered) < np.std(raw)


# ---------------------------------------------------------------------------
# 3. Land Masking Tests
# ---------------------------------------------------------------------------

def test_land_masking_island_detection(synthetic_sar_scene):
    detector = DeterministicSARDetector()
    land_mask = detector.create_land_mask(synthetic_sar_scene.data_db, threshold_db=-6.0)

    assert land_mask.shape == synthetic_sar_scene.data_db.shape
    assert land_mask.dtype == bool
    # Top-left island region should have True values in mask
    assert np.any(land_mask[:80, :80])
    # Open ocean region should be False
    assert not np.all(land_mask[100:150, 150:200])


# ---------------------------------------------------------------------------
# 4. Feature Extraction & Lookalike Rejection Auditing
# ---------------------------------------------------------------------------

def test_candidate_extraction_and_rejection_reasons(synthetic_sar_scene, mock_sar_scene_metadata):
    detector = DeterministicSARDetector()
    candidates = detector.extract_candidates(mock_sar_scene_metadata, synthetic_sar_scene)

    assert len(candidates) >= 1

    # Check for accepted mineral oil slick
    accepted = [c for c in candidates if c.is_accepted]
    assert len(accepted) >= 1
    top_slick = accepted[0]
    assert top_slick.classification == SARLookalikeClass.MINERAL_OIL
    assert top_slick.rejection_reason is None
    assert top_slick.confidence_score >= 0.60
    assert top_slick.features.mean_contrast_db >= 3.5

    # Check for rejected lookalikes if present
    rejected = [c for c in candidates if not c.is_accepted]
    for r in rejected:
        assert r.rejection_reason is not None
        assert len(r.rejection_reason) > 10
        assert r.lookalike_probability >= 0.60


# ---------------------------------------------------------------------------
# 5. Classifier Isolation Unit Tests
# ---------------------------------------------------------------------------

def test_explainable_classifier_rejection_branches():
    classifier = ExplainableRuleSARClassifier()

    # Case A: Low-wind lookalike due to huge surface area (> 150 km2)
    features_low_wind = SARFeatureVector(
        area_sq_km=210.0,
        perimeter_km=60.0,
        compactness=1.8,
        elongation_ratio=1.4,
        major_axis_orientation_deg=40.0,
        mean_contrast_db=4.5,
        std_dev_db=1.0,
        coeff_of_variation=0.08,
        edge_gradient_db_per_pixel=0.7,
        min_backscatter_db=-22.0,
        distance_to_land_km=15.0,
    )
    cls, is_acc, conf, lk_prob, reason = classifier.classify(features_low_wind)
    assert cls == SARLookalikeClass.LOOKALIKE_LOW_WIND
    assert is_acc is False
    assert "exceeds maximum" in reason.lower()

    # Case B: Biogenic lookalike due to weak damping contrast (< 3.5 dB)
    features_biogenic = SARFeatureVector(
        area_sq_km=8.5,
        perimeter_km=11.0,
        compactness=1.1,
        elongation_ratio=1.1,
        major_axis_orientation_deg=0.0,
        mean_contrast_db=1.9,  # Very weak damping
        std_dev_db=0.9,
        coeff_of_variation=0.06,
        edge_gradient_db_per_pixel=0.6,
        min_backscatter_db=-17.0,
        distance_to_land_km=10.0,
    )
    cls, is_acc, conf, lk_prob, reason = classifier.classify(features_biogenic)
    assert cls == SARLookalikeClass.LOOKALIKE_BIOGENIC
    assert is_acc is False
    assert "damping contrast" in reason.lower()

    # Case C: Coastal shadow near land (< 1.2 km)
    features_coastal = SARFeatureVector(
        area_sq_km=4.0,
        perimeter_km=9.0,
        compactness=1.5,
        elongation_ratio=2.0,
        major_axis_orientation_deg=30.0,
        mean_contrast_db=6.0,
        std_dev_db=1.1,
        coeff_of_variation=0.09,
        edge_gradient_db_per_pixel=1.1,
        min_backscatter_db=-24.0,
        distance_to_land_km=0.5,  # Very close to coast
    )
    cls, is_acc, conf, lk_prob, reason = classifier.classify(features_coastal)
    assert cls == SARLookalikeClass.LOOKALIKE_COASTAL_SHADOW
    assert is_acc is False
    assert "coastal shadow" in reason.lower()


# ---------------------------------------------------------------------------
# 6. Primary Slick Detection End-to-End Tests
# ---------------------------------------------------------------------------

def test_detect_primary_slick_success(synthetic_sar_scene, mock_sar_scene_metadata):
    detector = DeterministicSARDetector()
    detection: SlickDetection = detector.detect_primary_slick(
        scene=mock_sar_scene_metadata,
        raster=synthetic_sar_scene,
    )

    assert isinstance(detection, SlickDetection)
    assert detection.sar_scene_id == mock_sar_scene_metadata.id
    assert detection.area_sq_km > 1.0
    assert detection.confidence_score >= 0.60
    assert detection.lookalike_probability <= 0.40
    # Centroid coordinates within reasonable bounding box
    lon, lat = detection.centroid.coordinates
    assert 101.5 <= lon <= 103.0
    assert 2.0 <= lat <= 4.0
    # Closed polygon
    ring = detection.slick_polygon.coordinates[0]
    assert len(ring) >= 4
    assert ring[0] == ring[-1]


# ---------------------------------------------------------------------------
# 7. Candidate Collection API Endpoint Test
# ---------------------------------------------------------------------------

def test_api_get_sar_candidates():
    response = client.get("/api/cases/demo-case-001/sar-candidates")
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "demo-case-001"
    assert data["total_candidates"] >= 1
    assert data["accepted_count"] >= 1
    assert len(data["accepted_slicks"]) >= 1

    # Check classifier metadata disclaimer
    meta = data["classifier_metadata"]
    assert "DECISION_SUPPORT_BASELINE" in meta["scientific_status"]
    assert "limitations_note" in meta


def test_api_get_sar_candidates_case_not_found():
    response = client.get("/api/cases/non-existent-case-id/sar-candidates")
    assert response.status_code == 404
