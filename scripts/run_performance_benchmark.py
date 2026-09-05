"""Performance Benchmarking and Profiling Script for Maritime Oil Attribution Platform."""

import io
import json
import logging
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.schemas import SARScene
from backend.app.services.case_service import case_service
from backend.app.services.sar_detector import sar_detector, SyntheticSARGenerator
from backend.app.services.drift_engine import DriftEngine, DriftEngineConfig
from backend.app.services.ais_engine import AISEngine
from backend.app.services.scoring_engine import ScoringEngine
from backend.app.services.evidence_engine import evidence_engine
from backend.app.services.report_generator import InvestigationReportGenerator
from backend.app.services.pipeline_service import pipeline_service, PipelineOptions

logging.basicConfig(level=logging.WARNING)
client = TestClient(app)

def benchmark_suite():
    print("================================================================================")
    print("      MARITIME OIL ATTRIBUTION PLATFORM - PERFORMANCE BENCHMARKING SUITE       ")
    print("================================================================================")

    case_service.reload_cases_from_disk()
    case_id = "case_new_diamond_2020"
    loaded = case_service.get_case_details(case_id)
    assert loaded is not None

    measurements = {}

    # 1. SAR Loading
    t0 = time.perf_counter()
    from backend.app.providers.sar_adapter import HistoricalSARAdapter
    sar_adapter = HistoricalSARAdapter(seed=42)
    sar_scene = loaded["sar_scenes"][0]
    raster = sar_adapter.fetch_raster(sar_scene)
    measurements["sar_loading_ms"] = (time.perf_counter() - t0) * 1000

    # 2. SAR Preprocessing (Speckle filtering & land masking)
    t0 = time.perf_counter()
    denoised = sar_detector.apply_speckle_filter(raster.data_db, kernel_size=5)
    land_mask = sar_detector.build_land_mask(raster.data_db, threshold_db=-4.0)
    measurements["sar_preprocessing_ms"] = (time.perf_counter() - t0) * 1000

    # 3. Slick Detection & Feature Extraction (CFAR thresholding + morphology)
    t0 = time.perf_counter()
    patches = sar_detector.extract_candidate_patches(
        raster=raster,
        denoised_db=denoised,
        land_mask=land_mask,
        sar_scene_id=sar_scene.id,
    )
    measurements["slick_detection_ms"] = (time.perf_counter() - t0) * 1000

    # 4. Lookalike Classification
    t0 = time.perf_counter()
    classified_patches = [sar_detector.classify_patch(p) for p in patches]
    primary_slick = sar_detector.detect_primary_slick(raster=raster, sar_scene_id=sar_scene.id)
    measurements["lookalike_classification_ms"] = (time.perf_counter() - t0) * 1000

    # 5. Environmental Data Loading
    t0 = time.perf_counter()
    env = loaded["environment"]
    curr_vec = env["ocean_currents"]["mean_current_vectors"]
    wind_vec = env["wind_data"]["mean_wind_vectors"]
    measurements["environmental_loading_ms"] = (time.perf_counter() - t0) * 1000

    # 6. Drift Simulation (1000 particles, 49 timesteps)
    drift_engine = DriftEngine()
    t0 = time.perf_counter()
    drift_res_1k = drift_engine.run_backward_simulation(
        slick=primary_slick,
        current_vectors=curr_vec,
        wind_vectors=wind_vec,
        config=DriftEngineConfig(
            particle_count=1000,
            time_step_minutes=30,
            max_hours_backward=24.0,
            random_seed=42,
        ),
    )
    measurements["drift_sim_1k_ms"] = (time.perf_counter() - t0) * 1000

    # 6b. Drift Simulation Scaling (2000 & 5000 particles)
    t0 = time.perf_counter()
    drift_res_2k = drift_engine.run_backward_simulation(
        slick=primary_slick,
        current_vectors=curr_vec,
        wind_vectors=wind_vec,
        config=DriftEngineConfig(
            particle_count=2000,
            time_step_minutes=30,
            max_hours_backward=24.0,
            random_seed=42,
        ),
    )
    measurements["drift_sim_2k_ms"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    drift_res_5k = drift_engine.run_backward_simulation(
        slick=primary_slick,
        current_vectors=curr_vec,
        wind_vectors=wind_vec,
        config=DriftEngineConfig(
            particle_count=5000,
            time_step_minutes=30,
            max_hours_backward=24.0,
            random_seed=42,
        ),
    )
    measurements["drift_sim_5k_ms"] = (time.perf_counter() - t0) * 1000

    # 7. AIS Data Loading
    t0 = time.perf_counter()
    vessel_tracks = loaded["vessel_tracks"]
    measurements["ais_loading_ms"] = (time.perf_counter() - t0) * 1000

    # 8. AIS Normalization & Interpolation
    t0 = time.perf_counter()
    ais_engine = AISEngine()
    for vt in vessel_tracks:
        _ = ais_engine._interpolate_track(vt, step_minutes=5)
    measurements["ais_interpolation_ms"] = (time.perf_counter() - t0) * 1000

    # 9. Spatial Matching & Candidate Generation
    t0 = time.perf_counter()
    candidates = ais_engine.identify_candidate_vessels(
        case_id=case_id,
        vessel_tracks=vessel_tracks,
        origin_centroid=drift_res_1k.origin_centroid,
        origin_radius_km=drift_res_1k.origin_uncertainty_radius_km,
        release_window=drift_res_1k.release_window,
        probability_clouds=drift_res_1k.probability_clouds,
    )
    measurements["candidate_generation_ms"] = (time.perf_counter() - t0) * 1000

    # 10. Attribution Scoring
    scoring_engine = ScoringEngine()
    t0 = time.perf_counter()
    scores = scoring_engine.score_candidates(
        case_id=case_id,
        candidates=candidates,
        slick=primary_slick,
        release_window=drift_res_1k.release_window,
    )
    measurements["attribution_scoring_ms"] = (time.perf_counter() - t0) * 1000

    # 11. Evidence Generation
    t0 = time.perf_counter()
    cand_by_id = {c.id: c for c in candidates}
    for score in scores:
        cand = cand_by_id.get(score.candidate_vessel_id)
        if cand:
            _ = evidence_engine.generate_structured_evidence(
                score=score,
                candidate=cand,
                slick=primary_slick,
                release_window=drift_res_1k.release_window,
                uncertainty_radius_km=drift_res_1k.origin_uncertainty_radius_km,
            )
    measurements["evidence_generation_ms"] = (time.perf_counter() - t0) * 1000

    # 12. Full Pipeline Service Execution
    t0 = time.perf_counter()
    pipe_res = pipeline_service.run_investigation(
        case_id=case_id,
        options=PipelineOptions(
            particle_count=1000,
            random_seed=42,
            bypass_cache=True,
        ),
    )
    measurements["full_e2e_pipeline_uncached_ms"] = (time.perf_counter() - t0) * 1000

    # 12b. Full Pipeline Cached Execution
    t0 = time.perf_counter()
    pipe_res_cached = pipeline_service.run_investigation(
        case_id=case_id,
        options=PipelineOptions(
            particle_count=1000,
            random_seed=42,
            bypass_cache=False,
        ),
    )
    measurements["full_e2e_pipeline_cached_ms"] = (time.perf_counter() - t0) * 1000

    # 13. PDF Report Generation (with Matplotlib chart rendering)
    t0 = time.perf_counter()
    pdf_path = "docs/perf_test_report.pdf"
    InvestigationReportGenerator.generate_pdf(pipe_res, pdf_path)
    measurements["pdf_generation_ms"] = (time.perf_counter() - t0) * 1000
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    # Print results
    print("\n--- MEASURED EXECUTION TIMINGS (HIGH RESOLUTION) ---")
    for k, v in measurements.items():
        print(f"  {k:36s}: {v:8.3f} ms ({v/1000:.4f} s)")

    return measurements

if __name__ == "__main__":
    benchmark_suite()
