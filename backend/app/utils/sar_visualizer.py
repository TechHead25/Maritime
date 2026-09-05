"""Visual debugging generator for SAR detection pipeline steps."""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless plotting
import matplotlib.pyplot as plt
import numpy as np

from backend.app.models.schemas import SARScene, SlickDetection, SARLookalikeClass
from backend.app.services.sar_detector import (
    DeterministicSARDetector,
    DetectorConfig,
    SARRaster,
    SyntheticSARGenerator,
)


def generate_sar_detection_debug_plot(
    output_path: str = "docs/sar_detection_steps.png",
    seed: int = 42,
) -> str:
    """Runs the SAR detector on a synthetic scene and saves a multi-panel visual debug image."""
    # 1. Generate Synthetic Scene
    raster = SyntheticSARGenerator.create_synthetic_scene(seed=seed)
    mock_scene = SARScene(
        id="sar-scene-synthetic-001",
        case_id="case-test-sar-001",
        satellite_platform="Sentinel-1A (Synthetic SAR)",
        sensor_mode="IW",
        polarization="VV",
        acquisition_timestamp=datetime(2026, 9, 1, 14, 30, tzinfo=timezone.utc),
        pixel_resolution_meters=20.0,
    )
    detector = DeterministicSARDetector()
    cfg = detector.config

    # 2. Step-by-Step Processing
    filtered_db = detector.preprocess_speckle_filter(raster.data_db, window_size=cfg.speckle_filter_size)
    land_mask = detector.create_land_mask(raster.data_db, threshold_db=cfg.land_threshold_db, buffer_pixels=cfg.land_buffer_pixels)
    dark_mask, sea_mean, sea_std = detector.segment_dark_regions(
        filtered_db, land_mask, k_sigma=cfg.cfar_k_sigma, window_size=cfg.cfar_guard_window
    )
    candidates = detector.extract_candidates(mock_scene, raster, cfg)

    # 3. Create Multi-Panel Plot
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.patch.set_facecolor('#0b132b')

    cmap_sar = "gray"
    titles = [
        "1. Raw SAR Backscatter (dB)",
        "2. Speckle Filtered (dB)",
        "3. Land & Coastal Mask",
        "4. Adaptive CFAR Dark Segments",
        "5. Extracted Candidates & Types",
        "6. Primary Mineral Slick Detection",
    ]

    # Panel 1: Raw SAR
    im1 = axes[0, 0].imshow(raster.data_db, cmap=cmap_sar, vmin=-25, vmax=0)
    axes[0, 0].set_title(titles[0], color='#f8fafc', fontsize=11, fontweight='bold')
    plt.colorbar(im1, ax=axes[0, 0], fraction=0.046, pad=0.04, label="Backscatter (dB)")

    # Panel 2: Speckle Filtered
    im2 = axes[0, 1].imshow(filtered_db, cmap=cmap_sar, vmin=-25, vmax=0)
    axes[0, 1].set_title(titles[1], color='#f8fafc', fontsize=11, fontweight='bold')
    plt.colorbar(im2, ax=axes[0, 1], fraction=0.046, pad=0.04, label="Backscatter (dB)")

    # Panel 3: Land Mask
    axes[0, 2].imshow(land_mask, cmap='hot', vmin=0, vmax=1)
    axes[0, 2].set_title(titles[2], color='#f8fafc', fontsize=11, fontweight='bold')

    # Panel 4: Dark Mask
    axes[1, 0].imshow(dark_mask, cmap='Blues_r')
    axes[1, 0].set_title(titles[3], color='#f8fafc', fontsize=11, fontweight='bold')

    # Panel 5: Candidates
    axes[1, 1].imshow(filtered_db, cmap=cmap_sar, vmin=-25, vmax=0)
    for c in candidates:
        color = '#ef4444' if c.is_accepted else '#f59e0b'
        # Plot candidate polygon points converted to pixel coordinates
        poly_ring = c.polygon.coordinates[0]
        px_coords = [raster.geo_to_pixel(p[0], p[1]) for p in poly_ring]
        xs = [p[1] for p in px_coords]
        ys = [p[0] for p in px_coords]
        axes[1, 1].plot(xs, ys, color=color, linewidth=1.8, label=f"{c.classification.value} ({c.features.area_sq_km}km²)")
        # Plot centroid
        c_r, c_c = raster.geo_to_pixel(c.centroid.coordinates[0], c.centroid.coordinates[1])
        axes[1, 1].plot(c_c, c_r, marker='x', color=color, markersize=8)

    axes[1, 1].set_title(titles[4], color='#f8fafc', fontsize=11, fontweight='bold')

    # Panel 6: Final Verified Slick
    mineral_slicks = [c for c in candidates if c.is_accepted]
    axes[1, 2].imshow(filtered_db, cmap=cmap_sar, vmin=-25, vmax=0)
    if mineral_slicks:
        best = max(mineral_slicks, key=lambda x: x.confidence_score)
        poly_ring = best.polygon.coordinates[0]
        px_coords = [raster.geo_to_pixel(p[0], p[1]) for p in poly_ring]
        xs = [p[1] for p in px_coords]
        ys = [p[0] for p in px_coords]
        axes[1, 2].fill(xs, ys, color='#ef4444', alpha=0.45)
        axes[1, 2].plot(xs, ys, color='#dc2626', linewidth=2.5)
        c_r, c_c = raster.geo_to_pixel(best.centroid.coordinates[0], best.centroid.coordinates[1])
        axes[1, 2].plot(c_c, c_r, marker='o', color='#ffffff', markersize=6, markeredgecolor='#ef4444')
        axes[1, 2].text(
            15, 280,
            f"Area: {best.features.area_sq_km} km² | Contrast: {best.features.mean_contrast_db} dB\nConfidence: {best.confidence_score*100:.1f}% | Angle: {best.features.major_axis_orientation_deg}°",
            color='#38bdf8',
            fontsize=9,
            backgroundcolor='#0f172a',
            weight='bold'
        )
    axes[1, 2].set_title(titles[5], color='#f8fafc', fontsize=11, fontweight='bold')

    for ax in axes.flat:
        ax.tick_params(colors='#94a3b8')
        for spine in ax.spines.values():
            spine.set_color('#334155')

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    return output_path


if __name__ == "__main__":
    out = generate_sar_detection_debug_plot()
    print(f"Generated SAR detection debug visual at: {out}")
