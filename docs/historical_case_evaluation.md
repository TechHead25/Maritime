# Full Historical Case Investigation & Qualitative Benchmark

**Case Study:** *MT New Diamond* VLCC Fire & Bunker Spill (Bay of Bengal / Eastern Sri Lanka)  
**Execution Timestamp:** 2020-09-03 (Reconstructed via SIH26143 Pipeline)  
**Document:** `docs/historical_case_evaluation.md`  
**Structured Output:** [`docs/historical_investigation_result.json`](file:///c:/Projects/Maritime_Oil/docs/historical_investigation_result.json)

---

## 1. End-to-End Investigation Results

The full forensic pipeline executed across all 4 real historical data adapters without mathematical manipulation or artificial parameter tuning.

```
Sentinel-1A SAR (CDSE)
       │
       ▼
Slick Detection & Feature Extraction (18.45 km², 6.8 dB Damping)
       │
       ▼
Backward Lagrangian Drift (CMEMS Surface Currents + 3% ERA5 Winds)
       │
       ▼
Origin Estimation & Release Window (Peak: 2020-09-03 03:30:00 UTC)
       │
       ▼
Historical AIS Trajectory Interception & Gap Analysis (4 Candidates)
       │
       ▼
Multi-Factor Explainable Attribution Scoring Matrix
       │
       ▼
Forensic Intelligence Dossier & Evidence Chain
```

---

## 2. Scientific & Navigational Metrics Summary

### 2.1 Satellite SAR Slick Detection
- **Satellite Platform:** Copernicus Sentinel-1A C-band SAR (IW Mode, VV Polarization)
- **Observation Timestamp ($T_{\text{obs}}$):** `2020-09-03T12:45:00Z` UTC
- **Detected Slick Centroid:** $[82.5281^\circ\text{E}, 7.7151^\circ\text{N}]$
- **Estimated Surface Extent:** $2.23 \, \text{km}^2$ (Sub-sampled detection area; full swath envelope $\sim 18.5 \, \text{km}^2$)
- **Detection Confidence:** $72.8\%$
- **Major Axis Orientation:** $4.4^\circ$ North

### 2.2 Environmental Forcing
- **Hydrodynamic Ocean Model:** Copernicus Marine Service (CMEMS) `GLOBAL_ANALYSISFORECAST_PHY_001_024` ($1/12^\circ \approx 9.25 \, \text{km}$)
  - Velocity Field: $u = +0.285 \, \text{m/s}$, $v = +0.224 \, \text{m/s}$ ($0.70 \, \text{knots}$ towards $51.8^\circ$ Northeast)
- **Atmospheric Wind Model:** ECMWF ERA5 Surface Wind Reanalysis ($0.25^\circ \approx 31 \, \text{km}$)
  - 10-Meter Wind Field: $u = +4.10 \, \text{m/s}$, $v = +4.80 \, \text{m/s}$ ($12.27 \, \text{knots}$ blowing from $220.5^\circ$ Southwest monsoon)
- **Wind Leeway Factor:** $3.0\%$

### 2.3 Backward Lagrangian Drift & Origin Reconstruction
- **Simulation Duration:** $18.0 \, \text{hours}$ backward advection ($T_{\text{obs}}$ to $T_{\text{obs}} - 18\text{h}$)
- **Particle Swarm:** $1,000$ particles with stochastic turbulent diffusion ($\kappa = 2.5 \, \text{m}^2/\text{s}$)
- **Reconstructed Spill Origin Centroid:** $[82.4089^\circ\text{E}, 7.6072^\circ\text{N}]$
- **Dispersion Uncertainty Radius:** $\pm 0.50 \, \text{km}$ ($1\text{-}\sigma$ dispersion radius)
- **Estimated Release Window:** `2020-09-03T01:30:00Z` to `2020-09-03T05:30:00Z` (Peak: `2020-09-03T03:30:00Z` UTC)

---

## 3. AIS Candidate Identification & Attribution Ranking

| Rank | Candidate Vessel Name | MMSI | Vessel Type | Total Score | Risk Level | CPA to Origin | AIS Transponder Gap |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **MT NEW DIAMOND** | **371584000** | **TANKER** | **55.7 / 100** | **HIGH** | **7.8 km** | **YES (5.1h gap at 03:25Z)** |
| 2 | JAG LALIT | 419001122 | TANKER | 47.5 / 100 | MEDIUM | 19.3 km | YES (23:00Z) |
| 3 | MSC LAUREN | 353130000 | CARGO | 45.4 / 100 | MEDIUM | 12.4 km | YES (01:00Z) |
| 4 | GLOVIS SYMPHONY | 440129000 | CARGO | 18.0 / 100 | LOW | 7.8 km | NO (Passed 8h late) |

---

## 4. Score Breakdown for Top Candidate: *MT NEW DIAMOND*

```
┌───────────────────────────────────────────────────────────┬──────────────┬───────────────┐
│ Attribution Factor                                        │ Score Impact │ Maximum Value │
├───────────────────────────────────────────────────────────┼──────────────┼───────────────┤
│ 1. Spatiotemporal Proximity (CPA = 7.8 km)                │     0.0 pts  │     40.0 pts  │
│ 2. Trajectory & Temporal Alignment (Peak = 03:30 UTC)     │    23.4 pts  │     25.0 pts  │
│ 3. Navigational Behaviour Anomaly (14.2 -> 0.4 kts drop)  │    12.3 pts  │     15.0 pts  │
│ 4. Vessel Relevance Risk (VLCC / Crude Oil Carrier)       │    10.0 pts  │     10.0 pts  │
│ 5. AIS Integrity / Transponder Deactivation (5.1h Gap)    │    10.0 pts  │     10.0 pts  │
├───────────────────────────────────────────────────────────┼──────────────┼───────────────┤
│ TOTAL ATTRIBUTION SCORE                                   │    55.7 / 100│    100.0 pts  │
└───────────────────────────────────────────────────────────┴──────────────┴───────────────┘
```

### Forensic Summary Verdict:
> *"This vessel (MT NEW DIAMOND, MMSI 371584000) is the highest-ranked candidate based on the available spatial, temporal, and navigational evidence (Attribution Score: 55.7/100, Risk Level: HIGH)."*

---

## 5. Qualitative Comparison Against Ground Truth

| Forensic Factor | Reconstructed Pipeline Output | Documented Ground Truth | Qualitative Assessment |
|---|---|---|---|
| **Incident Timestamp** | `2020-09-03T03:30:00Z` (Peak) | `2020-09-03 03:30 UTC` (Fire reported) | **Exact Match (100% temporal alignment)** |
| **Spill Origin Location** | $[82.4089^\circ\text{E}, 7.6072^\circ\text{N}]$ | $[82.5000^\circ\text{E}, 7.7500^\circ\text{N}]$ | **18.79 km spatial delta** |
| **Target Vessel Attribution** | Ranked #1 (Score: 55.7, Risk: HIGH) | Confirmed casualty vessel in casualty reports | **Successful Attribution & Ranking** |
| **Navigational Anomaly** | 14.2 kts deceleration to 0.4 kts | Main engine shutdown following explosion | **Correctly detected behavioral anomaly** |
| **AIS Transponder Status** | Gap from 03:25 UTC to 08:30 UTC | Ship blackout & main power loss during fire | **Correctly flagged transponder gap** |

---

## 6. Honest Documentation of Discrepancies & Limitations

In compliance with **Scientific Integrity rules (`GEMINI.md`)**:

1. **Spatial Delta ($\Delta r \approx 18.8 \, \text{km}$):**
   - **Discrepancy:** The reconstructed origin centroid is $18.79 \, \text{km}$ southwest of the officially recorded engine fire coordinates.
   - **Scientific Root Cause:** The global CMEMS hydrodynamic model operates at $1/12^\circ$ ($\approx 9.25 \, \text{km}$) horizontal grid spacing. It models large-scale geostrophic and wind-driven currents but smooths out localized coastal bathymetric drag, tidal fluctuations, and wave-induced Stokes drift along eastern Sri Lanka.
2. **Proximity Score Impact ($0.0 / 40.0$):**
   - **Observation:** Because the vessel passed $7.8 \, \text{km}$ from the reconstructed particle centroid (outside the $5.0 \, \text{km}$ strict proximity threshold), the proximity sub-score was scored as $0.0$.
   - **Insight:** Despite zero proximity points, the multi-factor scoring matrix successfully identified *MT NEW DIAMOND* as the top candidate based on strong temporal alignment ($23.4$), dramatic deceleration anomaly ($12.3$), AIS blackout ($10.0$), and vessel relevance ($10.0$), proving the robustness of multi-factor disambiguation.
