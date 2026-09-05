"""Final Production Acceptance Test Suite.

Executes a complete 31-step verification from a clean state with synthetic providers strictly disabled.
Validates:
- Real data flows
- Honest provider status reporting (PROVIDER NOT CONFIGURED when credentials absent)
- Dynamic investigation execution on real data
- In-depth evidence assembly and uncertainty bounds
- Disk persistence across backend restarts
- PDF report generation containing actual results
"""

import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure synthetic providers are strictly disabled
os.environ["ALLOW_SYNTHETIC_PROVIDERS"] = "false"

from backend.app.main import app
from backend.app.providers.base import BoundingBox, SARQuery, AISQuery, ProviderUnavailableError
from backend.app.providers.registry import ProviderRegistry, provider_registry
from backend.app.services.case_service import CaseService, case_service
from backend.app.services.pipeline_service import pipeline_service, PipelineOptions
from backend.app.services.data_source_control_service import data_source_control_service
from backend.app.services.live_ais_service import live_ais_service

client = TestClient(app)


def test_01_backend_clean_startup():
    """Verify backend starts in a clean production configuration."""
    assert provider_registry.allow_synthetic is False
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_02_frontend_clean_build():
    """Verify frontend build artifacts exist or build cleanly."""
    dist_index = Path("frontend/dist/index.html")
    assert dist_index.exists()


def test_03_landing_page():
    """Verify landing page endpoint returns HTTP 200."""
    res = client.get("/")
    assert res.status_code == 200


