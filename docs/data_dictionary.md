# Data Dictionary & Schema Glossary

## Project: Maritime Oil-Spill Attribution Intelligence (SIH26143)

---

## 1. Domain Entities

| Entity | Description | Primary Key | Key Attributes |
|---|---|---|---|
| `InvestigationCase` | The top-level incident case aggregate | `id` (UUID) | `title`, `status`, `region_of_interest`, `created_at` |
| `SARScene` | Satellite radar image metadata & raster reference | `id` (UUID) | `case_id`, `platform`, `acquisition_timestamp`, `footprint` |
| `SlickDetection` | Segmented dark formation polygon and features | `id` (UUID) | `sar_scene_id`, `slick_polygon`, `area_sq_km`, `orientation` |
| `DriftSimulation` | Backward advection simulation run metadata | `id` (UUID) | `slick_detection_id`, `particle_count`, `time_step_minutes` |
| `ProbabilityCloud` | Time-sliced particle dispersion envelope | `id` (UUID) | `drift_simulation_id`, `timestamp`, `envelope_polygon` |
| `ReleaseWindow` | Estimated discharge time interval | `id` (UUID) | `drift_simulation_id`, `start_time`, `end_time`, `confidence` |
| `VesselTrack` | Historical GPS navigation trajectory | `id` (UUID) | `mmsi`, `vessel_name`, `vessel_type`, `waypoints` |
| `CandidateVessel` | Ship intersecting the spill release zone | `id` (UUID) | `case_id`, `vessel_track_id`, `cpa_km`, `time_of_cpa` |
| `AttributionScore` | Composite liability and ranking metric | `id` (UUID) | `candidate_vessel_id`, `total_score`, `sub_scores`, `risk` |
| `EvidenceItem` | Fact-based audit log item supporting score | `id` (UUID) | `attribution_score_id`, `factor_category`, `description` |

---

## 2. Standard Units & Conventions

| Measurement | Unit | Format / Standard |
|---|---|---|
| **Coordinates** | Decimal Degrees | WGS84 (`EPSG:4326`), `[longitude, latitude]` order in GeoJSON |
| **Timestamps** | UTC | ISO 8601 string (`YYYY-MM-DDTHH:MM:SSZ`) |
| **Distance** | Kilometers / Meters | $\text{km}$ for vessel distances, $\text{m}$ for particle dispersion |
| **Area** | Square Kilometers | $\text{km}^2$ for slick surface area |
| **Velocity (Current & Wind)** | Meters per second ($\text{m/s}$) | Eastward ($u$), Northward ($v$) vectors |
| **Vessel Speed** | Knots (nautical miles per hour) | SOG (Speed Over Ground) |
| **Angles / Headings** | Degrees ($0^\circ - 360^\circ$) | Clockwise from True North |
| **Attribution Score** | Scale $0.0 - 100.0$ | Continuous composite rating |

---

## 3. Synthetic Benchmark Fixtures & Scenarios (SYNTHETIC DATA)

> [!IMPORTANT]
> **SYNTHETIC DATA LABEL:** All files located in `data/cases/demo_case_001/` are deterministically generated synthetic benchmark fixtures created solely for software testing, algorithm validation, and integration tests. No real-world vessel identities, commercial violations, or actual satellite passes are represented.

### 3.1 Benchmark Incident: `demo_case_001` (Malacca Strait Incident)
- **Geographic Area:** Malacca Strait $[101.0^\circ\text{E} - 103.0^\circ\text{E}, \, 2.0^\circ\text{N} - 3.5^\circ\text{N}]$
- **SAR Satellite Overpass ($T_{\text{obs}}$):** `2026-09-01T14:30:00Z`
- **Observed Slick Centroid:** $[102.140^\circ\text{E}, \, 2.877^\circ\text{N}]$
- **Slick Surface Area:** $14.85 \, \text{km}^2$
- **Hydrodynamic Ocean Current:** $u = 0.789 \, \text{m/s}$ (Eastward), $v = 0.691 \, \text{m/s}$ (Northward), Speed: $\sim 2.0$ knots
- **Surface Wind:** $w_u = -3.5 \, \text{m/s}$ (Westward), $w_v = -3.5 \, \text{m/s}$ (Southward), Speed: $4.95 \, \text{m/s}$ ($\sim 9.6$ knots)
- **Reconstructed Drift Origin (at $T_{\text{obs}} - 14\text{h}$):** $[101.830^\circ\text{E}, \, 2.610^\circ\text{N}]$
- **Estimated Release Window:** `2026-08-31T22:00:00Z` to `2026-09-01T02:30:00Z` (Peak: `2026-09-01T00:30:00Z`)

### 3.2 Benchmark Vessel Profiles & Expected Scoring Behaviors

| Vessel | Identifier | Type | Scenario Role & Behavior | Expected Attribution Tier |
|---|---|---|---|---|
| **Vessel A (`MT PACIFIC GLORY`)** | MMSI: `538009912`<br>IMO: `9312345` | `TANKER` | **Ground-Truth Culprit:** Passes within $450 \, \text{m}$ of the origin at `00:45 UTC` during the peak release window. Heading $048^\circ$ matches slick elongation axis. Exhibits transponder dark gap from `23:45` to `01:15 UTC`. | **Rank #1 (VERY HIGH RISK)**<br>Score $\ge 85 / 100$ |
| **Vessel B (`MV ATLANTIC TRANSIT`)** | MMSI: `352001140`<br>IMO: `9488123` | `CARGO` | **Wrong Time Control:** Crosses near the origin coordinates ($[101.84, 2.62]$) but at `11:30 UTC` (11 hours after the release window). | **Low Score ($< 35 / 100$)**<br>Penalized heavily by temporal distance |
| **Vessel C (`STAR VOYAGER`)** | MMSI: `211889900`<br>IMO: `9122340` | `PASSENGER` | **Far Distance Control:** Crosses at the exact peak release timestamp (`00:30 UTC`), but $32 \, \text{km}$ away in the eastern commercial shipping lane. | **Low Score ($< 30 / 100$)**<br>Penalized by spatial distance and vessel type |
| **Vessel D (`NEPTUNE TRADER`)** | MMSI: `636015522`<br>IMO: `9554411` | `CARGO` | **AIS Gap / Weak Spatial Alignment:** Has a 2-hour AIS transponder gap (`23:30 - 01:30 UTC`), but passes $18 \, \text{km}$ away on a perpendicular heading ($140^\circ$). | **Moderate / Low Score ($< 45 / 100$)**<br>Receives gap penalty, but lacks spatial proximity and alignment |
