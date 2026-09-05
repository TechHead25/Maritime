# API Contract & Schema Specification

## Project: Maritime Oil-Spill Attribution Intelligence (SIH26143)
**Base URL:** `/api/v1`  
**Protocol:** REST (JSON & GeoJSON)

---

## 1. Summary of Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Cases** | `POST` | `/cases` | Create a new investigation case |
| **Cases** | `GET` | `/cases` | List all investigation cases |
| **Cases** | `GET` | `/cases/{case_id}` | Get full case details with current state |
| **Pipeline** | `POST` | `/cases/{case_id}/run-full-investigation` | Run end-to-end automated pipeline |
| **SAR** | `POST` | `/cases/{case_id}/detect-slick` | Detect slick from SAR scene |
| **Drift** | `POST` | `/cases/{case_id}/simulate-drift` | Run backward Lagrangian drift simulation |
| **AIS** | `POST` | `/cases/{case_id}/intercept-vessels` | Intercept and filter historical AIS candidates |
| **Attribution** | `POST` | `/cases/{case_id}/score-attribution` | Compute multi-factor explainable attribution |
| **Dossier** | `GET` | `/cases/{case_id}/dossier` | Retrieve structured JSON forensic dossier |
| **Dossier** | `GET` | `/cases/{case_id}/dossier/export.pdf` | Download printable PDF forensic investigation report |
| **Scenarios** | `GET` | `/scenarios` | List preloaded synthetic benchmark scenarios |
| **Scenarios** | `POST` | `/scenarios/load/{scenario_id}` | Initialize a case from a preloaded synthetic scenario |

---

## 2. Request and Response Schemas

### 2.1 Create Case
- **Endpoint:** `POST /api/v1/cases`
- **Request Body:**
```json
{
  "title": "Malacca Strait Slick Investigation",
  "region_of_interest": {
    "type": "Polygon",
    "coordinates": [
      [[101.0, 2.0], [103.0, 2.0], [103.0, 4.0], [101.0, 4.0], [101.0, 2.0]]
    ]
  },
  "metadata": {
    "lead_analyst": "Officer Sharma",
    "incident_ref": "SAR-IND-2026-004"
  }
}
```
- **Response (201 Created):**
```json
{
  "id": "c1f94a2b-7e61-412f-9271-8bc68df21034",
  "title": "Malacca Strait Slick Investigation",
  "status": "CREATED",
  "region_of_interest": { "type": "Polygon", "coordinates": [...] },
  "created_at": "2026-09-02T10:00:00Z",
  "updated_at": "2026-09-02T10:00:00Z",
  "metadata": { "lead_analyst": "Officer Sharma", "incident_ref": "SAR-IND-2026-004" }
}
```

---

### 2.2 Detect Slick (SAR Module)
- **Endpoint:** `POST /api/v1/cases/{case_id}/detect-slick`
- **Request Body:**
```json
{
  "sar_scene_id": "optional-existing-scene-id",
  "satellite_platform": "Sentinel-1A",
  "acquisition_timestamp": "2026-09-01T14:30:00Z",
  "use_mock_scene": true,
  "mock_scene_name": "malacca_tanker_discharge"
}
```
- **Response (200 OK):**
```json
{
  "slick_detection": {
    "id": "s82b1-419b-4dfa",
    "sar_scene_id": "sar-902-11a",
    "slick_polygon": {
      "type": "Polygon",
      "coordinates": [[[102.12, 2.85], [102.16, 2.87], [102.15, 2.89], [102.11, 2.86], [102.12, 2.85]]]
    },
    "centroid": { "type": "Point", "coordinates": [102.135, 2.867] },
    "area_sq_km": 14.85,
    "perimeter_km": 18.2,
    "major_axis_orientation_deg": 48.5,
    "confidence_score": 0.94,
    "lookalike_probability": 0.06
  }
}
```

---

### 2.3 Simulate Backward Drift
- **Endpoint:** `POST /api/v1/cases/{case_id}/simulate-drift`
- **Request Body:**
```json
{
  "max_hours_backward": 48,
  "time_step_minutes": 30,
  "particle_count": 2000,
  "wind_leeway_factor": 0.03,
  "current_advection_factor": 1.0,
  "use_synthetic_weather": true
}
```
- **Response (200 OK):**
```json
{
  "drift_simulation_id": "drift-8812-4aa1",
  "release_window": {
    "estimated_start_time": "2026-08-31T18:00:00Z",
    "estimated_end_time": "2026-09-01T06:00:00Z",
    "peak_probability_time": "2026-09-01T00:30:00Z",
    "confidence_interval": 0.92
  },
  "probability_clouds": [
    {
      "timestamp": "2026-09-01T00:30:00Z",
      "hours_before_sar": 14.0,
      "envelope_polygon": { "type": "Polygon", "coordinates": [...] },
      "center_point": { "type": "Point", "coordinates": [101.82, 2.61] },
      "dispersion_radius_km": 3.4
    }
  ]
}
```

---

### 2.4 Intercept AIS Candidates
- **Endpoint:** `POST /api/v1/cases/{case_id}/intercept-vessels`
- **Request Body:**
```json
{
  "buffer_radius_km": 10.0,
  "include_dark_gaps": true
}
```
- **Response (200 OK):**
```json
{
  "candidate_count": 3,
  "candidates": [
    {
      "candidate_id": "cand-001",
      "mmsi": "538009912",
      "vessel_name": "PACIFIC GLORY",
      "vessel_type": "TANKER",
      "flag_country": "Liberia",
      "closest_point_of_approach_km": 0.45,
      "time_of_closest_approach": "2026-09-01T00:45:00Z",
      "is_in_release_envelope": true,
      "has_ais_gaps": true,
      "gap_intervals": [["2026-08-31T23:30:00Z", "2026-09-01T02:00:00Z"]]
    }
  ]
}
```

---

### 2.5 Compute Explainable Attribution
- **Endpoint:** `POST /api/v1/cases/{case_id}/score-attribution`
- **Request Body:**
```json
{
  "weights": {
    "proximity": 0.35,
    "alignment": 0.25,
    "vessel_type": 0.15,
    "anomaly": 0.15,
    "ais_integrity": 0.10
  }
}
```
- **Response (200 OK):**
```json
{
  "ranked_candidates": [
    {
      "rank": 1,
      "candidate_id": "cand-001",
      "vessel_name": "PACIFIC GLORY",
      "mmsi": "538009912",
      "vessel_type": "TANKER",
      "total_score": 88.5,
      "risk_level": "VERY_HIGH",
      "sub_scores": {
        "proximity_score": 33.2,
        "trajectory_alignment_score": 23.5,
        "vessel_type_risk_score": 15.0,
        "navigational_anomaly_score": 7.0,
        "ais_integrity_penalty": 9.8
      },
      "evidence_items": [
        {
          "factor_category": "PROXIMITY",
          "title": "Within 450m of Drift Origin Center",
          "description": "Vessel trajectory placed it 450 meters from peak release probability cloud at 00:45 UTC.",
          "score_impact": 33.2
        },
        {
          "factor_category": "AIS_INTEGRITY",
          "title": "2.5-hour AIS Transponder Gap",
          "description": "AIS signal ceased 45 minutes prior to entering the spill origin envelope and resumed 2.5 hours later.",
          "score_impact": 9.8
        }
      ]
    }
  ]
}
```
