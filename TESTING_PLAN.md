# Testing Plan & Benchmark Scenarios

## Project: Maritime Oil-Spill Attribution Intelligence (SIH26143)

---

## 1. Testing Strategy

To guarantee forensic reliability, the testing suite is divided into three tiers:
1. **Unit Tests:** Verify individual mathematical and physical functions (reverse Euler advection, haversine/geodesic distance calculations, cosine alignment, scoring formulas).
2. **Integration Tests:** Verify pipeline sequences (e.g., Slick Detection $\rightarrow$ Drift Simulation $\rightarrow$ AIS Interceptor $\rightarrow$ Attribution Scoring).
3. **End-to-End Golden Scenarios:** Deterministic benchmark test cases with known "ground truth" culprits to evaluate attribution accuracy and ranking integrity.

---

## 2. Deterministic Benchmark Test Scenarios

### Scenario 1: "The Rogue Tanker" (Golden True-Positive Benchmark)
- **Context:** A crude oil tanker (*MT Ocean Marauder*, MMSI 538112233) conducts illegal tank washing at night in the Malacca Strait.
- **Physical Setup:**
  - Spill release at $T = 0$ (2026-08-31 22:00 UTC).
  - SAR observation at $T = +14\text{h}$ (2026-09-01 12:00 UTC).
  - Constant eastward current (0.5 knots) and NE wind (10 knots).
  - Vessel turns off AIS 30 minutes before discharge and turns it back on 3 hours later.
  - 3 background passing vessels (1 innocent container ship at $15\text{km}$ distance, 1 bulk carrier passing 10 hours later, 1 small tugboat).
- **Expected Test Outcome:**
  - Reverse drift reconstructs release origin within $1.5\text{km}$ of actual discharge GPS.
  - *MT Ocean Marauder* is ranked #1 with Attribution Score $\ge 85.0 / 100$.
  - All innocent vessels score $\le 30.0 / 100$.
  - AIS gap penalty is correctly triggered and cited in evidence items.

### Scenario 2: "Crossed Paths" (Disambiguation Benchmark)
- **Context:** Two vessels pass through the general area: Vessel A (Oil Tanker) moving at 14 knots on heading $045^\circ$, and Vessel B (Passenger Ferry) crossing perpendicular at heading $135^\circ$.
- **Physical Setup:**
  - Elongated slick shape has major axis aligned with $045^\circ$.
  - Vessel A was present at peak release time $T_{\text{peak}}$.
  - Vessel B passed 4 hours outside the primary release window.
- **Expected Test Outcome:**
  - Vessel A receives high trajectory alignment score ($> 20/25$) and high proximity score.
  - Vessel B is heavily penalized by temporal mismatch and low vessel risk.
  - Rank 1: Vessel A ($> 80/100$), Rank 2: Vessel B ($< 35/100$).

### Scenario 3: "Zero Intercept / Blind Zone" (Negative Control)
- **Context:** An oil slick is detected, but no AIS broadcast exists in the release window (e.g., pure uncooperative dark vessel or natural seepage).
- **Expected Test Outcome:**
  - Drift engine successfully computes probability cloud.
  - AIS Interceptor returns `0` candidate vessels without crashing or raising unhandled exceptions.
  - System flags a warning: *"No cooperative AIS tracks detected in release envelope; suspected unlisted vessel or natural seepage"*.

### Scenario 4: "Lookalike Rejection" (False Positive Control)
- **Context:** Input SAR scene contains a low-wind dark area / biogenic surfactant patch.
- **Expected Test Outcome:**
  - SAR detection module flags low confidence ($< 0.40$) and high lookalike probability ($> 0.70$).
  - Pipeline logs warning and halts before running unnecessary drift computations.

---

## 3. Automated Test Suite Matrix

| Test Suite | File Path | Scope | Automated Tool |
|---|---|---|---|
| **Data Schema Validation** | `tests/unit/test_schemas.py` | Pydantic model serialization, GeoJSON geometry checks | `pytest` |
| **Physics & Drift Math** | `tests/unit/test_drift_math.py` | Advection vectors, wind leeway fraction, RK4 vs Euler | `pytest` |
| **AIS Interpolator** | `tests/unit/test_ais_interp.py` | Spline interpolation, gap detection, distance calculations | `pytest` |
| **Attribution Math** | `tests/unit/test_attribution.py` | Scoring weights, boundary values ($0-100$), explainability | `pytest` |
| **SAR Feature Extractor** | `tests/unit/test_sar_extractor.py`| Contours, polygon area calculation, orientation angle | `pytest` |
| **Pipeline Integration** | `tests/integration/test_pipeline.py` | Full sequence execution on synthetic cases | `pytest` |
| **API Endpoints** | `tests/integration/test_api.py` | FastAPI HTTP request/response validation | `pytest` + `httpx` |
| **Dossier Exporter** | `tests/integration/test_dossier.py`| JSON schema audit and PDF byte generation | `pytest` |

---

## 4. How to Run the Tests

```bash
# Run all unit and integration tests
pytest -v

# Run with test coverage report
pytest --cov=app --cov-report=term-missing

# Run specific golden benchmark scenarios
pytest tests/integration/test_golden_scenarios.py -k "test_rogue_tanker"
```
