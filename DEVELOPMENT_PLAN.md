# Development Plan

## Project: Maritime Oil-Spill Attribution Intelligence (SIH26143)

---

## 1. Development Philosophy

1. **Mock-First, Fully Runnable Increments:**  
   Every phase MUST produce a runnable, verified subsystem with automated unit tests before proceeding to the next.
2. **Deterministic Synthetic Scenarios:**  
   We develop against clean, parameterized synthetic scenarios (e.g., *Scenario Alpha: The Rogue Tanker in Malacca Strait*) before integrating unpredictable external remote sensing and oceanographic feeds.
3. **Strict Separation of Concerns:**  
   The system is developed in standalone modules (Domain Core $\rightarrow$ API Layer $\rightarrow$ Frontend UI $\rightarrow$ Forensic Reporting).

---

## 2. Phase-by-Phase Roadmap

### Phase 0: Project Setup & Core Data Contracts
- **Deliverable:** Fully configured repository with Python backend structure, typed data models (Pydantic), and synthetic scenario generator.
- **Tasks:**
  - Create directory layout (`backend/app`, `frontend`, `data/synthetic_scenarios`, `tests`).
  - Implement Pydantic data schemas for all 10 core entities (`InvestigationCase`, `SARScene`, `SlickDetection`, `DriftSimulation`, `ProbabilityCloud`, `ReleaseWindow`, `VesselTrack`, `CandidateVessel`, `AttributionScore`, `EvidenceItem`).
  - Create synthetic dataset generator that creates a golden test incident:
    - 1 SAR scene with an elongated slick polygon.
    - Uniform/vortical wind and ocean current vector field.
    - 5 AIS vessel tracks: 1 culprit tanker intersecting drift origin, 2 innocent passing cargo ships, 1 dark vessel with gap, 1 slow fishing boat.
- **Runnable Output:** `pytest` passing for data model validation and synthetic scenario generation.

---

### Phase 1: Drift Simulation & AIS Interceptor Engine
- **Deliverable:** Standalone Python engines that calculate reverse drift and find candidate vessels.
- **Tasks:**
  - Implement `DriftEngine`:
    - 2D reverse Lagrangian advection with Euler / Runge-Kutta 4 integrator.
    - Monte Carlo diffusion perturbation to output a multi-timestep `ProbabilityCloud` (convex hull / bounding ellipses).
    - Release window calculator based on particle age bounds.
  - Implement `AISInterceptor`:
    - Spatial bounding filter and timestamp filter.
    - Linear/spline interpolation between AIS position reports.
    - AIS gap / dark ship anomaly detector.
    - Closest Point of Approach (CPA) and spatiotemporal distance calculation.
- **Runnable Output:** Standalone CLI script `python -m app.engines.drift_and_ais_test` that runs reverse drift on synthetic slick, filters ships, and prints intercept coordinates.

---

### Phase 2: Explainable Attribution Engine & Forensic Dossier
- **Deliverable:** Attribution scoring matrix with full mathematical breakdown and PDF/JSON dossier builder.
- **Tasks:**
  - Implement `AttributionEngine`:
    - 5-factor scoring algorithms (Proximity, Drift Alignment, Vessel Profile, Navigational Anomaly, AIS Integrity).
    - Evidence item generator explaining the rationale behind each sub-score.
    - Final ranking and confidence band calculation ($[0-100]$ score).
  - Implement `DossierService`:
    - Generates structured JSON forensic audit log.
    - Generates HTML / PDF investigation report with summary, tables, and timestamped audit hashes.
- **Runnable Output:** CLI test verifying that Candidate #1 (the rogue tanker) gets $\ge 85\%$ score with clear evidence breakdown, while innocent ships receive low scores ($< 30\%$).

---

### Phase 3: SAR Detection Engine
- **Deliverable:** SAR dark-formation detection and feature extractor module.
- **Tasks:**
  - Preprocessing pipeline: Grayscale conversion, speckle noise reduction (Lee filter / bilateral filter), land masking.
  - Dark patch segmentation: Adaptive thresholding (CFAR / Otsu) with morphological filtering.
  - Slick vectorizer: Contours to GeoJSON polygon, calculation of centroid, area ($\text{km}^2$), major axis orientation, and lookalike rejection heuristics.
  - Provide fallback mock provider for direct GeoJSON/GeoTIFF upload.
- **Runnable Output:** CLI/script taking a sample SAR image and producing a valid `SlickDetection` GeoJSON object with exact coordinates.

---

### Phase 4: FastAPI Backend & End-to-End Orchestrator
- **Deliverable:** Complete RESTful API server coordinating all engines.
- **Tasks:**
  - Implement Case CRUD endpoints (`/api/v1/cases`).
  - Implement Pipeline execution endpoints (`/api/v1/cases/{case_id}/run-investigation`).
  - Implement individual step endpoints for granular UI control (`/detect-slick`, `/simulate-drift`, `/intercept-vessels`, `/score-attribution`).
  - Implement Dossier export endpoints (`/export-report.pdf`, `/export-dossier.json`).
- **Runnable Output:** FastAPI server running on `http://localhost:8000` with interactive Swagger docs (`/docs`) running full mock cases end-to-end.

---

### Phase 5: Modern Interactive Web Dashboard (React + Vite + Leaflet)
- **Deliverable:** Visual interface for maritime investigators.
- **Tasks:**
  - Setup React + TailwindCSS + Lucide Icons + Leaflet/MapLibre.
  - Map View:
    - Display SAR footprint & detected oil slick layer.
    - Animate reverse drift probability cloud over time.
    - Render vessel trajectories with color-coded attribution risk (Red = High, Orange = Med, Gray = Low).
  - Temporal Time Slider: Scrub through hours $[T_{\text{obs}} \rightarrow T_{\text{release}}]$ with synchronized ship and particle movements.
  - Candidate Leaderboard & Evidence Dossier Modal: View score breakdown, radar chart, vessel particulars, and download PDF dossier.
- **Runnable Output:** Fully interactive web app on `http://localhost:5173` communicating with FastAPI backend.

---

### Phase 6: Real-World Data Connectors & Packaging (Post-MVP)
- **Deliverable:** Optional live connectors and production containerization.
- **Tasks:**
  - Copernicus Sentinel-1 API downloader / STAC client.
  - NOAA GFS & HYCOM / Copernicus Marine (CMEMS) API client for live wind & current grids.
  - AIS CSV / Parquet bulk loader for real maritime feeds.
  - Complete `docker-compose.yml` spinning up backend, frontend, and worker.
- **Runnable Output:** Single `docker compose up` spinning up the entire production-ready system.
