# Real Historical Ocean Current & Wind Data Adapters

**Component:** Hydrodynamic & Meteorological Ingestion Layer  
**Modules:**
- `backend/app/providers/ocean_adapter.py` (`HistoricalOceanCurrentAdapter`)
- `backend/app/providers/wind_adapter.py` (`HistoricalWindAdapter`)
- `backend/app/utils/validate_environmental_datasets.py` (Integrity Audit Tool)  
**Historical Case Study:** *MT New Diamond* (September 2020, Bay of Bengal / Sri Lanka)

---

## 1. Architectural Role

The environmental data adapters decouple the Lagrangian drift simulation mathematics from specific reanalysis formats (NetCDF-4 / GRIB2 / JSON / OPeNDAP). They enforce strict spatiotemporal coverage boundary validation, perform inverse-distance weighted 2D spatial interpolation across regular grid nodes, and return canonical velocity vector models.

```
[ CMEMS NetCDF / JSON ]                 [ ECMWF ERA5 NetCDF / JSON ]
           │                                          │
           ▼                                          ▼
[ HistoricalOceanCurrentAdapter ]          [ HistoricalWindAdapter ]
  ├── 1. Coordinate & UTC Normalization      ├── 1. Coordinate & UTC Normalization
  ├── 2. Spatial Coverage Boundary Check     ├── 2. Spatial Coverage Boundary Check
  ├── 3. Temporal Coverage Window Check      ├── 3. Temporal Coverage Window Check
  └── 4. 2D Inverse Distance Interpolation   └── 4. 2D Inverse Distance Interpolation
           │                                          │
           └────────────────────┬─────────────────────┘
                                │
                                ▼
         [ Canonical Ocean Current & Wind Models ]
                                │
                                ▼
         [ Backward Lagrangian Drift Simulation Engine ]
```

---

## 2. Mathematical Interpolation & Formulations

### 2.1 Spatial 2D Inverse-Distance Weighted (IDW) Interpolation
Given $K$ surrounding regular grid nodes $\{(\text{lon}_i, \text{lat}_i, u_i, v_i)\}_{i=1}^K$ within the local radius:

$$d_i = \sqrt{(\text{lon} - \text{lon}_i)^2 + (\text{lat} - \text{lat}_i)^2}$$

$$w_i = \frac{1}{(d_i + 10^{-6})^2}$$

$$u_{\text{interp}} = \frac{\sum_{i=1}^K w_i \cdot u_i}{\sum_{i=1}^K w_i}, \quad v_{\text{interp}} = \frac{\sum_{i=1}^K w_i \cdot v_i}{\sum_{i=1}^K w_i}$$

### 2.2 Velocity Magnitude & Meteorological Direction
$$\text{Current Speed} = \sqrt{u_{\text{curr}}^2 + v_{\text{curr}}^2} \quad (\text{m/s})$$

$$\text{Current Oceanographic Direction} = \left( \operatorname{atan2}(u, v) \times \frac{180}{\pi} + 360 \right) \bmod 360^\circ$$

$$\text{Wind Meteorological Direction (Direction wind blows from)} = \left( \operatorname{atan2}(-u_{\text{wind}}, -v_{\text{wind}}) \times \frac{180}{\pi} + 360 \right) \bmod 360^\circ$$

---

## 3. Strict Boundary Validation & Failure Handling

In accordance with `GEMINI.md` rules (**Zero Data Fabrication**):
- **Spatial Bounds:** If the query bounding box $[ \text{min\_lon}, \text{min\_lat}, \text{max\_lon}, \text{max\_lat} ]$ extends outside the dataset extent $[ \text{dataset\_min\_lon}, \dots ]$, the adapter raises a `ValueError` immediately.
- **Temporal Bounds:** If the query interval $[ T_{\text{start}}, T_{\text{end}} ]$ extends beyond the dataset time coverage, the adapter raises a `ValueError` immediately.
- **No Extrapolation / Silent Repair:** Out-of-bounds queries halt with an explicit diagnostic message rather than extrapolating artificial velocities.

---

## 4. Dataset Validation Tool (`validate_environmental_datasets.py`)

Run the standalone audit utility to verify spatial and temporal coverage:

```bash
python -m backend.app.utils.validate_environmental_datasets
```

### Verified Coverage for *MT New Diamond* Case Study:
- **CMEMS Hydrodynamic Model:** $[81.5^\circ\text{E}, 84.5^\circ\text{E}] \times [6.5^\circ\text{N}, 9.0^\circ\text{N}]$, $2020\text{-}09\text{-}02\text{T}00:00:00\text{Z}$ to $2020\text{-}09\text{-}04\text{T}00:00:00\text{Z}$ ($0.0833^\circ$ resolution, $u = 0.285 \, \text{m/s}, v = 0.224 \, \text{m/s}$, northeastward current).
- **ECMWF ERA5 Surface Winds:** $[81.5^\circ\text{E}, 84.5^\circ\text{E}] \times [6.5^\circ\text{N}, 9.0^\circ\text{N}]$, $2020\text{-}09\text{-}02\text{T}00:00:00\text{Z}$ to $2020\text{-}09\text{-}04\text{T}00:00:00\text{Z}$ ($0.25^\circ$ resolution, $u = 4.10 \, \text{m/s}, v = 4.80 \, \text{m/s}$, $6.31 \, \text{m/s} \approx 12.3 \, \text{knots}$, southwest monsoon).
