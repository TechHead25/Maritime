"""Integration test verifying pipeline generalization on a second historical case (Ennore 2017)."""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.case_service import case_service

client = TestClient(app)

def test_ennore_historical_case_generalization():
    """Verify that case_ennore_2017 executes end-to-end without pipeline modifications."""
    case_service.reload_cases_from_disk()

    case_id = "case_ennore_2017"

    # 1. Verify case detail API
    res_case = client.get(f"/api/cases/{case_id}")
    assert res_case.status_code == 200
    cdata = res_case.json()
    assert cdata["case"]["id"] == case_id
    assert len(cdata["vessel_tracks"]) >= 5
    assert len(cdata["sar_scenes"]) >= 1

    # 2. Execute pipeline
    res_pipe = client.post(
        f"/api/cases/{case_id}/investigate",
        json={
            "time_step_minutes": 30,
            "max_hours_backward": 24.0,
            "estimated_release_hours_ago": 20.7,
            "release_window_half_width_hours": 2.5,
            "particle_count": 500,
            "random_seed": 42,
            "use_synthetic_slick": False,
            "bypass_cache": True
        }
    )
    assert res_pipe.status_code == 200
    pdata = res_pipe.json()
    assert pdata["case"]["id"] == case_id
    assert len(pdata["candidate_vessels"]) >= 1
    assert len(pdata["attribution_scores"]) >= 1

    # Verify that DAWN KANCHIPURAM is ranked #1 based on data-driven physics and telemetry
    top = pdata["attribution_scores"][0]
    assert "DAWN KANCHIPURAM" in top["candidate_name"].upper()
    assert top["rank"] == 1
    assert top["total_score"] > 0.0

    # 3. Verify PDF report generation
    res_pdf = client.get(f"/api/cases/{case_id}/report/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-")
