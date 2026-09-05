# Specialized Coding Agents Plan

## Project: Maritime Oil-Spill Attribution Intelligence (SIH26143)

---

## 1. Agent Squad Roles & Responsibilities

To implement the platform with high engineering rigor, clean separation of concerns, and zero architectural drift, we organize development into **7 Specialized Agent Roles**:

```
                              ┌────────────────────────┐
                              │     LEAD ENGINEER      │
                              │ (Architect & Reviewer) │
                              └───────────┬────────────┘
                                          │
    ┌───────────────────────┬─────────────┴───────────────┬───────────────────────┐
    │                       │                             │                       │
┌───▼─────────────┐ ┌───────▼─────────────┐ ┌─────────────▼─────────┐ ┌───────────▼─────────────┐
│  DATA ENGINEER  │ │    SAR DETECTION    │ │    DRIFT & PHYSICS    │ │ ATTRIBUTION FORENSICS │
│                 │ │       ENGINEER      │ │       ENGINEER        │ │        ENGINEER       │
│ - Schemas       │ │ - Preprocessing     │ │ - Reverse Advection   │ │ - Multi-Factor Score  │
│ - Benchmarks    │ │ - Dark Patch Seg    │ │ - Wind & Currents     │ │ - Evidence Dossier    │
│ - Storage/DB    │ │ - Feature Vector    │ │ - Probability Cloud   │ │ - Explainability Math │
└───┬─────────────┘ └───────┬─────────────┘ └─────────────┬─────────┘ └───────────┬─────────────┘
    │                       │                             │                       │
    └───────────────────────┼─────────────────────────────┼───────────────────────┘
                            │                             │
                    ┌───────▼─────────────┐       ┌───────▼─────────────┐
                    │  FRONTEND ENGINEER  │       │     QA & TEST       │
                    │                     │       │     ENGINEER        │
                    │ - React / Leaflet   │       │ - Pytest Suites     │
                    │ - Timeline Scrubber │       │ - Golden Benchmarks │
                    │ - Evidence UI       │       │ - Coverage & Audit  │
                    └─────────────────────┘       └─────────────────────┘
```

---

## 2. Detailed Agent Profiles

### 2.1 Lead Engineer (System Architect & Pipeline Orchestrator)
- **Primary Focus:** High-level system architecture, FastAPI orchestration, repository structure, API contract adherence, and code quality.
- **Key Files:** `backend/app/main.py`, `backend/app/api/`, `backend/app/core/orchestrator.py`.
- **Guidelines:** Ensures modules remain loosely coupled, stateless, and adhere strictly to `API_CONTRACT.md` and `ARCHITECTURE.md`.

### 2.2 Data Engineer (Data Models & Synthetic Fixtures)
- **Primary Focus:** Pydantic schemas, spatial serialization (GeoJSON), synthetic scenario generators, and data persistence.
- **Key Files:** `backend/app/models/`, `backend/app/data/synthetic_scenarios.py`.
- **Guidelines:** Guarantees deterministic, reproducible mock data fixtures for all 4 benchmark scenarios.

### 2.3 SAR Detection Engineer (Computer Vision & Remote Sensing)
- **Primary Focus:** SAR image preprocessing, dark-spot segmentation algorithms (CFAR, Otsu, U-Net wrapper), and polygon feature extraction (area, centroid, orientation).
- **Key Files:** `backend/app/engines/sar_engine.py`, `backend/app/engines/sar_features.py`.
- **Guidelines:** Must provide both an algorithmic computer vision pipeline and an instant deterministic mock provider.

### 2.4 Drift Engineer (Oceanographic & Atmospheric Physics)
- **Primary Focus:** Backward Lagrangian particle tracking, advection integration (Runge-Kutta 4 / Euler), wind leeway and current vector field interpolation, Monte Carlo dispersion clouds.
- **Key Files:** `backend/app/engines/drift_engine.py`, `backend/app/engines/metocean_provider.py`.
- **Guidelines:** Ensures backward time integration is physically sound ($-\vec{u}_{\text{current}} - 0.03 \cdot \vec{u}_{\text{wind}}$) and computes tight convex hull probability envelopes.

### 2.5 Attribution Forensics Engineer (Maritime Intelligence & Scoring)
- **Primary Focus:** Spatiotemporal AIS intersection, track interpolation, dark-ship gap analysis, multi-factor explainable scoring matrix, and PDF/JSON dossier generation.
- **Key Files:** `backend/app/engines/ais_interceptor.py`, `backend/app/engines/attribution_engine.py`, `backend/app/services/dossier_service.py`.
- **Guidelines:** Never use black-box unexplainable calculations. Every point awarded or deducted must have an explicit mathematical rationale and human-readable `EvidenceItem`.

### 2.6 Frontend Engineer (Geospatial Visualization & UX)
- **Primary Focus:** Interactive web UI (React, Vite, Tailwind CSS, Leaflet/MapLibre), synchronized temporal playback slider, candidate ranking cards, radar charts, and PDF dossier viewer.
- **Key Files:** `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/api/`.
- **Guidelines:** Ensure fast, responsive map rendering with smooth scrubbing across historical hours.

### 2.7 QA & Test Engineer (Verification & Benchmarking)
- **Primary Focus:** Unit tests, integration tests, golden benchmark scenarios (Rogue Tanker, Crossed Paths, Blind Zone, Lookalike), and edge case validation.
- **Key Files:** `tests/unit/`, `tests/integration/`, `tests/fixtures/`.
- **Guidelines:** Ensure 100% pass rate on golden benchmark scenarios before any release milestone.
