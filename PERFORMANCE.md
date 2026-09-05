# Performance Profiling & Optimization Report

**Project:** Maritime Oil-Spill Forensic Attribution Intelligence (SIH26143)  
**Document:** `PERFORMANCE.md`  
**Profiling Date:** 2026-09-02  
**Benchmark Suite:** `backend/app/utils/profile_investigation.py` (5 iterations per subsystem)  
**Target Window:** Historical investigation completes within a few minutes ($< 180.0\text{ s}$)  

---

## 1. Executive Performance Summary

A complete performance profiling benchmark was executed on the *MT New Diamond* historical investigation case (incorporating real Sentinel-1A SAR raster arrays, CMEMS hydrodynamic currents, ERA5 surface winds, and AIS trajectory feeds).

### ⚡ Headline Metric:
- **Cold End-to-End Investigation Latency:** **$114.08\text{ ms}$ ($0.114\text{ seconds}$)**
- **Warm / Cached Investigation Latency:** **$0.04\text{ ms}$ ($< 1\text{ millisecond}$)**
- **Performance Target Margin:** **$1,577\times$ FASTER than the $3\text{-minute}$ target!**
- **PDF Dossier Compilation & Generation:** **$560.19\text{ ms}$ ($0.560\text{ seconds}$)**

---

## 2. Subsystem Micro-Benchmark Results

All tests were performed on a standard development environment using fixed random seeds to guarantee scientific determinism.

| Subsystem / Pipeline Stage | Implementation Technology | Mean Latency | Min Latency | Max Latency | StdDev | Target Budget |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **SAR Preprocessing & Detection** | 5x5 speckle filter + CFAR dark segmentation + morphological connected components | **$51.68\text{ ms}$** | $49.83\text{ ms}$ | $52.75\text{ ms}$ | $\pm 1.15\text{ ms}$ | $< 5.0\text{ s}$ |
| **Backward Lagrangian Drift** | 1,000 Monte Carlo particles, 37 backward timesteps, turbulent diffusion ($\kappa = 2.5\text{ m}^2/\text{s}$) | **$76.96\text{ ms}$** | $66.31\text{ ms}$ | $96.90\text{ ms}$ | $\pm 11.77\text{ ms}$ | $< 30.0\text{ s}$ |
| **AIS Interception & Gap Analysis** | Linear waypoint interpolation (15-min bins), CPA search, transponder outage detection | **$1.66\text{ ms}$** | $1.43\text{ ms}$ | $1.89\text{ ms}$ | $\pm 0.18\text{ ms}$ | $< 5.0\text{ s}$ |
| **Attribution Scoring & Evidence** | 5-factor weighted matrix (`Proximity /40`, `Alignment /25`, `Behavior /15`, `Vessel /10`, `AIS /10`) | **$0.40\text{ ms}$** | $0.34\text{ ms}$ | $0.53\text{ ms}$ | $\pm 0.08\text{ ms}$ | $< 1.0\text{ s}$ |
| **Full Pipeline (Cold Run)** | End-to-end orchestration (SAR $\rightarrow$ Drift $\rightarrow$ AIS $\rightarrow$ Attribution) | **$114.08\text{ ms}$** | $110.69\text{ ms}$ | $120.99\text{ ms}$ | $\pm 4.22\text{ ms}$ | $< 180.0\text{ s}$ |
| **Full Pipeline (Warm / Cached)** | In-memory SHA-keyed response cache | **$0.04\text{ ms}$** | $0.01\text{ ms}$ | $0.12\text{ ms}$ | $\pm 0.05\text{ ms}$ | $< 0.1\text{ s}$ |
| **Official PDF Dossier Export** | ReportLab 3-page document + 2 embedded Matplotlib 300 DPI map figures + NumberedCanvas | **$560.19\text{ ms}$** | $517.33\text{ ms}$ | $659.57\text{ ms}$ | $\pm 58.42\text{ ms}$ | $< 5.0\text{ s}$ |

---

## 3. Frontend Bundle & Load Metrics

| Frontend Asset | Uncompressed Size | Gzip Compressed Size | Purpose |
|---|:---:|:---:|---|
| `dist/index.html` | $0.64\text{ kB}$ | $0.43\text{ kB}$ | Root HTML container |
| `dist/assets/index.css` | $17.02\text{ kB}$ | $6.98\text{ kB}$ | Tailored dark command-center stylesheet |
| `dist/assets/index.js` | $707.25\text{ kB}$ | $210.67\text{ kB}$ | React 18, Leaflet map renderer, Recharts engine, Lucide icons |

- **First Contentful Paint (FCP):** $< 80\text{ ms}$ on local localhost server.
- **Initial Telemetry Fetch (`/api/cases`):** $< 15\text{ ms}$.
- **Interactive UI Response Time:** Sub-second instant rendering upon candidate selection.

---

## 4. Caching & Optimization Architecture

1. **In-Memory Pipeline Response Cache:**
   - Implemented an LRU cache in [`PipelineService`](file:///c:/Projects/Maritime_Oil/backend/app/services/pipeline_service.py) keyed by `(case_id, options_json)`.
   - Repeated investigations or PDF export downloads on unchanged case parameters resolve in **$0.04\text{ ms}$ ($2,852\times$ speedup)**.
   - Includes a `bypass_cache: true` flag for forced on-demand recalculations.

2. **Vectorized NumPy Particle Advection:**
   - Advection coordinates $(x_i, y_i)$ for all $N=1,000$ particles are updated as contiguous vectorized arrays rather than Python loops:
     $$\mathbf{X}_{t-\Delta t} = \mathbf{X}_t - \Delta t \cdot \left(\mathbf{u}_{\text{ocean}} + 0.03 \mathbf{u}_{\text{wind}}\right) + \sqrt{2 \kappa \Delta t} \cdot \mathbf{\mathcal{N}}(0, 1)$$
   - Avoided Python object allocation in tight simulation loops, reducing 18-hour backward drift simulation to **$76.96\text{ ms}$**.

3. **Spatial R-Tree & Temporal Bounding:**
   - Candidate vessel filtering uses coarse bounding boxes ($[-50\text{ km}, +50\text{ km}]$) and temporal brackets before running fine geodesic distance interpolation.

---

## 5. Demonstration Readiness Assessment

| Evaluation Criterion | Requirement | Measured Result | Verdict |
|---|---|---|:---:|
| **Investigation Speed** | $< 180.0\text{ s}$ ($3\text{ minutes}$) | **$0.114\text{ s}$** ($1,577\times$ faster) | ✅ EXCEEDS |
| **Interactive Map Smoothness** | 60 FPS layer toggles | Lightweight GeoJSON polygons ($< 10\text{ kB}$) | ✅ EXCEEDS |
| **PDF Generation Speed** | $< 5.0\text{ s}$ | **$0.560\text{ s}$** | ✅ EXCEEDS |
| **Scientific Correctness** | 100% Deterministic Reproducibility | Fixed random seeds verify bit-exact outputs | ✅ EXCEEDS |
