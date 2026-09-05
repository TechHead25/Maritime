# Algorithmic Methodology

## Project: Maritime Oil-Spill Attribution Intelligence (SIH26143)

---

## 1. Overview of Forensic Algorithm Pipeline

The oil spill attribution pipeline reconstructs the historical chain of events using physics-based Lagrangian advection and multi-factor spatiotemporal scoring.

```
[ SAR Imagery ]
      │
      ▼
1. Slick Detection & Morphological Extraction
      │
      ▼
2. Backward Lagrangian Drift Simulation (Advection + Perturbation)
      │
      ▼
3. Origin Estimation & Release Window Calculation
      │
      ▼
4. AIS Spatiotemporal Interception & Trajectory Interpolation
      │
      ▼
5. Multi-Factor Attribution Scoring Matrix
      │
      ▼
6. Verifiable Evidence Chain Assembly
```

---

## 2. Backward Particle Drift Engine: Beginner-Friendly Guide

### 2.1 The Concept: "Rewinding the Ocean"
When a ship discharges oil into the ocean, two natural forces push the slick across the surface:
1. **Ocean Surface Currents:** The water moves the oil directly at 100% of the current's speed.
2. **Surface Wind:** The wind blows across the surface of the water, pushing the oil slick at roughly **3% of the wind speed** (known in oceanography as the *wind leeway factor* $\alpha = 0.03$).

If we observe a slick at satellite capture time $T_{\text{obs}}$, we calculate its backward path by **reversing the direction of the forces**:

$$\vec{v}_{\text{backward}} = - \left( 1.0 \times \vec{u}_{\text{current}} + 0.03 \times \vec{u}_{\text{wind}} \right) + \text{turbulent noise}$$

### 2.2 How the Simulation Works Step-by-Step

```
At T_obs (e.g. 14:30 UTC):
   [ Seed 1,000 particles randomly inside the observed slick polygon ]
                  │
                  ▼  Step Backward by Δt (e.g., 30 minutes)
   [ Move every particle: x_new = x_old - (v_current + 0.03 * v_wind) * Δt + noise ]
                  │
                  ▼  Repeat for each step (e.g., 48 hours backward)
   [ Calculate mean center, standard deviation spread, and 95% bounding box ]
                  │
                  ▼  At Estimated Release Time (e.g. 00:30 UTC)
   [ Output: Probability Cloud (Origin Center + Uncertainty Radius) ]
```

### 2.3 Converting Physical Speeds to Latitude and Longitude
The ocean currents and winds are measured in meters per second ($\text{m/s}$). Over a 30-minute timestep ($\Delta t = 1,800 \, \text{seconds}$), the displacement in meters is:
$$\Delta x_{\text{meters}} = - u_{\text{advect}} \times \Delta t + \text{noise}_x$$
$$\Delta y_{\text{meters}} = - v_{\text{advect}} \times \Delta t + \text{noise}_y$$

To convert meters into latitude and longitude decimal degrees on Earth:
- **Latitude:** $1^\circ \approx 110,574 \, \text{meters}$
  $$\Delta \text{lat} = \frac{\Delta y_{\text{meters}}}{110,574}$$
- **Longitude:** $1^\circ \approx 111,320 \times \cos(\text{latitude}) \, \text{meters}$
  $$\Delta \text{lon} = \frac{\Delta x_{\text{meters}}}{111,320 \times \cos(\text{latitude}_{\text{radians}})}$$

### 2.4 Why Stochastic Noise (Random Diffusion) is Included
The real ocean is not a smooth conveyor belt; it contains small whirlpools, waves, and turbulence. 
To account for this uncertainty, we add a random perturbation (Gaussian noise) to every particle at each step:
$$\sigma_{\text{diffusion}} = \sqrt{2 \cdot K_h \cdot \Delta t}$$
where $K_h \approx 2.5 \, \text{m}^2/\text{s}$ is the horizontal eddy diffusivity. This causes the particle swarm to spread naturally as we go further back in time, creating an **Uncertainty Radius (Dispersion Radius)**.

