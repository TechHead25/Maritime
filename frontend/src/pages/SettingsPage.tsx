import React, { useState } from 'react';
import {
  Database,
  Key,
  Sliders,
  MapPin,
  Server,
  Save,
  CheckCircle2,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Editable settings states
  const [particleCount, setParticleCount] = useState<number>(500);
  const [timeStepMinutes, setTimeStepMinutes] = useState<number>(30);
  const [leewayFactor, setLeewayFactor] = useState<number>(0.030);
  const [diffusivity, setDiffusivity] = useState<number>(2.5);
  const [maxCpaKm, setMaxCpaKm] = useState<number>(10.0);
  const [mapBaseLayer, setMapBaseLayer] = useState<string>('carto-dark');
  const [coordFormat, setCoordFormat] = useState<string>('DD');
  const [gridOverlay, setGridOverlay] = useState<boolean>(true);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            System & Forensic Configuration
          </h1>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.25rem', marginBottom: 0 }}>
            Manage remote data provider endpoints, API credentials status, simulation parameters, and map options.
          </p>
        </div>

        <button
          onClick={handleSave}
          style={{
            backgroundColor: '#0284c7',
            border: 'none',
            color: '#ffffff',
            padding: '0.50rem 1.15rem',
            borderRadius: '6px',
            fontSize: '0.82rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            boxShadow: '0 2px 8px rgba(2, 132, 199, 0.3)',
          }}
        >
          <Save size={15} /> Save Configuration
        </button>
      </div>

      {saveSuccess && (
        <div style={{
          backgroundColor: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid #10b981',
          color: '#34d399',
          padding: '0.75rem 1.25rem',
          borderRadius: '6px',
          fontSize: '0.82rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <CheckCircle2 size={16} /> Configuration saved successfully.
        </div>
      )}

      {/* 1. Data Providers Configuration */}
      <div style={panelCardStyle}>
        <div style={panelHeaderStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Database size={18} color="#38bdf8" />
            <h2 style={panelTitleStyle}>Data Provider Endpoints</h2>
          </div>
          <span style={panelSubtitleStyle}>Configured upstream sensor repositories</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.80rem' }}>
          <div>
            <label style={labelStyle}>Copernicus Data Space Ecosystem (CDSE) REST URL</label>
            <input
              type="text"
              readOnly
              value="https://catalogue.dataspace.copernicus.eu/resto/api"
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle}>AIS Ingestion Local Spool / Stream Directory</label>
            <input
              type="text"
              readOnly
              value="data/ais_archive"
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle}>CMEMS Global Ocean Hydrodynamics Service</label>
            <input
              type="text"
              readOnly
              value="https://nrt.cmems-du.eu/thredds/wms/global-analysis-forecast-phy-001-024"
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle}>ECMWF Climate Data Store (CDS) Surface Winds</label>
            <input
              type="text"
              readOnly
              value="https://cds.climate.copernicus.eu/api/v2"
              style={inputStyle}
            />
          </div>
        </div>
      </div>

      {/* 2. API Credentials Status (No raw secrets exposed!) */}
      <div style={panelCardStyle}>
        <div style={panelHeaderStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Key size={18} color="#f59e0b" />
            <h2 style={panelTitleStyle}>API Credentials Status</h2>
          </div>
          <span style={panelSubtitleStyle}>Secure hardware & vault token indicators</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem', fontSize: '0.80rem' }}>
          <div style={credentialBoxStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
              <strong style={{ color: '#f8fafc' }}>Copernicus CDSE Client ID</strong>
              <span style={verifiedBadgeStyle}>Configured</span>
            </div>
            <div style={{ color: '#94a3b8', fontFamily: 'monospace', fontSize: '0.75rem' }}>
              cdse-marine-ops-key
            </div>
          </div>

          <div style={credentialBoxStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
              <strong style={{ color: '#f8fafc' }}>Copernicus CDSE Secret</strong>
              <span style={verifiedBadgeStyle}>Encrypted</span>
            </div>
            <div style={{ color: '#64748b', fontFamily: 'monospace', fontSize: '0.75rem' }}>
              ••••••••••••••••••••••••••••••••
            </div>
          </div>

          <div style={credentialBoxStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
              <strong style={{ color: '#f8fafc' }}>CMEMS Access Token</strong>
              <span style={verifiedBadgeStyle}>Verified</span>
            </div>
            <div style={{ color: '#64748b', fontFamily: 'monospace', fontSize: '0.75rem' }}>
              ••••••••••••••••••••••••••••••••
            </div>
          </div>

          <div style={credentialBoxStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
              <strong style={{ color: '#f8fafc' }}>ECMWF CDS API Key</strong>
              <span style={verifiedBadgeStyle}>Configured</span>
            </div>
            <div style={{ color: '#64748b', fontFamily: 'monospace', fontSize: '0.75rem' }}>
              ••••••••••••••••••••••••••••••••
            </div>
          </div>
        </div>
      </div>

      {/* 3. Scientific Processing Defaults */}
      <div style={panelCardStyle}>
        <div style={panelHeaderStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sliders size={18} color="#10b981" />
            <h2 style={panelTitleStyle}>Scientific Processing Defaults</h2>
          </div>
          <span style={panelSubtitleStyle}>Governing Lagrangian drift & attribution parameters</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', fontSize: '0.80rem' }}>
          <div>
            <label style={labelStyle}>Default Particle Count</label>
            <input
              type="number"
              value={particleCount}
              onChange={(e) => setParticleCount(Number(e.target.value))}
              min={100}
              max={5000}
              step={100}
              style={inputStyle}
            />
            <span style={hintStyle}>Standard: 500 swarms</span>
          </div>

          <div>
            <label style={labelStyle}>Simulation Time Step (min)</label>
            <input
              type="number"
              value={timeStepMinutes}
              onChange={(e) => setTimeStepMinutes(Number(e.target.value))}
              min={10}
              max={60}
              step={5}
              style={inputStyle}
            />
            <span style={hintStyle}>$\Delta t$ advection interval</span>
          </div>

          <div>
            <label style={labelStyle}>Wind Leeway Factor ($\alpha$)</label>
            <input
              type="number"
              value={leewayFactor}
              onChange={(e) => setLeewayFactor(Number(e.target.value))}
              min={0.01}
              max={0.06}
              step={0.005}
              style={inputStyle}
            />
            <span style={hintStyle}>Standard: 0.030 (3.0%)</span>
          </div>

          <div>
            <label style={labelStyle}>Horizontal Diffusivity ($K_h$)</label>
            <input
              type="number"
              value={diffusivity}
              onChange={(e) => setDiffusivity(Number(e.target.value))}
              min={0.5}
              max={10.0}
              step={0.5}
              style={inputStyle}
            />
            <span style={hintStyle}>Standard: 2.5 m²/s</span>
          </div>

          <div>
            <label style={labelStyle}>Max CPA Interception (km)</label>
            <input
              type="number"
              value={maxCpaKm}
              onChange={(e) => setMaxCpaKm(Number(e.target.value))}
              min={1.0}
              max={30.0}
              step={1.0}
              style={inputStyle}
            />
            <span style={hintStyle}>Candidate search radius</span>
          </div>
        </div>
      </div>

      {/* 4. Map Display Settings */}
      <div style={panelCardStyle}>
        <div style={panelHeaderStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <MapPin size={18} color="#38bdf8" />
            <h2 style={panelTitleStyle}>Geospatial Map Settings</h2>
          </div>
          <span style={panelSubtitleStyle}>Cartographic basemap and coordinate representation</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.80rem' }}>
          <div>
            <label style={labelStyle}>Default Basemap Provider</label>
            <select
              value={mapBaseLayer}
              onChange={(e) => setMapBaseLayer(e.target.value)}
              style={inputStyle}
            >
              <option value="carto-dark">CARTO Dark Matter (High-Contrast Marine)</option>
              <option value="carto-positron">CARTO Positron (Light)</option>
              <option value="osm">OpenStreetMap Standard</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>Coordinate Representation</label>
            <select
              value={coordFormat}
              onChange={(e) => setCoordFormat(e.target.value)}
              style={inputStyle}
            >
              <option value="DD">Decimal Degrees (DD: 7.7820°N, 82.5030°E)</option>
              <option value="DDM">Degrees Decimal Minutes (DDM: 7° 46.92' N)</option>
            </select>
          </div>

          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#cbd5e1', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={gridOverlay}
                onChange={(e) => setGridOverlay(e.target.checked)}
                style={{ accentColor: '#0284c7' }}
              />
              <span>Render Graticule Coordinate Grid on Nautical Map</span>
            </label>
          </div>
        </div>
      </div>

      {/* 5. System Configuration */}
      <div style={panelCardStyle}>
        <div style={panelHeaderStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Server size={18} color="#a855f7" />
            <h2 style={panelTitleStyle}>System Architecture & Limits</h2>
          </div>
          <span style={panelSubtitleStyle}>Server environment and storage paths</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem', fontSize: '0.80rem' }}>
          <div>
            <span style={labelStyle}>FASTAPI BACKEND SERVICE</span>
            <span style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>http://127.0.0.1:8000</span>
          </div>

          <div>
            <span style={labelStyle}>DURABLE CASE REPOSITORY</span>
            <span style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>data/cases/</span>
          </div>

          <div>
            <span style={labelStyle}>IN-MEMORY LRU CACHE</span>
            <span style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>512 MB (Active)</span>
          </div>

          <div>
            <span style={labelStyle}>UNIVERSAL TIMESTAMP STANDARD</span>
            <span style={{ color: '#34d399', fontWeight: 600 }}>ISO 8601 UTC (Strict Enforcement)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const panelCardStyle: React.CSSProperties = {
  backgroundColor: '#0c1322',
  border: '1px solid #1e293b',
  borderRadius: '8px',
  padding: '1.25rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '1rem',
};

const panelHeaderStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  borderBottom: '1px solid #1e293b',
  paddingBottom: '0.75rem',
};

const panelTitleStyle: React.CSSProperties = {
  fontSize: '0.95rem',
  fontWeight: 700,
  color: '#f8fafc',
  margin: 0,
};

const panelSubtitleStyle: React.CSSProperties = {
  fontSize: '0.70rem',
  color: '#64748b',
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.68rem',
  fontWeight: 700,
  color: '#64748b',
  display: 'block',
  marginBottom: '0.25rem',
  letterSpacing: '0.03em',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  backgroundColor: '#131b2e',
  border: '1px solid #1e293b',
  color: '#f8fafc',
  padding: '0.45rem 0.65rem',
  borderRadius: '4px',
  fontSize: '0.80rem',
  outline: 'none',
  boxSizing: 'border-box',
};

const hintStyle: React.CSSProperties = {
  fontSize: '0.68rem',
  color: '#64748b',
  marginTop: '0.2rem',
  display: 'block',
};

const credentialBoxStyle: React.CSSProperties = {
  backgroundColor: '#111827',
  border: '1px solid #1e293b',
  borderRadius: '6px',
  padding: '0.75rem',
};

const verifiedBadgeStyle: React.CSSProperties = {
  fontSize: '0.65rem',
  fontWeight: 700,
  color: '#34d399',
  backgroundColor: 'rgba(16, 185, 129, 0.12)',
  padding: '0.1rem 0.4rem',
  borderRadius: '3px',
};
