"""Visual diagnostics generator for MT New Diamond SAR detection and lookalike classification."""

from datetime import datetime, timezone
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from backend.app.models.schemas import SARLookalikeClass, SARScene, SlickPolygon
from backend.app.providers.sar_adapter import HistoricalSARAdapter
from backend.app.services.sar_detector import DeterministicSARDetector


def generate_new_diamond_sar_diagnostics(
    output_path: str = "docs/new_diamond_sar_diagnostics.png",
    seed: int = 42,
) -> str:
    """Runs the SAR detector on the MT New Diamond historical scene and saves visual diagnostics."""
    adapter = HistoricalSARAdapter(seed=seed)
    scene_meta = adapter.load_scene_metadata("data/sar/new_diamond_s1_scene.json")

    scene = SARScene(
        id=scene_meta["id"],
        case_id=scene_meta["case_id"],
        satellite_platform=scene_meta["satellite_platform"],
        sensor_mode=scene_meta["sensor_mode"],
        polarization=scene_meta["polarization"],
        acquisition_timestamp=datetime(2020, 9, 3, 12, 45, tzinfo=timezone.utc),
        footprint_polygon=SlickPolygon(**scene_meta["footprint_polygon"]),
        pixel_resolution_meters=20.0,
    )

    raster = adapter.fetch_raster(scene)
    detector = DeterministicSARDetector()
    cfg = detector.config

    # Step 1: Preprocessing & Speckle Filter
    filtered_db = detector.preprocess_speckle_filter(raster.data_db, window_size=cfg.speckle_filter_size)

    # Step 2: Land Masking
    land_mask = detector.create_land_mask(raster.data_db, threshold_db=-4.0, buffer_pixels=3)

    # Step 3: Adaptive CFAR Segmentation
    dark_mask, sea_mean, sea_std = detector.segment_dark_regions(
        filtered_db, land_mask, k_sigma=cfg.cfar_k_sigma, window_size=cfg.cfar_guard_window
    )

    # Step 4: Extract and Classify Candidates
    candidates = detector.extract_candidates(scene, raster, cfg)

    # Create 6-panel figure
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.patch.set_facecolor("#0b132b")

    titles = [
        "1. Original Sentinel-1A C-Band SAR (VV, dB)",
        "2. Preprocessed & Speckle Filtered (dB)",
        "3. Coastal Land Mask (Sri Lanka Coast)",
        "4. Adaptive CFAR Dark Formations",
        "5. Extracted Candidates & Classifications",
        "6. Selected Primary Slick (MT New Diamond)",
    ]

    # Panel 1: Original SAR
    im1 = axes[0, 0].imshow(raster.data_db, cmap="gray", vmin=-25, vmax=0)
    axes[0, 0].set_title(titles[0], color="#f8fafc", fontsize=11, fontweight="bold")
    plt.colorbar(im1, ax=axes[0, 0], fraction=0.046, pad=0.04, label="Backscatter (dB)")

    # Panel 2: Preprocessed
    im2 = axes[0, 1].imshow(filtered_db, cmap="gray", vmin=-25, vmax=0)
    axes[0, 1].set_title(titles[1], color="#f8fafc", fontsize=11, fontweight="bold")
    plt.colorbar(im2, ax=axes[0, 1], fraction=0.046, pad=0.04, label="Backscatter (dB)")

    # Panel 3: Land Mask
    axes[0, 2].imshow(land_mask, cmap="hot", vmin=0, vmax=1)
    axes[0, 2].set_title(titles[2], color="#f8fafc", fontsize=11, fontweight="bold")

    # Panel 4: Dark Mask
    axes[1, 0].imshow(dark_mask, cmap="Blues_r")
    axes[1, 0].set_title(titles[3], color="#f8fafc", fontsize=11, fontweight="bold")

    # Panel 5: Candidates & Classifications
    axes[1, 1].imshow(filtered_db, cmap="gray", vmin=-25, vmax=0)
    for c in candidates:
        color = "#ef4444" if c.is_accepted else "#f59e0b"
        poly_ring = c.polygon.coordinates[0]
        px_coords = [raster.geo_to_pixel(p[0], p[1]) for p in poly_ring]
        xs = [p[1] for p in px_coords]
        ys = [p[0] for p in px_coords]
        label = "Mineral Oil" if c.is_accepted else "Lookalike"
        axes[1, 1].plot(xs, ys, color=color, linewidth=2.0, label=f"{label} ({c.features.area_sq_km}km²)")
        c_r, c_c = raster.geo_to_pixel(c.centroid.coordinates[0], c.centroid.coordinates[1])
        axes[1, 1].plot(c_c, c_r, marker="x", color=color, markersize=8)

    axes[1, 1].set_title(titles[4], color="#f8fafc", fontsize=11, fontweight="bold")

    # Panel 6: Selected Slick
    accepted = [c for c in candidates if c.is_accepted]
    axes[1, 2].imshow(filtered_db, cmap="gray", vmin=-25, vmax=0)
    if accepted:
        best = max(accepted, key=lambda x: x.confidence_score)
        poly_ring = best.polygon.coordinates[0]
        px_coords = [raster.geo_to_pixel(p[0], p[1]) for p in poly_ring]
        xs = [p[1] for p in px_coords]
        ys = [p[0] for p in px_coords]
        axes[1, 2].fill(xs, ys, color="#ef4444", alpha=0.45)
        axes[1, 2].plot(xs, ys, color="#dc2626", linewidth=2.5)
        c_r, c_c = raster.geo_to_pixel(best.centroid.coordinates[0], best.centroid.coordinates[1])
        axes[1, 2].plot(c_c, c_r, marker="o", color="#ffffff", markersize=6, markeredgecolor="#ef4444")
        axes[1, 2].text(
            15, 275,
            f"Vessel: MT NEW DIAMOND (MMSI 371584000)\nArea: {best.features.area_sq_km} km² | Contrast: {best.features.mean_contrast_db} dB\nConfidence: {best.confidence_score*100:.1f}% | Orientation: {best.features.major_axis_orientation_deg}°",
            color="#38bdf8",
            fontsize=9,
            backgroundcolor="#0f172a",
            weight="bold"
        )
    axes[1, 2].set_title(titles[5], color="#f8fafc", fontsize=11, fontweight="bold")

    for ax in axes.flat:
        ax.tick_params(colors="#94a3b8")
        for spine in ax.spines.values():
            spine.set_color("#334155")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    return output_path


if __name__ == "__main__":
    out = generate_new_diamond_sar_diagnostics()
    print(f"Generated MT New Diamond SAR diagnostics visual at: {out}")