### 2.5 Reconstructing the Probability Cloud & Release Window
- **Release Window $[T_{\text{start}}, T_{\text{end}}]$:** The estimated time window when the discharge occurred (e.g., 14 hours prior to SAR overpass $\pm 2$ hours).
- **Probability Cloud:** The convex envelope or bounding box containing the particles at that specific time slice.
- **Origin Centroid:** The average coordinate of all particles at the peak probability time $T_{\text{peak}}$.

---

## 3. AIS Trajectory Interpolation & Anomaly Detection

Between discrete AIS pings $(p_1, p_2)$ with timestamps $(t_1, t_2)$:
- Piecewise linear/geodesic interpolation computes estimated position $\vec{x}_{\text{vessel}}(t)$ at any intermediate $t \in [t_1, t_2]$.
- **Dark Gap Identification:** Any interval where $(t_2 - t_1) > 60$ minutes inside the Area of Interest is recorded as a transponder outage anomaly.

---

## 4. Multi-Factor Explainable Attribution Scoring Engine

The platform evaluates every candidate vessel $V_j$ using a 5-factor transparent scoring matrix normalized from **0 to 100 points**:

$$S_{\text{total}} = S_{\text{prox}} + S_{\text{timing}} + S_{\text{behavior}} + S_{\text{ais}} + S_{\text{vessel}}$$

### 4.1 Scoring Breakdown & Weights

| Factor | Weight | Max Points | Formulation & Mathematical Description |
|---|---|---|---|
| **1. Spatial Proximity ($S_{\text{prox}}$)** | **40%** | **40.0** | $$40.0 \times \exp\left( - \frac{d_{\text{cpa}}^2}{2 \cdot \sigma_{\text{cloud}}^2} \right)$$<br>Calculated from the Closest Point of Approach ($d_{\text{cpa}}$ in $\text{km}$) relative to the peak origin cloud dispersion spread. |
| **2. Timing Alignment ($S_{\text{timing}}$)** | **25%** | **25.0** | Inside release window $[T_{\text{start}}, T_{\text{end}}]$:<br>$$25.0 \times \left(1.0 - \frac{\|\Delta t\|}{W_{\text{half}}} \times 0.25\right)$$<br>Outside window decays exponentially with time difference. |
| **3. Navigational Behaviour ($S_{\text{behavior}}$)** | **15%** | **15.0** | **Heading Alignment ($10.0$ pts):** $10.0 \times \max(0, \cos(\Delta \theta_{\text{slick}}))$<br>**Speed Reduction ($5.0$ pts):** Deceleration $\ge 3.5$ knots down to $< 9.0$ knots in open sea. |
| **4. AIS Continuity ($S_{\text{ais}}$)** | **10%** | **10.0** | $+10.0$ pts if an intentional transponder gap ($\ge 60$ mins) occurred during transit near/inside the release zone ($0.0$ if continuous transmission). |
| **5. Vessel Relevance ($S_{\text{vessel}}$)** | **10%** | **10.0** | `TANKER` = $10.0$ pts, `BUNKER` = $8.5$ pts, `CARGO` = $6.0$ pts, `FISHING` = $3.0$ pts, `PASSENGER` / `OTHER` = $1.0$ pt. |

### 4.2 Risk Level Classification

- **Total $\ge 75.0$ pts:** `VERY_HIGH` Risk
- **Total $50.0 - 74.9$ pts:** `HIGH` Risk
- **Total $30.0 - 49.9$ pts:** `MEDIUM` Risk
- **Total $15.0 - 29.9$ pts:** `LOW` Risk
- **Total $< 15.0$ pts:** `NEGLIGIBLE` Risk

---

## 5. Scientific Integrity & Attribution Phrasing

- All scores represent mathematical forensic evidence metrics rather than legal certainties.
- The platform never declares a vessel "guilty" or "the definitive polluter".
- **Required Standard Phrasing:**
  > *"This vessel is the highest-ranked candidate based on the available spatial, temporal, and navigational evidence."*
