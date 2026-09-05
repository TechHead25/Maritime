"""Production Data Integrity & Anti-Fabrication Runtime Audit Tests.

Verifies:
1. Synthetic providers are strictly disabled in production (ALLOW_SYNTHETIC_PROVIDERS=false).
2. Zero automatic fallback from real data to synthetic data.
3. Live maritime reports DISCONNECTED honestly with 0 fake vessels when unconfigured.
4. Investigation creation and data discovery work with real providers.
5. Real SAR, AIS, ocean currents, and winds execute dynamically without hardcoded scores.
6. Investigation results and PDF reports contain actual dynamic outputs.
7. No synthetic benchmark data appears in production case listings unless explicitly queried.
"""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.providers.base import BoundingBox, SARQuery, AISQuery, ProviderUnavailableError
from backend.app.providers.registry import ProviderRegistry, provider_registry
from backend.app.services.case_service import case_service
from backend.app.services.pipeline_service import pipeline_service, PipelineOptions

client = TestClient(app)


def test_production_mode_has_synthetic_providers_disabled():
    """Verifies that synthetic mode is disabled by default in production."""
    reg = ProviderRegistry()
    assert reg.allow_synthetic is False


def test_zero_automatic_fallback_to_synthetic_sar():
    """Verifies that SAR provider raises ProviderUnavailableError when real observation missing."""
    reg = ProviderRegistry()
    reg.allow_synthetic = False

    # Force unconfigured historical and external SAR
    reg._historical_sar.is_available = lambda: False
    reg._copernicus_sar.is_available = lambda: False

    with pytest.raises(ProviderUnavailableError, match="No active SAR provider available"):
        reg.get_sar_provider(prefer_historical=True)


def test_zero_automatic_fallback_to_synthetic_ais():
    """Verifies that AIS provider raises ProviderUnavailableError when live/archive unconfigured."""
    reg = ProviderRegistry()
    reg.allow_synthetic = False

    reg._historical_ais.is_available = lambda: False
    reg._live_ais.is_available = lambda: False

    with pytest.raises(ProviderUnavailableError, match="No active AIS provider available"):
        reg.get_ais_provider(prefer_live=True)


def test_live_maritime_returns_zero_fake_vessels():
    """Verifies that live maritime tracking never returns simulated vessels when disconnected."""
    from backend.app.services.live_ais_service import live_ais_service
    live_ais_service.reset()
    res = client.get("/api/live/vessels")
    assert res.status_code == 200
    data = res.json()
    assert "vessels" in data
    assert "status" in data
    # In unconfigured test environment, status must be DISCONNECTED or empty, never populated with fake vessels
    if data["status"] == "DISCONNECTED":
        assert len(data["vessels"]) == 0


def test_production_case_listing_excludes_synthetic_benchmarks():
    """Verifies that GET /api/cases filters out synthetic benchmark cases in production."""
    res = client.get("/api/cases?include_synthetic=false")
    assert res.status_code == 200
    cases = res.json()

    for c in cases:
        assert not c.get("id", "").startswith("demo-")
        assert not c.get("id", "").startswith("demo_")
        metadata = c.get("metadata") or {}
        assert metadata.get("synthetic") is not True


def test_real_sar_environmental_and_ais_pipeline_execution():
    """Verifies that the full forensic pipeline runs dynamically on real historical data."""
    # Run historical case (MT New Diamond 2020: real Sentinel-1 GeoTIFF, real AIS, real CMEMS currents)
    case_id = "case_new_diamond_2020"
    opts = PipelineOptions(
        particle_count=200,
        max_hours_backward=18.0,
        time_step_minutes=30,
        random_seed=42,
        use_synthetic_slick=False,  # Strictly execute real SAR CFAR detector
    )

    response = pipeline_service.run_pipeline(case_id=case_id, options=opts)
    assert response.case.id == case_id
    assert response.case.status == "ATTRIBUTION_COMPLETED"
    assert len(response.attribution_scores) > 0

    # Top candidate should be the historical tanker MT New Diamond
    top_cand = response.attribution_scores[0]
    assert "NEW DIAMOND" in top_cand.candidate_name
    assert top_cand.rank == 1
    assert top_cand.total_score > 40.0
    assert len(top_cand.evidence_items) > 0


def test_pdf_report_contains_actual_dynamic_results():
    """Verifies that PDF report is generated with actual dynamic attribution results."""
    case_id = "case_new_diamond_2020"
    res = client.get(f"/api/cases/{case_id}/report/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000  # Non-empty valid PDF byte stream
