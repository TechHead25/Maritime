# SAR Lookalike Discrimination & Baseline Classifier

**Component:** SAR Detection & Feature Extraction Subsystem  
**Module:** `backend/app/services/sar_detector.py`  
**Classification Scope:** Explainable Heuristic Baseline (SIH26143 Decision Support)

---

## 1. Overview & Scientific Context

Synthetic Aperture Radar (SAR) sensors detect ocean oil slicks as **dark formations** because oil films dampen high-frequency surface capillary-gravity waves, causing specular reflection away from the radar antenna.

However, non-mineral physical and biological phenomena produce lookalike dark patches with similar low backscatter signatures:
- **Low-Wind Calm Basins:** Meteorological calm areas ($< 3 \, \text{m/s}$) with insufficient wind friction to generate capillary waves.
- **Biogenic Surfactants:** Natural monomolecular organic films produced by plankton or fish schools.
- **Coastal Land Shadows & Shallow Reefs:** Radar shielding near high coastal topography or bottom topography dampening.
- **Oceanic Upwelling & Internal Waves:** Cold-water upwelling altering surface roughness.
- **Rain Cell Downdrafts:** Atmospheric attenuation and sea surface smoothing.

The objective of this subsystem is to extract dark formations, compute multi-dimensional explainable features, distinguish verified mineral oil slicks from lookalikes, and log explicit **rejection reasons** for forensic auditability.

---

## 2. Multi-Dimensional Explainable Feature Vector

For each segmented candidate patch, the system extracts a strongly-typed `SARFeatureVector`:

| Feature Name | Symbol / Equation | Physical & Radar Rationale | Typical Mineral Slick | Lookalike Behavior |
|---|---|---|---|---|
| **Surface Area** | $A \, (\text{km}^2)$ | Total planar extent in $\text{km}^2$ | $1.0 - 60.0 \, \text{km}^2$ | Low-wind basins often $> 150 \, \text{km}^2$ |
| **Damping Contrast** | $\Delta\text{dB} = \mu_{\text{sea}} - \mu_{\text{patch}}$ | Radar backscatter attenuation vs ambient sea | $\ge 4.0 \, \text{dB}$ (strong damping) | Biogenic films often $< 2.5 \, \text{dB}$ (weak damping) |
| **Elongation Ratio** | $\sqrt{\lambda_1 / \lambda_2}$ | Ratio of major to minor principal spatial moments | $\ge 1.8$ (stream-like / drift dispersion) | Biogenic patches often isotropic / circular ($< 1.3$) |
| **Compactness** | $\frac{P^2}{4\pi A}$ | Isoperimetric quotient ($1.0 = \text{circle}$) | High ($> 1.5$) due to ocean currents/wind | Circular or diffuse |
| **Edge Gradient Sharpness** | $\left\|\nabla \sigma_0\right\| \, (\text{dB/px})$ | Mean Sobel gradient magnitude along boundary | Sharp ($\ge 0.8 \, \text{dB/px}$) | Upwelling / internal waves are diffuse ($< 0.5$) |
| **Texture Variation** | $\text{CoV} = \sigma / |\mu|$ | Internal homogeneity / coefficient of variation | Low to moderate (uniform damping) | Noisy / variable |
| **Distance to Land** | $d_{\text{land}} \, (\text{km})$ | Distance transform to high-backscatter coastline | $> 2.0 \, \text{km}$ | Coastal shadows $< 1.0 \, \text{km}$ |
| **Ambient Wind Speed** | $W_{\text{ambient}} \, (\text{m/s})$ | Ambient sea surface wind speed | $3.0 - 12.0 \, \text{m/s}$ | Extreme calm $< 2.5 \, \text{m/s}$ |

---

## 3. Classifier Architecture & ML Extensibility

The subsystem defines an abstract classifier contract (`BaseSARClassifier`):

```python
class BaseSARClassifier(ABC):
    @abstractmethod
    def classify(
        self,
        features: SARFeatureVector,
    ) -> Tuple[SARLookalikeClass, bool, float, float, Optional[str]]:
        """Returns: (classification, is_accepted, confidence_score, lookalike_probability, rejection_reason)"""
        pass
```

### Current Implementation: `ExplainableRuleSARClassifier`
Uses transparent threshold boundaries on damping contrast, area, and elongation with itemized rejection audit strings.

### Future ML / Deep-Learning Interchangeability
A future machine learning model (e.g., Random Forest, XGBoost, or a U-Net / ResNet feature head trained on the NOAA or EMSA CleanSeaNet datasets) can inherit from `BaseSARClassifier` and plug into `DeterministicSARDetector` with zero changes to downstream drift or attribution engines.

---

## 4. Rejected Candidate Audit Collection

Every rejected dark patch is preserved in `SARCandidatePatch` with its complete feature vector and a human-readable rejection explanation.

**Example Rejection Explanations:**
- *"Rejected as low-wind lookalike: Surface area (182.4 km²) exceeds maximum expected oil slick size (150.0 km²); characteristic of meteorological calm sea basin."*
- *"Rejected as biogenic lookalike: Radar damping contrast (2.10 dB) is below the mineral oil threshold (3.5 dB); consistent with natural monomolecular films."*
- *"Rejected as coastal shadow: Located within 0.85 km of landmass / coastal surf."*

---

## 5. Scientific Limitations & Boundaries (Non-Production Notice)

In accordance with permanent rules (`GEMINI.md`):

> [!WARNING]
> **Scientific Limitations Notice:**  
> 1. **Baseline Status:** The baseline rule-based classifier is a **deterministic heuristic model designed for algorithmic transparency and decision support**, not a production-grade deep-learning classifier.  
> 2. **Wind Speed Dependency:** Discriminating mineral oil from biogenic films in low-wind regimes ($< 3.0 \, \text{m/s}$) remains an active research challenge in satellite oceanography.  
> 3. **Validation Boundary:** Threshold boundaries ($\Delta\text{dB} \ge 3.5$, $A \le 150 \, \text{km}^2$) are baseline heuristics and must be statistically calibrated against ground-truth SAR collections before operational deployment.
