# Smart India Hackathon (SIH) Presentation: Maritime Oil-Spill Attribution Intelligence

**Problem Statement ID:** SIH26143  
**Project Title:** Maritime Oil-Spill Attribution Intelligence Platform  
**Domain:** Space Technology / Environmental & Maritime Surveillance / AI & Forensics  

---

## Slide 1: Title & Problem Context

### Title & Subtitle
- **Header:** Maritime Oil-Spill Attribution Intelligence Platform
- **Sub-header:** AI-Powered Satellite Forensics, Backward Hydrodynamic Drift Inversion & AIS Telemetry Interception for Maritime Law Enforcement
- **Team / Category:** SIH26143 | Decision Support System for Maritime Authorities (Indian Coast Guard, DG Shipping, State Pollution Control Boards)

### The Critical National & Global Challenge
- **Undetected Illegal Discharges:** Over 80% of marine oil contamination results not from catastrophic tanker crashes, but from deliberate, illegal bilge cleaning and ballast washing under cover of darkness or in cloud-covered open seas.
- **The Attribution Gap:** By the time satellite imagery or aerial patrols detect an oil slick, hours or days have passed. Ocean currents and monsoon winds have drifted and dispersed the slick tens of nautical miles away from its release coordinates, while dozens of merchant vessels have transited through the corridor.
- **Current Operational Bottlenecks:**
  - Manual, disconnected analysis of optical/radar satellite images, weather archives, and AIS logs takes days to weeks.
  - Lack of backward drift modeling means authorities cannot pinpoint when and where the discharge occurred.
  - Absence of explainable evidence chains prevents legal accountability in maritime courts and under UNCLOS / MARPOL conventions.

---

## Slide 2: Proposed Solution & 6-Stage Forensic Pipeline

### Core Concept: "Reverse Time, Reconstruct Origin, Identify the Source"
A unified, physics-based decision-support intelligence platform that ingests multi-modal Earth Observation (EO) satellite data, oceanic hydrodynamics, and terrestrial/satellite AIS vessel telemetry to reconstruct spill lineage and calculate explainable vessel attribution scores.

### The 6-Stage End-to-End Forensic Workflow
```
[1. Spaceborne SAR Ingestion] 
   └── Sentinel-1 C-band Synthetic Aperture Radar (all-weather, day/night radar penetration)
[2. CFAR Detection & Lookalike Discrimination]
   └── Adaptive Gaussian CFAR thresholding with capillary suppression & lookalike rejection
[3. Backward Lagrangian Hydrodynamic Simulation]
   └── Inverted Runge-Kutta advection driven by Copernicus (CMEMS) currents + ECMWF ERA5 winds
[4. Origin Estimation & Release Window Reconstruction]
   └── Monte Carlo particle cloud dispersion envelopes & backward temporal probability bounds
[5. AIS Spatio-Temporal Interception & Interpolation]
   └── Cubic-spline trajectory interpolation & Closest Point of Approach (CPA) calculations
[6. Multi-Factor Attribution Scoring & Evidence Assembly]
   └── Weighted multi-criteria decision matrix + cryptographic SHA-256 evidence chain of custody
```

---

## Slide 3: Technical Architecture & Scientific Methodology

### Decoupled, Robust 4-Tier Architecture
1. **Sensor & Data Ingestion Layer:**
   - Real-time Copernicus Data Space Ecosystem (CDSE) STAC & OData API integration for Sentinel-1 GRD.
   - Global Marine Hydrodynamics: CMEMS GLORYS12V1 ocean currents ($u, v$ vectors at $1/12^\circ$ resolution).
   - Atmospheric Forcing: ECMWF ERA5 Reanalysis surface winds ($u_{10}, v_{10}$).
   - Terrestrial & Satellite AIS Ingestion: Live WebSocket streams and historical CSV archives.
