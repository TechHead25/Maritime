# Product Requirements Document (PRD)
## Project Title: Maritime Oil-Spill Attribution Intelligence
**Problem Statement ID:** SIH26143  
**Domain:** Maritime Domain Awareness, Environmental Forensics, Remote Sensing, Geospatial AI  

---

## 1. Executive Summary & Objective

Illegal and accidental maritime oil discharges cause catastrophic ecological and economic damage. While Synthetic Aperture Radar (SAR) imagery enables all-weather, day-and-night detection of oil slicks on the ocean surface, identifying the specific vessel responsible ("attribution") remains a major challenge due to:
1. **Ocean Dynamics:** Wind and ocean surface currents move and deform the slick between release time and satellite observation time.
2. **Temporal Gaps:** Satellite revisit intervals mean slicks are observed hours or days after the actual discharge.
3. **AIS Spoofing & Dark Ships:** Vessels engaging in illicit discharges often turn off, manipulate, or degrade their Automatic Identification System (AIS) transponders.

### System Goal
To build a modular, explainable, and end-to-end **Historical Maritime Oil-Spill Attribution Intelligence Platform** that ingests SAR imagery, segments oil slicks, computes backward Lagrangian/hydrodynamic drift trajectories to locate historical release windows, correlates spatiotemporally with historical AIS vessel tracking data, and produces an auditable, multi-factor attribution score with a human-verifiable evidence dossier.

---

## 2. Core Workflow & Pipeline Stages

```
[ SAR Imagery ]
       │
       ▼
[ 1. Slick Detection & Feature Extraction ] (Segmentation, Shape, Area, Confidence)
       │
       ▼
[ 2. Backward Drift Trajectory Simulation ] (Wind & Surface Current Advection)
       │
       ▼
[ 3. Release Window & Probability Cloud ] (Origin Area & Release Timestamp Estimation)
       │
       ▼
[ 4. Spatiotemporal AIS Interception ] (Historical AIS Candidate Search & Interpolation)
       │
       ▼
[ 5. Explainable Attribution Scoring Engine ] (Proximity, Drift Alignment, Speed, Type, AIS Anomalies)
       │
       ▼
[ 6. Interactive Web Dashboard & Dossier Export ] (Map Visualization, Timeline, PDF/JSON Report)
```

---

## 3. Detailed Scope & Functional Requirements

### 3.1 Module 1: SAR Scene Ingestion & Slick Detection
- **Input:** SAR scenes (Sentinel-1 GRD / synthetic test arrays in GeoTIFF / NetCDF / PNG format).
- **Core Processing:**
  - Preprocessing: Calibration, speckle filtering (Lee filter), land masking (GSHHG/SRTM), wind-masking.
  - Oil Slick Segmentation: Deep learning segmentation (U-Net / ResNet-UNet) or adaptive thresholding (CFAR / Otsu on dark patch anomalies) to classify oil slicks vs lookalikes (low wind areas, biogenic slicks, upwelling).
  - Feature Extraction: Slick polygon geometry (GeoJSON), centroid coordinate, surface area ($\text{km}^2$), orientation angle, perimeter-to-area ratio, detection confidence score.
- **Output:** Structured `SlickDetection` record linked to the `SARScene`.

### 3.2 Module 2: Backward Drift Simulation (Lagrangian Back-Tracking)
- **Input:** Slick polygon geometry, centroid, SAR observation timestamp $T_{\text{obs}}$, oceanographic current data ($U, V$ vectors) and surface wind data ($W_u, W_v$ vectors).
- **Core Processing:**
  - Back-projection / Reverse Lagrangian particle tracking:
    $$\vec{v}_{\text{particle}} = \vec{u}_{\text{current}} + \alpha \cdot \vec{u}_{\text{wind}} + \vec{u}_{\text{diffusion}}$$
    where $\alpha \approx 0.03$ (3% wind drift factor, with wind leeway deflection angle if applicable).
  - Reverse time steps: From $T_{\text{obs}}$ backwards to $T_{\text{obs}} - \Delta t_{\text{max}}$ (e.g., up to 24–72 hours).
  - Monte Carlo perturbation: Injects turbulence/uncertainty to generate an evolving **Probability Cloud** (search ellipse or convex hull envelope).
- **Output:** `DriftSimulation` comprising trajectory paths, origin probability envelopes, and calculated `ReleaseWindow` intervals.

