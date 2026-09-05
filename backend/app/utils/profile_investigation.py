"""Performance Profiling & Benchmark Tool for Maritime Oil-Spill Attribution Intelligence.

Measures precise execution times across:
1. SAR Ingestion, Preprocessing & CFAR Slick Detection
2. Backward Lagrangian Particle Drift Simulation
3. AIS Trajectory Interception & Gap Analysis
4. Multi-Factor Attribution Scoring & Evidence Assembly
5. Complete Backend Investigation Pipeline
6. PDF Report Generation & Export
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import time
from typing import Any, Dict, List

from backend.app.models.schemas import (
    InvestigationCase,
    SARScene,
    SlickDetection,
    SlickPolygon,
)
from backend.app.providers.sar_adapter import HistoricalSARAdapter
from backend.app.services.ais_engine import AISEngine, AISEngineConfig
from backend.app.services.case_service import case_service
from backend.app.services.drift_engine import DriftEngine, DriftEngineConfig
from backend.app.services.pipeline_service import pipeline_service, PipelineOptions
from backend.app.services.report_generator import report_generator
from backend.app.services.sar_detector import DeterministicSARDetector
from backend.app.services.scoring_engine import ScoringEngine


def profile_all_subsystems(iterations: int = 5) -> Dict[str, Any]:
    case_service.reload_cases_from_disk()
    case_id = "case_new_diamond_2020"

    print("=" * 80)
    print("  MARITIME OIL-SPILL ATTRIBUTION INTELLIGENCE")
    print(f"  SYSTEM PERFORMANCE PROFILING BENCHMARK ({iterations} ITERATIONS)")
    print("=" * 80)

    # 1. Benchmark SAR Preprocessing & Detection
    sar_times = []
    sar_adapter = HistoricalSARAdapter(seed=42)
    sar_detector = DeterministicSARDetector()
    scene = case_service.sar_scenes[case_id][0]

    for _ in range(iterations):
        t0 = time.perf_counter()
        raster = sar_adapter.fetch_raster(scene)
        primary_slick = sar_detector.detect_primary_slick(scene, raster)
        t1 = time.perf_counter()
        sar_times.append((t1 - t0) * 1000.0)

    # 2. Benchmark Drift Simulation (1,000 particles, 37 time slices)
    drift_times = []
    drift_engine = DriftEngine(config=DriftEngineConfig(
        time_step_minutes=30,
        max_hours_backward=18.0,
        particle_count=1000,
        random_seed=42,
    ))
    env = case_service.environments.get(case_id, {})

    for _ in range(iterations):
        t0 = time.perf_counter()
        drift_res = drift_engine.run_backward_drift(
            slick_detection=primary_slick,
            observation_timestamp=scene.acquisition_timestamp,
            ocean_current_data=env.get("ocean_currents"),
            wind_data=env.get("wind_data"),
            estimated_release_hours_ago=9.25,
            release_window_half_width_hours=2.0,
        )
        t1 = time.perf_counter()
        drift_times.append((t1 - t0) * 1000.0)

    # 3. Benchmark AIS Interception & Gap Analysis (5 vessels)
    ais_times = []
    ais_engine = AISEngine(config=AISEngineConfig(
        max_cpa_distance_km=50.0,
        interpolation_step_minutes=15.0,
    ))
    vessel_tracks = case_service.vessel_tracks.get(case_id, [])

    for _ in range(iterations):
        t0 = time.perf_counter()
        candidates = ais_engine.identify_candidates(
            case_id=case_id,
            vessel_tracks=vessel_tracks,
            release_window=drift_res.release_window,
            probability_clouds=drift_res.probability_clouds,
        )
        t1 = time.perf_counter()
        ais_times.append((t1 - t0) * 1000.0)

    # 4. Benchmark Attribution Scoring (5 candidates)
    scoring_times = []
    scoring_engine = ScoringEngine()

    for _ in range(iterations):
        t0 = time.perf_counter()
        scores = scoring_engine.score_candidates(
            candidates=candidates,
            vessel_tracks=vessel_tracks,
            slick_detection=primary_slick,
            release_window=drift_res.release_window,
            probability_clouds=drift_res.probability_clouds,
        )
        t1 = time.perf_counter()
        scoring_times.append((t1 - t0) * 1000.0)

    # 5a. Benchmark Cold End-to-End Pipeline Execution (bypassing cache)
    cold_pipeline_times = []
    cold_opts = PipelineOptions(
        time_step_minutes=30,
        max_hours_backward=18.0,
        particle_count=1000,
        random_seed=42,
        estimated_release_hours_ago=9.25,
        use_synthetic_slick=False,
        bypass_cache=True,
    )

    for _ in range(iterations):
        t0 = time.perf_counter()
        full_resp = pipeline_service.run_pipeline(case_id, options=cold_opts)
        t1 = time.perf_counter()
        cold_pipeline_times.append((t1 - t0) * 1000.0)

    # 5b. Benchmark Warm (Cached) Pipeline Execution
    warm_pipeline_times = []
    warm_opts = PipelineOptions(
        time_step_minutes=30,
        max_hours_backward=18.0,
        particle_count=1000,
        random_seed=42,
        estimated_release_hours_ago=9.25,
        use_synthetic_slick=False,
        bypass_cache=False,
    )
    # Warm up cache first
    pipeline_service.run_pipeline(case_id, options=warm_opts)

    for _ in range(iterations):
        t0 = time.perf_counter()
        cached_resp = pipeline_service.run_pipeline(case_id, options=warm_opts)
        t1 = time.perf_counter()
        warm_pipeline_times.append((t1 - t0) * 1000.0)

    # 6. Benchmark PDF Report Generation
    pdf_times = []
    test_pdf_path = "docs/profile_test_report.pdf"

    for _ in range(iterations):
        t0 = time.perf_counter()
        report_generator.generate_pdf(full_resp, output_path=test_pdf_path)
        t1 = time.perf_counter()
        pdf_times.append((t1 - t0) * 1000.0)

    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)

    def calc_stats(times_ms: List[float]) -> Dict[str, float]:
        return {
            "mean_ms": round(statistics.mean(times_ms), 2),
            "min_ms": round(min(times_ms), 2),
            "max_ms": round(max(times_ms), 2),
            "stdev_ms": round(statistics.stdev(times_ms) if len(times_ms) > 1 else 0.0, 2),
        }

    results = {
        "sar_detection": calc_stats(sar_times),
        "backward_drift": calc_stats(drift_times),
        "ais_interception": calc_stats(ais_times),
        "attribution_scoring": calc_stats(scoring_times),
        "cold_investigation_pipeline": calc_stats(cold_pipeline_times),
        "warm_cached_pipeline": calc_stats(warm_pipeline_times),
        "pdf_report_generation": calc_stats(pdf_times),
    }

    print("\nBENCHMARK RESULTS (Time in Milliseconds):")
    print("-" * 80)
    print(f"{'Subsystem / Stage':<35} {'Mean (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12} {'StdDev'}")
    print("-" * 80)
    for name, s in results.items():
        label = name.replace("_", " ").title()
        print(f"{label:<35} {s['mean_ms']:<12.2f} {s['min_ms']:<12.2f} {s['max_ms']:<12.2f} +/- {s['stdev_ms']:.2f}")
    print("-" * 80)

    total_backend_sec = results["cold_investigation_pipeline"]["mean_ms"] / 1000.0
    print(f"\n[PERF] Total Cold End-to-End Pipeline Latency: {total_backend_sec:.3f} seconds (Target: < 180.0s)")
    print(f"[PERF] Performance Target Margin: {(180.0 / total_backend_sec):.1f}x FASTER than 3-minute target!")
    print(f"[PERF] Cached Response Latency: {results['warm_cached_pipeline']['mean_ms']:.2f} ms ({results['cold_investigation_pipeline']['mean_ms'] / max(results['warm_cached_pipeline']['mean_ms'], 0.01):.0f}x speedup)")
    print("=" * 80)

    return results


if __name__ == "__main__":
    profile_all_subsystems(iterations=5)
