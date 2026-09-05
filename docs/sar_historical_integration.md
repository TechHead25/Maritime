# Historical SAR Dataset Integration: MT New Diamond (September 2020)

**Component:** Satellite SAR Ingestion & Dark-Patch Feature Extraction  
**Satellite Sensor:** Copernicus Sentinel-1A C-band SAR ($\lambda = 5.546 \, \text{cm}$)  
**Sensor Mode:** Level-1 GRD in Interferometric Wide Swath (IW) mode  
**Polarization:** Co-polarized VV channel  
**Acquisition Timestamp:** `2020-09-03T12:45:00Z` ($T_{\text{obs}}$)  
**Historical Case Study:** *MT New Diamond* VLCC Fire & Bunker Oil Release (Bay of Bengal / Eastern Sri Lanka)

---

## 1. Product Ingestion & Validation

The `HistoricalSARAdapter` ([`backend/app/providers/sar_adapter.py`](file:///c:/Projects/Maritime_Oil/backend/app/providers/sar_adapter.py)) ingests the real Sentinel-1A product metadata ([`data/sar/new_diamond_s1_scene.json`](file:///c:/Projects/Maritime_Oil/data/sar/new_diamond_s1_scene.json)) and enforces the following pre-flight validation gates:

1. **Satellite Platform & Sensor Mode:** Validates that the platform is `Sentinel-1A` / `Sentinel-1B` in `IW` mode.
2. **Polarization Channel:** Enforces co-polarized `VV` channel (cross-pol `VH` has low backscatter contrast over calm sea).
3. **Geographic Coverage:** Validates that the ground swath footprint $[81.5^\circ\text{E} - 84.5^\circ\text{E}] \times [6.5^\circ\text{N} - 9.0^\circ\text{N}]$ covers the incident coordinates ($07^\circ 45'\text{N}, 082^\circ 30'\text{E}$).
4. **Acquisition Timestamp:** Validates that $T_{\text{obs}}$ (`2020-09-03T12:45:00Z`) aligns with the incident time window.

---

## 2. Detection Pipeline Execution

```
Original SAR (VV dB) ──► Adaptive Speckle Filter ──► Coastal Land Mask ──► CFAR Dark Segmentation ──► Lookalike Rejection ──► Primary Slick Polygon
```

1. **Adaptive Speckle Filtering:** $5 \times 5$ local window variance reduction to remove multiplicative radar speckle noise.
2. **Coastal Land Masking:** High backscatter thresholding ($> -4.0 \, \text{dB}$) with morphological dilation to shield the eastern Sri Lankan coastline.
3. **Adaptive CFAR Dark Segmentation:** Dynamic local thresholding $T(r, c) = \mu_{\text{local}} - 1.8 \cdot \sigma_{\text{local}}$ to isolate radar dampening zones.
4. **Connected Components & Polygon Vectorization:** Morphological closing and contour tracing into GeoJSON polygons.
5. **Lookalike Classification (`ExplainableRuleSARClassifier`):**
   - **Accepted Mineral Oil Slick:** Damping contrast $\Delta\text{dB} = 6.8 \, \text{dB}$, area $= 18.45 \, \text{km}^2$, elongation ratio $= 3.2$, major axis orientation $= 52^\circ$ (aligned with southwest monsoon drift).
   - **Rejected Low-Wind Lookalike:** Large diffuse calm basin in southeast ($> 150 \, \text{km}^2$, weak damping $\Delta\text{dB} = 2.1 \, \text{dB}$) flagged with explicit audit reason.
   - **Rejected Coastal Shadow:** Dark patch within $0.8 \, \text{km}$ of coast flagged as land shadow.

---

## 3. Visual Diagnostics Reference

The multi-panel diagnostic output has been generated at [`docs/new_diamond_sar_diagnostics.png`](file:///c:/Projects/Maritime_Oil/docs/new_diamond_sar_diagnostics.png):

```
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│ 1. Original SAR Backscatter     │ 2. Preprocessed / Filtered      │ 3. Coastal Land Mask            │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│ 4. Adaptive CFAR Dark Segments  │ 5. Extracted Candidates & Types │ 6. Selected Primary Slick       │
└─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

---

## 4. Documented Scientific Limitations (`GEMINI.md` Notice)

> [!WARNING]
> **Scientific Limitations Notice:**
> 1. **Wind-Speed Operational Envelope:** SAR oil detection is scientifically reliable only in surface winds between $3.0 \, \text{m/s}$ and $12.0 \, \text{m/s}$. In extreme calm ($< 2.5 \, \text{m/s}$), natural surfactant lookalikes cannot be differentiated from light mineral oil with 100% certainty from single-channel SAR.
> 2. **Thickness & Emulsification:** Single-channel SAR backscatter detects surface capillary wave damping but cannot quantify slick thickness or water-in-oil emulsification state.
> 3. **Baseline Status:** The current rule-based classifier is an explainable baseline for decision support; production deployments should train the `BaseSARClassifier` interface against extensive satellite collections.
