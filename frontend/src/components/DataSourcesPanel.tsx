import React from 'react';

interface Props {
  dataSources?: Record<string, any>;
  isSynthetic?: boolean;
}

export const DataSourcesPanel: React.FC<Props> = ({
  dataSources = {},
  isSynthetic = false,
}) => {
  return (
    <div style={{
      backgroundColor: '#0f172a',
      border: '1px solid #1e293b',
      borderRadius: '8px',
      padding: '1.25rem',
      marginBottom: '1rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc' }}>
            🛰 Sensor Telemetry Lineage & Provenance
          </h3>
          <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
            Explicit separation of raw observation sensors from numerical physics models
          </span>
        </div>

        <span style={{
          fontSize: '0.70rem',
          fontWeight: 700,
          color: isSynthetic ? '#f59e0b' : '#10b981',
          backgroundColor: isSynthetic ? '#f59e0b15' : '#10b98115',
          border: `1px solid ${isSynthetic ? '#f59e0b40' : '#10b98140'}`,
          padding: '0.15rem 0.5rem',
          borderRadius: '4px',
        }}>
          {isSynthetic ? 'SYNTHETIC BENCHMARK' : 'HISTORICAL SENSOR DATA'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem', fontSize: '0.78rem' }}>
        {/* SAR Satellite */}
        <div style={{ backgroundColor: '#1e293b', padding: '0.65rem 0.85rem', borderRadius: '6px', borderLeft: `3px solid ${dataSources.sar_platform ? '#10b981' : '#ef4444'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.68rem', fontWeight: 600 }}>SAR RADAR IMAGERY</span>
            <span style={{ color: dataSources.sar_platform ? '#10b981' : '#ef4444', fontSize: '0.65rem', fontWeight: 700 }}>
              {dataSources.sar_platform ? 'OBSERVED DATA' : 'DATA SOURCE UNAVAILABLE'}
            </span>
          </div>
          <strong style={{ color: dataSources.sar_platform ? '#f8fafc' : '#f87171' }}>
            {dataSources.sar_platform || 'No SAR raster imagery provided'}
          </strong>
        </div>

        {/* AIS Tracks */}
        <div style={{ backgroundColor: '#1e293b', padding: '0.65rem 0.85rem', borderRadius: '6px', borderLeft: `3px solid ${dataSources.ais_provider !== false ? '#10b981' : '#ef4444'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.68rem', fontWeight: 600 }}>AIS VESSEL TELEMETRY</span>
            <span style={{ color: dataSources.ais_provider !== false ? '#10b981' : '#ef4444', fontSize: '0.65rem', fontWeight: 700 }}>
              {dataSources.ais_provider !== false ? 'OBSERVED DATA' : 'DATA SOURCE UNAVAILABLE'}
            </span>
          </div>
          <strong style={{ color: dataSources.ais_provider !== false ? '#f8fafc' : '#f87171' }}>
            {dataSources.ais_provider || 'Historical Terrestrial + Satellite AIS'}
          </strong>
        </div>

        {/* Ocean Hydrodynamics */}
        <div style={{ backgroundColor: '#1e293b', padding: '0.65rem 0.85rem', borderRadius: '6px', borderLeft: `3px solid ${dataSources.hydrodynamic_model !== false ? '#38bdf8' : '#ef4444'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.68rem', fontWeight: 600 }}>HYDRODYNAMIC CURRENTS</span>
            <span style={{ color: dataSources.hydrodynamic_model !== false ? '#38bdf8' : '#ef4444', fontSize: '0.65rem', fontWeight: 700 }}>
              {dataSources.hydrodynamic_model !== false ? 'MODEL ESTIMATE' : 'DATA SOURCE UNAVAILABLE'}
            </span>
          </div>
          <strong style={{ color: dataSources.hydrodynamic_model !== false ? '#f8fafc' : '#f87171' }}>
            {dataSources.hydrodynamic_model || 'CMEMS Global Ocean Physics (0.083°)'}
          </strong>
        </div>

        {/* Atmospheric Winds */}
        <div style={{ backgroundColor: '#1e293b', padding: '0.65rem 0.85rem', borderRadius: '6px', borderLeft: `3px solid ${dataSources.meteorological_model !== false ? '#38bdf8' : '#ef4444'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.68rem', fontWeight: 600 }}>ATMOSPHERIC SURFACE WIND</span>
            <span style={{ color: dataSources.meteorological_model !== false ? '#38bdf8' : '#ef4444', fontSize: '0.65rem', fontWeight: 700 }}>
              {dataSources.meteorological_model !== false ? 'MODEL ESTIMATE' : 'DATA SOURCE UNAVAILABLE'}
            </span>
          </div>
          <strong style={{ color: dataSources.meteorological_model !== false ? '#f8fafc' : '#f87171' }}>
            {dataSources.meteorological_model || 'ECMWF ERA5 Atmospheric Reanalysis'}
          </strong>
        </div>
      </div>
    </div>
  );
};
