# External Telemetry Data Sources & Adapter Specifications

**Project:** Maritime Oil-Spill Attribution Intelligence (SIH26143)  
**Document:** `docs/data_sources.md`  
**Architecture Pattern:** Provider Adapter Pattern (`SARDataProvider`, `AISDataProvider`, `OceanCurrentProvider`, `WindDataProvider`)

---

## 1. Architectural Principles

The forensic intelligence pipeline strictly decouples scientific calculations from external provider APIs. All external data connectors must implement the project's canonical abstract provider interfaces:

```
[ External Satellite / Sensor API ]
               │
               ▼
[ Provider Adapter Implementation ] (e.g. CopernicusCDSEProvider, SpireAISProvider)
               │
               ▼
   [ Canonical Domain Models ]     (SARScene, SARRaster, List[VesselTrack], OceanCurrentGrid, WindGrid)
               │
               ▼
[ Scientific Forensic Engines ]    (SAR Segmentation ➔ Lagrangian Drift ➔ AIS Attribution)
```

---

## 2. Target External Data Sources

### 2.1 Synthetic Aperture Radar (SAR) Imagery

| Attribute | Specification |
|---|---|
| **Primary Source** | European Space Agency (ESA) Copernicus Data Space Ecosystem (CDSE) / Open Access Hub |
| **Constellation / Sensor** | Sentinel-1A / Sentinel-1B C-band SAR ($\lambda = 5.546 \, \text{cm}$, $5.405 \, \text{GHz}$) |
| **Product Type** | Level-1 Ground Range Detected (GRD) in Interferometric Wide Swath (IW) mode |
| **Data Format** | SAFE format containing GeoTIFF 16-bit unsigned integer amplitude rasters and XML calibration metadata |
| **Spatial Resolution** | $10 \, \text{m} \times 10 \, \text{m}$ pixel spacing ($20 \, \text{m}$ spatial resolution) with $250 \, \text{km}$ swath width |
| **Temporal Resolution** | 6–12 day repeat orbit revisit over oceanic shipping corridors |
| **Authentication** | CDSE OAuth2 bearer token / API key |
| **Scientific Limitations** | • Ocean surface wind speed must be between $3.0 \, \text{m/s}$ and $12.0 \, \text{m/s}$ (at $<3 \, \text{m/s}$, calm sea resembles slicks; at $>12 \, \text{m/s}$, waves break up oil films).<br>• Radar speckle noise requires multi-look adaptive filtering.<br>• Inability to distinguish oil thickness or chemical grade directly from single-channel SAR backscatter. |
| **Licensing / Usage** | **Open Access Free Data Policy:** Creative Commons CC-BY 4.0 / Copernicus Open Data Policy. |

---

### 2.2 Automatic Identification System (AIS) Vessel Tracks

| Attribute | Specification |
|---|---|
| **Primary Sources** | Spire Maritime Historical AIS API / AISHub / Global Fishing Watch (GFW) / NOAA MarineCadastre |
| **Data Format** | GeoJSON / CSV / NMEA 0183 decoded messages (Type 1, 2, 3 position reports, Type 5 static/voyage data) |
| **Telemetry Fields** | `mmsi`, `imo`, `vessel_name`, `vessel_type`, `timestamp_utc`, `longitude`, `latitude`, `sog_knots`, `cog_deg`, `nav_status`, `destination`, `draught` |
| **Spatial Resolution** | Sub-meter GPS precision ($\pm 5 - 10 \, \text{m}$) |
| **Temporal Resolution** | Variable ping interval (every 2–10 seconds for dynamic Class A underway; 5–15 minutes for Satellite S-AIS) |
| **Authentication** | REST API Token / HTTPS Bearer Header / S3 Bucket Access Keys |
| **Scientific Limitations** | • **Transponder Outages / Gaps:** Deliberate or accidental transponder switch-offs in international waters.<br>• **Terrestrial vs Satellite Latency:** Shore-based AIS ranges typically $< 40 \, \text{nmi}$; satellite AIS subject to packet collisions in high-density choke points (e.g. Malacca Strait, English Channel).<br>• **Identity Spoofing:** Requires cross-referencing MMSI with static IMO registry data. |
| **Licensing / Usage** | • Commercial providers (Spire, MarineTraffic): Proprietary commercial license.<br>• Open datasets (GFW, NOAA): CC-BY 4.0 Open Data. |

