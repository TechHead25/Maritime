# Enterprise Data Provider Architecture

**System:** Maritime Oil-Spill Attribution Intelligence Platform  
**Module:** Data Provider & Observational Ingestion Layer  
**Specification:** `docs/DATA_PROVIDER_ARCHITECTURE.md`

---

## 1. Architectural Overview

The platform decouples the core scientific calculation engines (Lagrangian backward drift, CFAR segmentation, multi-factor attribution) from external telemetry, environmental, and satellite sensor APIs.

```
                          +-------------------------------------------------+
                          |             DATA SOURCE CONTROL CENTER          |
                          |                 (/app/data-sources)             |
                          +------------------------+------------------------+
                                                   |
            +--------------------------------------+--------------------------------------+
            |                                      |                                      |
+-----------v-----------+              +-----------v-----------+              +-----------v-----------+
|   EARTH OBSERVATION   |              |          AIS          |              |         OCEAN         |
|  (Copernicus CDSE /   |              |  (AISStream.io /      |              |  (Copernicus Marine   |
|   Sentinel-1 SAR)     |              |   Terrestrial NMEA)   |              |   CMEMS Physics)      |
+-----------------------+              +-----------------------+              +-----------------------+
            |                                      |                                      |
+-----------v-----------+              +-----------v-----------+              +-----------v-----------+
|        WEATHER        |              |    VESSEL IDENTITY    |              |        BASEMAP        |
|  (Open-Meteo Marine / |              |  (ITU MARS / Equasis  |              |  (CARTO Dark Matter   |
|   ECMWF ERA5 Winds)   |              |   Verified Directory) |              |   Nautical Tiles)     |
+-----------------------+              +-----------------------+              +-----------------------+
```

---

## 2. Configured External Data Providers

| Category | Canonical Provider | Service / Endpoint | Authentication Strategy | Primary Data Modality |
|---|---|---|---|---|
| **Earth Observation** | Copernicus Data Space Ecosystem (CDSE) | Sentinel-1 OData / STAC API | OAuth2 Client Credentials (`COPERNICUS_CDSE_CLIENT_ID`) | C-Band SAR GRD / SLC (10–20m resolution, VV/VH) |
| **AIS** | AISStream.io / Terrestrial Receiver Gateway | WebSocket Stream & Historical CSV Archive | WebSocket API Key (`AISSTREAM_API_KEY`) | Class A & B AIS Dynamic & Static Kinematic Frames |
| **Ocean** | Copernicus Marine (CMEMS) | Data Store / Subsetter API (`GLOBAL_ANALYSISFORECAST_PHY_001_024`) | Copernicus Marine CAS Token (`COPERNICUS_MARINE_USERNAME`) | 3D Hydrodynamic Velocity Vectors ($u, v$ in m/s at 0.083°) |
| **Weather** | Open-Meteo Marine & ECMWF ERA5 | Marine Reanalysis API | Public Open Access / Open Data | 10m Marine Surface Wind Vectors ($u_{10}, v_{10}$ in m/s) |
| **Vessel Identity** | ITU MARS & Equasis | Maritime Registry Directory Adapter | Open Directory Standard | Verified IMO, MMSI, Call Sign, Flag, DWT, Beam, Owner |
| **Basemap** | CARTO & OpenStreetMap | Dark Matter XYZ Vector / Raster Tile Service | Public CDN (Unmetered) | High-contrast nautical basemap tiles (PNG/WebP) |

---

## 3. Credential Security & Masking Policy

Strict enforcement of operational security principles:
- **Environment-Backed Configuration:** All sensitive secrets (`API_KEY`, `CLIENT_SECRET`, `PASSWORD`) are stored exclusively in backend process environment variables (`.env`).
- **Zero Frontend Bundle Exposure:** No API keys or secret tokens are embedded in frontend source code, client-side bundles, or repository source control.
- **Strict API Response Masking:** Control Center and health endpoints mask all credentials before transmission. For example:
  - Raw Secret: `copernicus_production_secret_key_84920`
  - Masked Over Wire: `cdse_***_key`
  - Auth Status: `CONFIGURED` / `OPEN_ACCESS` / `UNCONFIGURED`