### 3.3 Module 3: AIS Ingestion & Candidate Vessel Interception
- **Input:** Release probability envelopes, release time window $[T_{\text{start}}, T_{\text{end}}]$, AIS trajectory database (MMSI, IMO, vessel name, vessel type, timestamped coordinates, SOG, COG, navigational status).
- **Core Processing:**
  - Spatiotemporal bounding box query to filter all historical vessel tracks intersecting the probability cloud during the release window.
  - Track interpolation: Linear / cubic spline interpolation to estimate precise vessel position at time $t$ between sparse AIS pings.
  - Anomaly detection: Flagging AIS "dark gaps" (transponder switched off), abnormal speed drops, sudden course alterations near the probability cloud.
- **Output:** List of `CandidateVessel` entities with associated `VesselTrack` snippets and proximity metrics.

### 3.4 Module 4: Multi-Factor Explainable Attribution Engine
- **Input:** Candidate vessels, vessel tracks, slick origin probability cloud, release window.
- **Core Processing:**
  Computes a composite, weighted attribution score $S_{\text{attr}} \in [0, 100]$ based on deterministic, explainable factors:
  1. **Spatiotemporal Proximity ($w_1 \approx 0.35$):** Minimum distance between interpolated vessel position and the high-density drift origin center at release time.
  2. **Trajectory Alignment & Drift Consistency ($w_2 \approx 0.25$):** Cosine similarity / vector alignment between vessel heading and slick dispersion axis.
  3. **Vessel Risk & Type Profile ($w_3 \approx 0.15$):** Tankers, crude carriers, cargo vs non-polluting small craft.
  4. **Behavioral & Navigational Anomaly ($w_4 \approx 0.15$):** Slowing down, loitering, zig-zagging in open ocean during release window.
  5. **AIS Integrity Penalty ($w_5 \approx 0.10$):** High score boost if vessel turned off AIS right before or inside the release zone.
- **Output:** `AttributionScore` and a breakdown of individual `EvidenceItem` records per candidate.

### 3.5 Module 5: Investigation Dashboard & Dossier Export
- **Web UI Capabilities:**
  - Dual map layers: SAR backscatter layer, segmented slick polygon, drift probability cloud overlay, historical vessel trajectories (color-coded by rank).
  - Playback Timeline: Slider allowing investigators to scrub time from $T_{\text{obs}}$ back to $T_{\text{release}}$ and see particles and ships move in sync.
  - Evidence Dossier Panel: Ranked candidate list, radar chart/breakdown of factor scores, vessel metadata (IMO, flag, destination, draft).
  - One-Click Report Generator: Export formal forensic PDF & JSON audit dossier containing hashes, methodology, maps, and ranked evidence.

---

## 4. Requirement Categorization (MVP vs. Future Roadmap)

| Feature / Capability | MVP (Phase 1–4) | Future Roadmap (Post-MVP) |
|---|---|---|
| **Slick Input** | GeoJSON slick polygons + synthetic/preprocessed SAR GeoTIFFs | Automated live Sentinel-1 GRD pipeline via Copernicus API |
| **Slick Segmentation** | Pre-trained deep learning model / adaptive Otsu-CFAR segmentation | Full multi-sensor fusion (Sentinel-1 SAR + Sentinel-2 Optical + Landsat) |
| **Drift Simulation** | 2D backward Lagrangian advection with synthetic/mock current & wind grids + NOAA GFS/HYCOM stub | Full 3D hydrodynamic & weathering model (evaporation, emulsification, Stokes drift) |
| **AIS Data** | Synthetic deterministic AIS datasets & historical CSV/Parquet replays | Live real-time AIS feeds (AISHub, Spire, MarineTraffic streaming) |
| **Attribution Engine** | 5-factor deterministic explainable scoring matrix | Bayesian Graph Neural Network + maritime legal compliance database |
| **User Interface** | Interactive Leaflet/MapLibre UI with timeline scrubber & evidence table | 3D bathymetric ocean viewer with dark-vessel satellite optical search |
| **Reporting** | Printable HTML-to-PDF forensic investigation dossier & JSON export | Digitally signed, tamper-proof blockchain audit trail for legal court submission |

---

## 5. Non-Functional Requirements

1. **Determinism & Reproducibility:** Given identical SAR input, wind/current fields, and AIS logs, the drift simulation and attribution score must produce 100% identical outputs.
2. **Performance:**
   - Slick segmentation $\le 5$ seconds for standard region-of-interest patch.
   - Backward drift simulation ($10,000$ particles, 48-hour window) $\le 3$ seconds.
   - Candidate ranking for up to 100 vessels $\le 2$ seconds.
   - End-to-end case execution $\le 10$ seconds.
3. **Modularity:** Every pipeline stage must be a decoupled service or python module that can be tested, mocked, or replaced independently.
4. **Explainability:** Zero black-box ranking. Every point in the attribution score must cite specific mathematical and physical evidence.
5. **Portability:** Containerizable via Docker, runnable locally on Windows/Linux/macOS with zero mandatory cloud GPU dependencies for mock/testing modes.