---

### 2.3 Oceanographic Hydrodynamic Currents

| Attribute | Specification |
|---|---|
| **Primary Source** | Copernicus Marine Environment Monitoring Service (CMEMS) |
| **Product Identifier** | `GLOBAL_ANALYSISFORECAST_PHY_001_024` (Global Ocean Physics Analysis and Forecast) |
| **Data Format** | NetCDF-4 / OPeNDAP with CF-1.6 conventions |
| **Key Variables** | `uo` (Eastward surface seawater velocity, $\text{m/s}$), `vo` (Northward surface seawater velocity, $\text{m/s}$), `zos` (Sea surface height) |
| **Spatial Resolution** | $1/12^\circ$ horizontal grid spacing ($\approx 9.25 \, \text{km} \times 9.25 \, \text{km}$ at equator) with 50 vertical depth levels |
| **Temporal Resolution** | Daily mean and 3-hourly instantaneous velocity field forecasts/hindcasts |
| **Authentication** | CMEMS Copernicus Marine credentials (Username & API Token) |
| **Scientific Limitations** | • Sub-mesoscale coastal eddies ($< 5 \, \text{km}$) and shallow bathymetric boundary friction are smoothed out in global models.<br>• Tidal constituent currents require supplemental tidal hydrodynamic harmonic model coupling (e.g. TPXO9). |
| **Licensing / Usage** | Free and open access for all users under the Copernicus Marine Service data license. |

---

### 2.4 Atmospheric Surface Wind Reanalysis

| Attribute | Specification |
|---|---|
| **Primary Source** | European Centre for Medium-Range Weather Forecasts (ECMWF) ERA5 / NOAA NCEP GFS |
| **Product Identifier** | ERA5 hourly data on single levels from 1940 to present (`reanalysis-era5-single-levels`) |
| **Data Format** | NetCDF-4 / GRIB2 |
| **Key Variables** | `u10` (10-meter U-wind component, $\text{m/s}$), `v10` (10-meter V-wind component, $\text{m/s}$), `sp` (Surface air pressure, $\text{Pa}$) |
| **Spatial Resolution** | $0.25^\circ \times 0.25^\circ$ ($\approx 31 \, \text{km} \times 31 \, \text{km}$) |
| **Temporal Resolution** | Hourly reanalysis steps ($T_{00:00}, T_{01:00}, \dots, T_{23:00}$) |
| **Authentication** | ECMWF Copernicus Climate Data Store (CDS) API key (`~/.cdsapirc`) |
| **Scientific Limitations** | • Coastal orography wind deflection and localized squalls/thunderstorms ($< 10 \, \text{km}$) may be underestimated.<br>• Wind leeway factor approximation ($\alpha = 0.03 \pm 0.005$) introduces stochastic dispersion spreading over long integration horizons ($> 48\text{h}$). |
| **Licensing / Usage** | Open Access license under Copernicus Climate Change Service (C3S). |

---

## 3. Provider Testing & Synthetic Isolation

In accordance with `GEMINI.md`:
- **Synthetic Providers (`backend/app/providers/synthetic.py`)** remain permanently accessible and active by default.
- Unit and regression test suites execute offline deterministically with zero network calls.
- Real historical dataset integrations will be added via dedicated provider subclasses implementing `SARDataProvider`, `AISDataProvider`, `OceanCurrentProvider`, and `WindDataProvider`.