---

## 4. Provider-Specific Freshness Thresholds

Data freshness is evaluated using modality-specific oceanographic and operational criteria:

$$\Delta t = t_{\text{current}} - t_{\text{last\_observation}}$$

| Provider Category | Fresh ($\Delta t$) | Aging ($\Delta t$) | Stale ($\Delta t$) | Unavailable | Physical Rationale |
|---|---|---|---|---|---|
| **Earth Observation (SAR)** | $\le 48\text{ h}$ | $48\text{ h} < \Delta t \le 7\text{ d}$ | $> 7\text{ d}$ | Service unreachable | Sentinel-1 repeat orbit constellation cycle (6–12 days). |
| **AIS Telemetry** | $\le 5\text{ min}$ | $5\text{ min} < \Delta t \le 2\text{ h}$ | $> 2\text{ h}$ | Stream offline | Real-time coastal transponder message frequency (2s–3min). |
| **Ocean Currents** | $\le 24\text{ h}$ | $24\text{ h} < \Delta t \le 48\text{ h}$ | $> 48\text{ h}$ | Grid server down | CMEMS daily forecast assimilation cycle. |
| **Marine Weather** | $\le 6\text{ h}$ | $6\text{ h} < \Delta t \le 24\text{ h}$ | $> 24\text{ h}$ | Endpoint error | ECMWF IFS / ERA5 6-hourly atmospheric analysis cycles. |
| **Vessel Identity** | $\le 30\text{ d}$ | $30\text{ d} < \Delta t \le 90\text{ d}$ | $> 90\text{ d}$ | Database missing | Official flag state and IMO registry audit frequency. |
| **Nautical Basemap** | $\le 24\text{ h}$ | $24\text{ h} < \Delta t \le 7\text{ d}$ | $> 7\text{ d}$ | CDN unreachable | Map tile CDN cache TTL. |

---

## 5. Immutable Provenance Tracking

Every investigation case immutably retains complete scientific lineage for all ingested data. Provenance records are attached to each observation and persisted in the case dossier:

```json
{
  "provider": "Copernicus Data Space Ecosystem (CDSE / ESA)",
  "dataset": "Sentinel-1 Synthetic Aperture Radar (SAR)",
  "product": "S1A_IW_GRDH_1SDV_20200903T004310_20200903T004335_034187_03F8ED_7A12",
  "observation_time_utc": "2020-09-03T00:43:10Z",
  "retrieval_time_utc": "2026-09-03T05:22:15Z",
  "geographic_extent": [80.5, 5.5, 84.5, 9.5],
  "resolution": "10m ground pixel resolution",
  "version": "IPF 003.31",
  "checksum_sha256": "8f49a7c3d2e1b09847156291a27e436894c2194a86b1f284c10729486c91a702",
  "request_parameters": {
    "sensor_mode": "IW",
    "polarization": "VV",
    "orbit_direction": "DESCENDING"
  }
}
```

---

## 6. Transparent Failure Handling & Anti-Fabrication Principles

In strict accordance with `GEMINI.md`:
1. **Zero Data Fabrication:** The system will never generate fake satellite dark patches, simulated AIS vessels, or synthetic wind grids in production.
2. **Actual Failure Visibility:** When an external service is unavailable (e.g. invalid API credentials, HTTP 429 rate-limited, network timeout), the UI displays the exact error message and operational status (`UNCONFIGURED` or `OFFLINE`).
3. **Explicit Fallback Policy:** The system will never silently substitute data. Fallback to local verified archives (e.g., historical Sentinel-1 GeoTIFF or local AIS CSV) only occurs when explicitly authorized in configuration, and the UI visibly discloses the verified fallback source.