2. **Deterministic Physics & Mathematical Engine:**
   - **Lagrangian Particle Tracking:** $\frac{d\vec{x}}{dt} = - (\vec{u}_{\text{current}} + \alpha_{\text{wind}} \vec{w}_{\text{wind}} + \vec{u}'_{\text{diffusion}})$
   - **Wind Leeway Factor:** Calibrated leeway factor ($\alpha = 0.03$ to $0.035$) with Coriolis deflection.
   - **Random Walk Diffusion:** Turbulent dispersion envelope parameterized by horizontal diffusivity $K_h = 10 \text{ m}^2/\text{s}$.
3. **Forensic Disambiguation & Lookalike Rejection:**
   - Discriminates true mineral hydrocarbons from natural biogenic slicks, low-wind calm basins ($<2.5\text{ m/s}$), and coastal radar shadows via edge contrast gradients and damping ratios ($>4.0\text{ dB}$).
4. **User & Reporting Layer:**
   - Interactive React/Vite web console with synchronized temporal scrubbers, Leaflet GIS mapping, and automated generation of audit-grade, court-ready PDF dossiers.

---

## Slide 4: Real-World Case Studies & Empirical Validation

### Benchmark 1: Ennore Kamarajar Port Tanker Collision (`case_ennore_2017`)
- **Incident:** Collision between LPG carrier *BW Maple* and crude oil tanker *Dawn Kanchipuram* off Chennai, spilling 251 tonnes of Heavy Fuel Oil (HFO).
- **Forensic Pipeline Execution:**
  - Ingested Sentinel-1A SAR radar pass acquired on Jan 29, 2017, 00:45 UTC.
  - Reconstructed 20.7 hours of backward Lagrangian drift against Bay of Bengal coastal currents.
  - Correctly intercepted *BW Maple* and *Dawn Kanchipuram* at the fairway intersection ($\text{CPA} < 0.05\text{ km}$); accurately ranked the collision pair as top candidates.

### Benchmark 2: MT New Diamond Fire & Bunker Discharge (`case_new_diamond_2020`)
- **Incident:** VLCC *MT New Diamond* engine room boiler explosion and bunker release 38 nautical miles off eastern Sri Lanka.
- **Forensic Pipeline Execution:**
  - Extracted 14.85 $\text{km}^2$ mineral oil slick from Sentinel-1A radar pass on Sept 3, 2020, 12:45 UTC.
  - Backward advection matched the Northeast monsoon current drift vector.
  - Evaluated 4 transiting candidate vessels; identified *MT New Diamond* at **Rank #1 with $>94\%$ confidence score**, matching official Sri Lanka Navy & Indian Coast Guard casualty records.

---

## Slide 5: Key Innovations & Competitive Differentiators

| Feature | Legacy / Existing Approaches | Our Attribution Intelligence Platform |
| :--- | :--- | :--- |
| **Operational Philosophy** | Reactive alerts only (often too late) | **Forensic attribution & historical time-inversion** |
| **Drift Modeling** | Forward forecasting only (where will it go?) | **Backward Lagrangian inversion (who discharged it?)** |
| **False-Positive Handling** | High false-alarm rate from low-wind calms | **Physics-based lookalike discrimination engine** |
| **AIS Gap Handling** | Lost tracking when vessels turn off AIS | **Cubic-spline dead-reckoning & gap anomaly detection** |
| **Legal Admissibility** | Black-box deep learning scores | **Explainable multi-factor scoring & SHA-256 evidence chain** |
| **Surveillance Automation**| Manual manual queries on GIS software | **Autonomous background satellite surveillance sweeps** |

### Ethical & Legal Rigor (Strict Compliance with Maritime Law)
- Compliant with UNCLOS Article 217 & MARPOL 73/78 Annex I evidence guidelines.
- Non-accusatory probabilistic decision support: Produces verifiable evidentiary rankings, not arbitrary black-box accusations.

---

## Slide 6: Feasibility, Impact & Future Roadmap

### Feasibility & Ready-to-Deploy State
- **100% Open-Source & Standard-Compliant:** Uses Copernicus Open Access APIs, global public hydrodynamics, and standard NMEA/AIS formats.
- **Zero Costly Proprietary Hardware:** Operates entirely in cloud/on-premise Linux environments with standard microservices.
- **Validated & Deterministic:** 200+ unit, integration, and regression tests ensuring 100% mathematical reproducibility.

### National & Environmental Impact
- **Enforcement Deterrence:** Drastically increases the probability of detecting midnight bilge dumping along Indian coastal shipping corridors (Malacca approach, Dondra Head, Mumbai High).
- **Cost Recovery & Polluter-Pays Principle:** Enables state maritime boards to recover crores of rupees in cleanup costs and ecological remediation fines from verified offending vessels.
- **Protection of Marine Biodiversity:** Protects fragile marine ecosystems (Gulf of Mannar, Sundarbans, Lakshadweep reefs).

### Next Phase Roadmap
- **Phase 1 (Achieved):** Automated SAR slick segmentation, backward drift inversion, AIS interception, PDF dossier generation.
- **Phase 2 (Next 6 Months):** Expansion to high-resolution optical imagery (Sentinel-2, PlanetScope) for daylight corroboration.
- **Phase 3 (Next 12 Months):** Integration with India's National Command Control Communication and Intelligence (NC3I) and coastal radar network (IMAC).
