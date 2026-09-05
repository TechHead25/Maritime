# Maritime Oil-Spill Attribution Intelligence (SIH26143)

> **A Historical Maritime Forensics Platform that connects Satellite Radar (SAR) Oil Slicks to Offending Vessels using Reverse Ocean Drift & AIS Spatiotemporal Correlation.**

---

## 🌊 What is This Project?

When oil is illegally or accidentally discharged into the ocean:
1. Satellites capture a radar image (SAR) of the dark slick hours or days later.
2. The ocean has already moved the slick far away from where it was originally dumped.
3. Ships may have sailed away or turned off their tracking transponders (AIS).

**This platform solves the mystery by:**
- **Finding the slick** in SAR imagery.
- **Rewinding ocean currents and wind backwards in time** (Lagrangian drift simulation) to locate the exact "crime scene" (Probability Cloud & Release Window).
- **Matching historical ship tracks (AIS)** with that origin area.
- **Calculating an explainable, court-admissible Attribution Score** for every candidate vessel.
- **Providing an interactive web dashboard and downloadable forensic dossier.**

---

## 📚 Project Documentation & Specifications

Before writing code, review the core architectural blueprints in this directory:

- 📄 [`PRD.md`](./PRD.md) — Product Requirements & Scope (MVP vs. Future).
- 🏗️ [`ARCHITECTURE.md`](./ARCHITECTURE.md) — Complete system architecture & data flow diagrams.
- 🗺️ [`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md) — Step-by-step implementation phases.
- 📐 [`DATA_MODEL.md`](./DATA_MODEL.md) — Detailed schemas for all 10 core domain entities.
- 🔌 [`API_CONTRACT.md`](./API_CONTRACT.md) — RESTful API endpoints and JSON request/response formats.
- 🧪 [`TESTING_PLAN.md`](./TESTING_PLAN.md) — Unit, integration, and golden benchmark test scenarios.
- 🤖 [`AGENT_PLAN.md`](./AGENT_PLAN.md) — Specialized coding agent squad roles and task allocations.

---

## 🚀 Beginner Quickstart (How to Run When Implementation Begins)

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- Git

### 1. Backend Setup
```bash
# Navigate to project root
cd c:/Projects/Maritime_Oil

# Create and activate virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Start the FastAPI backend server
uvicorn backend.app.main:app --reload --port 8000
```
- API Docs (Swagger UI): `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
# In a new terminal tab:
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:5173`

### 3. Running Automated Tests
```bash
# Run all unit tests and golden benchmark scenarios
pytest -v
```

---

## 📂 Repository Layout (Target Structure)

```
Maritime_Oil/
├── PRD.md
├── ARCHITECTURE.md
├── DEVELOPMENT_PLAN.md
├── DATA_MODEL.md
├── API_CONTRACT.md
├── TESTING_PLAN.md
├── AGENT_PLAN.md
├── README.md
│
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI App Entrypoint
│   │   ├── api/                   # REST Route Controllers
│   │   ├── models/                # Pydantic Core Data Schemas
│   │   ├── engines/               # Scientific Analytics Engines
│   │   │   ├── sar_engine.py      # SAR Slick Detection & Features
│   │   │   ├── drift_engine.py    # Backward Lagrangian Drift
│   │   │   ├── ais_interceptor.py # AIS Trajectory Search & Interpolation
│   │   │   └── attribution.py     # Explainable Scoring Engine
│   │   ├── services/              # Dossier Generator & Exporter
│   │   └── data/                  # Synthetic Scenario Benchmarks
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/            # Map, Timeline, Leaderboard, Dossier
│   │   ├── hooks/                 # Data Fetching & State
│   │   └── App.tsx                # Main Application Shell
│   └── package.json
│
└── tests/
    ├── unit/                      # Math & Schema Unit Tests
    ├── integration/               # Pipeline & API Tests
    └── fixtures/                  # Benchmark Synthetic Scenarios
```
