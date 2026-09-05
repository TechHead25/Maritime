"""Generalization Test Suite: Executing full forensic investigation on a second real historical case (Ennore Kamarajar Port Spill 2017)."""

import json
import logging
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.schemas import CaseStatus
from backend.app.services.case_service import case_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("generalization_test")

client = TestClient(app)

def run_generalization_test():
    print("================================================================================")
    print("             MARITIME OIL ATTRIBUTION - GENERALIZATION TEST SUITE               ")
    print("      CASE 2: Ennore Kamarajar Port Tanker Collision & Oil Spill (2017)        ")
    print("================================================================================")

    case_id = "case_ennore_2017"

    # Reload cases to ensure case_ennore_2017 is discovered
    case_service.reload_cases_from_disk()

    # Stage 1: Load case details
    print("\n[STAGE 1] Loading and Validating Case Metadata...")
    res_case = client.get(f"/api/cases/{case_id}")
    assert res_case.status_code == 200, f"Failed to fetch case: {res_case.text}"
    cdata = res_case.json()
    case = cdata["case"]
    sar_scenes = cdata["sar_scenes"]
    vessels = cdata["vessel_tracks"]
    env = cdata["environment"]
    
    print(f"  [OK] Case Title: {case['title']}")
    print(f"  [OK] Geographic Area ROI: {case.get('region_of_interest')}")
    print(f"  [OK] SAR Scenes: {len(sar_scenes)} ({sar_scenes[0]['satellite_platform']} {sar_scenes[0]['acquisition_timestamp']})")
    print(f"  [OK] Ingested Vessels: {len(vessels)}")
    print(f"  [OK] Ocean Currents: {env['ocean_currents']['mean_current_vectors']}")
    print(f"  [OK] Wind Vectors: {env['wind_data']['mean_wind_vectors']}")

    # Stage 2: SAR Detection & Lookalike Discrimination
    print("\n[STAGE 2] SAR Feature Extraction & Discrimination...")
    res_sar = client.get(f"/api/cases/{case_id}/sar-candidates")
    assert res_sar.status_code == 200, f"Failed SAR candidates: {res_sar.text}"
    sdata = res_sar.json()
    print(f"  [OK] Accepted Slicks: {len(sdata['accepted_slicks'])}, Rejected Lookalikes: {len(sdata['rejected_candidates'])}")

    # Stage 3: Full Pipeline Execution
    print("\n[STAGE 3] Executing 8-Stage Pure Mathematical Forensic Pipeline...")
    t0 = time.time()
    res_pipe = client.post(
        f"/api/cases/{case_id}/investigate",
        json={
            "time_step_minutes": 30,
            "max_hours_backward": 24.0,
            "estimated_release_hours_ago": 20.7,
            "release_window_half_width_hours": 2.5,
            "particle_count": 1000,
            "random_seed": 42,
            "use_synthetic_slick": False,
            "bypass_cache": True
        }
    )
    t_pipe = time.time() - t0
    assert res_pipe.status_code == 200, f"Pipeline failed: {res_pipe.text}"
    pdata = res_pipe.json()
    print(f"  [OK] Pipeline Completed in {t_pipe:.3f} seconds (1,000 particles, 49 timesteps)")

    # Stage 4: Backward Drift & Origin Uncertainty
    print("\n[STAGE 4] Lagrangian Backward Drift & Reconstructed Release Origin...")
    origin = pdata["origin_centroid"]
    unc_radius = pdata["origin_uncertainty_radius_km"]
    clouds = pdata["probability_clouds"]
    r_windows = pdata["release_windows"]
    print(f"  [OK] Reconstructed Origin Centroid: {origin['coordinates']} (WGS84 [Lon, Lat])")
    print(f"  [OK] Origin 1-Sigma Uncertainty: +/- {unc_radius:.2f} km")
    print(f"  [OK] Probability Clouds: {len(clouds)} timesteps ({clouds[0]['timestamp']} -> {clouds[-1]['timestamp']})")
    print(f"  [OK] Release Window Bounds: [{r_windows[0]['estimated_start_time']} to {r_windows[0]['estimated_end_time']}]")
    print(f"  [OK] Peak Release Window: {r_windows[0]['peak_probability_time']}")

    # Stage 5: AIS Interception & Candidate Attribution Scoring
    print("\n[STAGE 5] Candidate Interception, 5-Factor Scoring & Structured Evidence...")
    candidates = pdata["candidate_vessels"]
    scores = pdata["attribution_scores"]
    print(f"  [OK] Intercepted Candidates: {len(candidates)}")
    for s in scores:
        print(f"\n  [RANK #{s['rank']}]: {s['candidate_name']} (MMSI: {s['mmsi']}, Type: {s['vessel_type']})")
        print(f"    - Total Attribution Score: {s['total_score']:.1f} / 100 ({s['risk_level']})")
        print(f"    - Sub-Scores (5-Factor Calibrated Matrix):")
        for k, v in s["sub_scores"].items():
            print(f"      * {k:26s}: {v:.1f}")
        supp = s.get("supporting_evidence", [])
        cont = s.get("contradicting_evidence", [])
        excul = s.get("exculpatory_evidence", [])
        qual = s.get("data_quality_items", []) + s.get("uncertainty_items", [])
        print(f"    - Evidence: {len(supp)} Supp, {len(cont)} Cont, {len(excul)} Excul, {len(qual)} Quality/Uncertainty")
        for ev in s.get("evidence_items", []):
            print(f"      [{ev['category']:24s}] {ev['title']} ({ev['severity']}) -> {ev['description']}")

    # Stage 6: Verdict Phrasing & Scientific Defensibility
    print("\n[STAGE 6] Forensic Decision-Support Statement...")
    print(f"  Summary: \"{pdata['summary_verdict']}\"")

    # Stage 7: Persistence Verification
    print("\n[STAGE 7] Local Disk Persistence & Artifact Organization...")
    case_dir = Path("data/cases") / case_id
    assert (case_dir / "investigation_result.json").exists()
    assert (case_dir / "investigation_config.json").exists()
    assert (case_dir / "provenance.json").exists()
    print(f"  [OK] All persistence artifacts verified under {case_dir}")

    # Stage 8: PDF Report Generation
    print("\n[STAGE 8] Compiling PDF Forensic Dossier...")
    res_pdf = client.get(f"/api/cases/{case_id}/report/pdf")
    assert res_pdf.status_code == 200, f"PDF generation failed: {res_pdf.text}"
    assert res_pdf.headers["content-type"] == "application/pdf"
    print(f"  [OK] PDF Generated Cleanly: {len(res_pdf.content):,} bytes")

    print("\n================================================================================")
    print("             GENERALIZATION TEST ON CASE 2 COMPLETED SUCCESSFULLY!              ")
    print("================================================================================")

if __name__ == "__main__":
    run_generalization_test()
