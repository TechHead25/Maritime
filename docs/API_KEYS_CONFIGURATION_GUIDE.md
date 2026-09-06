# Maritime Oil-Spill Attribution Intelligence
## Complete API Keys & Environment Configuration Guide

This document provides a comprehensive operational guide to all external API keys, credentials, registration links, and environment variables utilized across the platform backend (Render) and frontend (Vercel).

---

### Executive Summary: API Credentials Matrix

| Environment Variable | Provider / Service | Purpose / Feature Unlocked | Cost / Tier | Required / Optional |
| :--- | :--- | :--- | :--- | :--- |
| **AISSTREAM_API_KEY** | [aisstream.io](https://aisstream.io) | Live satellite & terrestrial AIS real-time transponder feed streaming (/app/live) | Free Tier | **Configured** (Recommended for Live Tracking) |
| **CDSE_CLIENT_ID** | [Copernicus Data Space](https://dataspace.copernicus.eu) | Query & ingest Sentinel-1 SAR GRD satellite imagery via OData & STAC APIs | Free (EU Copernicus) | Optional (Required for Live SAR Downloads) |
| **CDSE_CLIENT_SECRET** | [Copernicus Data Space](https://dataspace.copernicus.eu) | OAuth2 client secret for CDSE identity authentication | Free (EU Copernicus) | Optional (Required with CDSE_CLIENT_ID) |
| **COPERNICUS_MARINE_USERNAME** | [Copernicus Marine (CMEMS)](https://marine.copernicus.eu) | Ocean hydrodynamic current models (Global Analysis & Forecast 0.083° NetCDF) | Free (CMEMS Open) | Optional (Offline archive fallback included) |
| **COPERNICUS_MARINE_PASSWORD** | [Copernicus Marine (CMEMS)](https://marine.copernicus.eu) | HTTP Basic Auth password for CMEMS Subsetter / WMS data access | Free (CMEMS Open) | Optional (Required with username) |
| **JWT_SECRET** | Internal Platform Security | Cryptographic HS256 secret key for signing user authentication session tokens | N/A (Internal) | Recommended (Has secure fallback) |
| **CORS_ORIGINS** | Backend Security | Allowed client URLs (https://maritime-iota.vercel.app,http://localhost:5173) | N/A (Internal) | Pre-configured on Render |

---

### 1. Live AIS Streaming: AISSTREAM_API_KEY

#### Purpose
Enables real-time ingestion of live vessel broadcasts (Position Reports, Static Voyage Data) across maritime shipping corridors directly into the backend WebSocket consumer and streams them to the interactive UI via Server-Sent Events (SSE).

#### Current Status
- **Already Added** to your Render environment!
- The platform uses decoupled asynchronous queueing so that high-volume messages never stall the network socket.

#### Key Registration & Retrieval Steps
1. Navigate to **[https://aisstream.io](https://aisstream.io)**.
2. Sign in to your account or create a free account.
3. Click on **Dashboard / API Keys**.
4. Generate or copy your 32-character API key string.
5. **Render Variable**: AISSTREAM_API_KEY = <your-api-key>.

---

### 2. Copernicus Data Space Ecosystem: CDSE_CLIENT_ID & CDSE_CLIENT_SECRET

#### Purpose
Used by the satellite ingestion provider to search and stream European Space Agency (ESA) **Sentinel-1 C-band SAR GRD** products over any geographic bounding box and date range.

#### What Happens If Unset?
The platform seamlessly uses its verified historical high-resolution SAR datasets (such as the verified Sentinel-1 IW GRDH acquisition for the MT New Diamond incident and Ennore case). Adding these credentials enables real-time dynamic searches for any global oil spill coordinate.

#### Step-by-Step Registration & Key Creation
1. Go to the **Copernicus Data Space Portal**:  
   **[https://dataspace.copernicus.eu](https://dataspace.copernicus.eu)**
2. Click **Register** (top-right) and confirm your email.
3. Once logged in, navigate to the **CDSE Identity & User Management** page:  
   **[https://identity.dataspace.copernicus.eu/auth/realms/CDSE/account](https://identity.dataspace.copernicus.eu/auth/realms/CDSE/account)**
4. In the left navigation menu, click **OAuth Clients** or **API Keys**.
5. Click **Create New Client** / **Generate Client Credentials**:
   - **Name:** Maritime-Oil-Attribution
   - **Redirect URI:** http://localhost (or leave blank if optional)
6. Copy the two generated values:
   - **Client ID** (e.g., cdse-client-xxxx-xxxx)
   - **Client Secret** (e.g., s3cr3t-xxxx-xxxx-xxxx)
7. **Render Environment Configuration:**
   - Name: CDSE_CLIENT_ID | Value: <your-client-id>
   - Name: CDSE_CLIENT_SECRET | Value: <your-client-secret>

---

### 3. Copernicus Marine Service (CMEMS): COPERNICUS_MARINE_USERNAME & COPERNICUS_MARINE_PASSWORD

#### Purpose
Powers the backward Lagrangian drift simulation by dynamically downloading real ocean current vectors (u-eastward, v-northward velocity grids) from the Global Ocean Physics Analysis and Forecast model (cmems_mod_glo_phy_my_0.083deg_P1D-m).

#### What Happens If Unset?
The system automatically utilizes verified calibrated NetCDF ocean models pre-bundled in data/ocean_models/ covering the Indian Ocean, Bay of Bengal, and Arabian Sea. Adding credentials allows on-demand global hydrodynamic current ingestion for any custom coordinate worldwide.

#### Step-by-Step Registration
1. Navigate to **[https://marine.copernicus.eu](https://marine.copernicus.eu)**.
2. Click **Register** (completely free, open-access EU initiative).
3. Fill out the academic/research profile (e.g., 'Maritime Environmental Research').
4. Verify your account via email.
5. Your login credentials are used directly for API access:
   - **Username:** Your registered CMEMS username or email.
   - **Password:** Your account password.
6. **Render Environment Configuration:**
   - Name: COPERNICUS_MARINE_USERNAME | Value: <your-cmems-username>
   - Name: COPERNICUS_MARINE_PASSWORD | Value: <your-cmems-password>

---

### 4. Zero Watermark Map Basemap: Esri World Dark Gray

#### Purpose
Renders high-contrast dark naval cartography in Leaflet (/app/live and /app/investigations/:id).

#### Key Advantage
- **Zero API Keys Required**: We migrated away from CARTO (which required personal tokens and showed watermarks) to the authoritative **Esri ArcGIS World Dark Gray Canvas** base and reference layers.
- **Cost:** Free, no quota limits, zero setup.

---

### 5. Deployment Environment Setup Walkthrough

#### Setting Environment Variables on Render (Backend)
1. Log into your Render dashboard: **[https://dashboard.render.com](https://dashboard.render.com)**.
2. Select your backend service: **maritime-backend-lcnu**.
3. Navigate to the **Environment** tab on the left sidebar.
4. Add or verify the following key-value pairs:
   - AISSTREAM_API_KEY: (Already added)
   - CDSE_CLIENT_ID: (Optional - for Sentinel-1 live satellite download)
   - CDSE_CLIENT_SECRET: (Optional - for Sentinel-1 live satellite download)
   - COPERNICUS_MARINE_USERNAME: (Optional - for live CMEMS ocean currents)
   - COPERNICUS_MARINE_PASSWORD: (Optional - for live CMEMS ocean currents)
   - CORS_ORIGINS: https://maritime-iota.vercel.app,http://localhost:5173
   - LOG_LEVEL: INFO
5. Click **Save Changes**. Render will automatically redeploy with the active credentials.

#### Setting Environment Variables on Vercel (Frontend)
1. Log into your Vercel dashboard: **[https://vercel.com](https://vercel.com)**.
2. Select your project: **maritime-iota**.
3. Navigate to **Settings** -> **Environment Variables**.
4. Verify the backend connection variable:
   - VITE_API_BASE_URL: https://maritime-backend-lcnu.onrender.com/api
5. Save changes and redeploy if necessary.

---

### Summary Checklist

| Action Item | Status | Priority |
| :--- | :--- | :--- |
| Configure AISSTREAM_API_KEY on Render | **Completed** | High (Live AIS) |
| Decouple Live AIS WebSocket loop with Async Queue | **Completed** | High (Stability) |
| Integrate Verified Maritime Seed Cache | **Completed** | High (Zero Blank Map) |
| Register CDSE account for live Sentinel-1 SAR | Optional | Medium (Dynamic SAR) |
| Register CMEMS account for live Ocean Currents | Optional | Medium (Dynamic Hydrodynamics) |
