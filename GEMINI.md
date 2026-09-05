# Permanent Engineering Rules & Guidelines

**Project:** Maritime Oil-Spill Attribution Intelligence (SIH26143)  
**Workspace Configuration:** `GEMINI.md`

---

## 1. Project Principles

- **Historical Investigation Focus:** This system is a **historical maritime oil-spill forensic investigation platform**, not a real-time reactive alarm.
- **Decision Support System:** The platform provides **decision support and explainable intelligence**, never an automated legal accusation or verdict.
- **Core Forensic Pipeline:** Every analysis strictly follows this sequenced data flow:
  ```
  SAR Imagery
  → Slick Detection & Feature Extraction
  → Backward Drift Simulation
  → Origin Estimation & Release Window
  → AIS Candidate Vessel Detection & Interpolation
  → Multi-Factor Attribution Scoring
  → Verifiable Evidence Chain
  → Forensic Investigation Report / Dossier
  ```

---

## 2. Beginner-First Development

- **Simplicity First:** Prefer transparent, interpretable, and simple algorithmic implementations before attempting complex deep learning or advanced ML.
- **Documented Decisions:** Explain all major architectural and algorithmic decisions clearly in project documentation.
- **Zero Hidden Complexity:** Never conceal architectural complexity, assumptions, or technical debt from the project owner.
- **Documented Scientific Assumptions:** Never make implicit assumptions about oceanographic, meteorological, or satellite data without explicit inline documentation and docstrings.

---

## 3. Data Integrity

- **Zero Data Fabrication:** Never fabricate real-world satellite, meteorological, or AIS data.
- **Explicit Synthetic Labeling:** All synthetic datasets, scenarios, and fixtures must be explicitly tagged and labeled as `synthetic: true` / `SYNTHETIC`.
- **Observation vs. Model Output:** Always clearly distinguish between directly observed sensor data (e.g., raw SAR backscatter, raw AIS pings) and model-derived data (e.g., segmented slick polygon, interpolated coordinates, drift probability clouds).
- **Universal UTC Timestamps:** All internal timestamps, database records, calculations, and API models must strictly use ISO 8601 UTC (`datetime.timezone.utc` / `Z`).
- **Source Metadata Preservation:** Preserve original sensor, satellite platform, provider metadata, and processing lineage across all pipeline stages.

---

## 4. Scientific Integrity & Attribution Phrasing

- **Uncertainty Representation:** Never present estimated spill origins, drift paths, or release windows as exact coordinates. Always convey them as probability distributions, dispersion envelopes, or confidence intervals.
- **Statistical Calibration:** Do not refer to attribution scores as "legal probabilities of guilt" unless statistically calibrated against ground-truth validation datasets.
- **Non-Accusatory Forensics:** Never state that a vessel "definitely caused a spill" or "is guilty".
  - **Required Forensic Wording:** Use objective, evidence-based statements such as:  
    > *"This vessel is the highest-ranked candidate based on the available spatial, temporal, and navigational evidence."*

---

## 5. Architecture & Separation of Concerns

Keep the following layers strictly decoupled and isolated:
- **Data Loading:** Ingestion, parsing, and validation of raw SAR GeoTIFFs, NetCDF weather grids, and AIS CSVs.
- **Scientific Calculations:** Pure mathematical, geometric, and physical engines (Lagrangian drift advection, CFAR thresholding, spline interpolation).
- **Business & Forensics Logic:** Attribution scoring matrices, risk classification, and evidence assembly.
- **API & Orchestration:** FastAPI controllers, routing, request validation, and pipeline task dispatch.
- **Frontend Presentation:** React / Vite / Leaflet user interface, time scrubber, and map visualizations.

**Typed Contracts:** Always use strongly-typed models (Pydantic / TypeScript schemas) at the boundaries between all modules.

---

## 6. Testing & Determinism

- **Deterministic Scientific Tests:** Every scientific, mathematical, and algorithmic component must have deterministic unit and integration tests.
- **Fixed Random Seeds:** All stochastic and Monte Carlo processes (e.g., particle diffusion perturbation) must use fixed random seeds in tests to ensure 100% reproducible results.
- **Benchmark Suite:** Maintain golden test scenarios (e.g., Rogue Tanker, Crossed Paths, Blind Zone, Lookalike Rejection) with expected mathematical tolerances.

---

## 7. Scope Boundaries (Out of Scope for MVP)

Do **NOT** implement the following unless explicitly requested in writing:
- Live global satellite constellation monitoring.
- Real-time India-wide / worldwide AIS streaming ingestion.
- Native mobile applications (iOS / Android).
- Research-grade 3D hydrodynamic / multi-phase oil weathering physics simulations.
- Automated legal conclusions, subpoenas, or enforcement triggers.

---

## 8. Implementation Protocol

Before executing any major implementation step, always follow this 6-step checklist:

1. **Inspect:** Examine existing codebase, models, and interfaces.
2. **Explain:** Present a clear, concise implementation plan to the user.
3. **Implement:** Build the smallest useful, self-contained increment.
4. **Test:** Write and run automated unit/integration tests verifying the increment.
5. **Verify:** Confirm the code behaves correctly without side-effects.
6. **Document:** Update relevant documentation, schema files, and walkthrough logs.

**Preservation Rule:** Do not refactor or rewrite working code unnecessarily.