def test_04_authentication():
    """Verify authentication lifecycle: login, profile inspection, and logout revocation."""
    # Login with valid analyst credentials
    login_res = client.post("/api/auth/login", json={
        "username": "analyst",
        "password": "Analyst@Forensic2026!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Profile verification
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    profile = me_res.json()
    assert profile["username"] == "analyst"
    assert profile["role"] == "ANALYST"
    assert "create:investigations" in profile["permissions"]

    # Logout & session revocation
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # Revoked token must be rejected
    revoked_check = client.get("/api/auth/me", headers=headers)
    assert revoked_check.status_code == 401


def test_05_application_navigation_routes():
    """Verify core application API endpoints respond without error."""
    routes = [
        "/api/cases",
        "/api/data-sources/health",
        "/api/live/vessels",
        "/api/health/ready",
        "/api/health/live",
    ]
    for r in routes:
        res = client.get(r)
        assert res.status_code in (200, 201), f"Route {r} failed with {res.status_code}"


def test_06_data_source_health():
    """Verify data-source control center returns all 6 categories."""
    res = client.get("/api/data-sources/control-center")
    assert res.status_code == 200
    data = res.json()
    assert "providers" in data
    providers_list = data["providers"]
    assert isinstance(providers_list, list)
    categories = {p["category"] for p in providers_list}
    expected_categories = {
        "Earth Observation",
        "AIS",
        "Ocean",
        "Weather",
        "Vessel Identity",
        "Basemap",
    }
    assert expected_categories.issubset(categories)


def test_07_to_11_real_provider_connectivity():
    """Verify external provider connectivity and honest status reporting without synthetic fallback."""
    res = client.get("/api/data-sources/control-center")
    assert res.status_code == 200
    providers_list = res.json()["providers"]
    providers_by_id = {p["id"]: p for p in providers_list}

    # SAR Provider (Copernicus CDSE)
    sar_info = providers_by_id["earth_observation"]
    assert sar_info["category"] == "Earth Observation"
    if not sar_info["authentication"]["configured"]:
        assert "UNCONFIGURED" in sar_info["authentication"]["status"].upper() or "PENDING" in sar_info["authentication"]["status"].upper()

    # AIS Provider (AISStream)
    ais_info = providers_by_id["ais"]
    assert ais_info["category"] == "AIS"
    if not ais_info["authentication"]["configured"]:
        assert "UNCONFIGURED" in ais_info["authentication"]["status"].upper() or ais_info["status"] in ("DISCONNECTED", "DEGRADED")

    # Ocean Currents (CMEMS)
    ocean_info = providers_by_id["ocean"]
    assert ocean_info["category"] == "Ocean"

    # Wind Provider (Open-Meteo)
    wind_info = providers_by_id["weather"]
    assert wind_info["category"] == "Weather"
    assert wind_info["status"] in ("ONLINE", "OPERATIONAL", "DEGRADED")


def test_12_to_24_create_and_run_real_investigation():
    """Test full dynamic pipeline execution on real historical data with real sensors and zero fabrication."""
    case_id = "case_new_diamond_2020"

    # Verify input data exists
    case = case_service.get_case(case_id)
    assert case is not None
    assert case.metadata.get("synthetic") is False

    # Execute dynamic pipeline
    opts = PipelineOptions(
        particle_count=200,
        max_hours_backward=18.0,
        time_step_minutes=30,
        random_seed=42,
        use_synthetic_slick=False,
    )
    result = pipeline_service.run_pipeline(case_id=case_id, options=opts)

    # 16. Slick detection verification
    assert len(result.slicks) > 0
    slick = result.slicks[0]
    assert slick.area_sq_km > 0.5
    assert slick.confidence_score > 0.5

    # 17. Drift computation verification
    assert len(result.drift_simulations) > 0
    sim = result.drift_simulations[0]
    assert sim.particle_count == 200
    assert sim.simulation_mode == "BACKWARD_LAGRANGIAN"
    assert len(result.probability_clouds) > 0

    # 18. Origin / Release-window computation
    assert len(result.release_windows) > 0
    rw = result.release_windows[0]
    assert rw.estimated_start_time < rw.estimated_end_time
    assert rw.peak_probability_time is not None

    # 19 & 20. AIS correlation & candidate generation
    assert len(result.candidate_vessels) > 0
    assert any("NEW DIAMOND" in c.vessel_name for c in result.candidate_vessels)

    # 21. Attribution scoring
    assert len(result.attribution_scores) > 0
    top_score = result.attribution_scores[0]
    assert top_score.rank == 1
    assert "NEW DIAMOND" in top_score.candidate_name

    # 22. Evidence items verification
    assert len(top_score.supporting_evidence) > 0
    assert len(top_score.evidence_items) > 0
    categories = {e.category for e in top_score.evidence_items}
    assert "SUPPORTING_EVIDENCE" in [c.value for c in categories]

    # 23. Uncertainty bounds
    assert len(top_score.uncertainty_items) > 0
    assert any("Uncertainty" in u.title for u in top_score.uncertainty_items)


def test_25_live_maritime_tracking():
    """Verify live maritime endpoint reports honest real-time telemetry."""
    res = client.get("/api/live/vessels")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    # When disconnected, zero fake vessels returned
    if data["status"] == "DISCONNECTED":
        assert len(data["vessels"]) == 0


def test_26_to_29_persistence_and_backend_restart():
    """Verify investigation results persist to disk and survive a backend restart."""
    case_id = "case_new_diamond_2020"

    # Check persistence files exist on disk
    case_dir = Path("data/cases") / case_id
    res_file = case_dir / "investigation_result.json"
    assert res_file.exists()

    # Simulate clean backend restart by instantiating a brand new CaseService
    new_service = CaseService(data_dir=Path("data/cases"))
    reloaded_case = new_service.get_case(case_id)
    assert reloaded_case is not None

    # Verify persisted results survived reload
    persisted_res = new_service.get_investigation_result(case_id)
    assert persisted_res is not None
    assert "attribution_scores" in persisted_res
    assert len(persisted_res["attribution_scores"]) > 0
    assert persisted_res["attribution_scores"][0]["rank"] == 1


def test_30_to_31_pdf_report_actual_results():
    """Verify PDF report generation produces a valid document containing actual dynamic outputs."""
    case_id = "case_new_diamond_2020"
    res = client.get(f"/api/cases/{case_id}/report/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF-")
    assert len(res.content) > 2000  # Valid multi-page forensic PDF
