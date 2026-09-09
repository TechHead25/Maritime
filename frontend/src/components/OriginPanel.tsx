import React from 'react';
import { GeoPoint } from '../types';

interface Props {
  originCentroid?: GeoPoint;
  originUncertaintyKm?: number;
  slickCentroid?: GeoPoint;
}

export const OriginPanel: React.FC<Props> = ({
  originCentroid,
  originUncertaintyKm = 1.0,
  slickCentroid,
}) => {
  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--glass-border)',
      borderRadius: '8px',
      padding: '1rem 1.25rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
          📍 Probable Origin
        </h3>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
          Peak Likelihood Centroid
        </span>
      </div>

      {originCentroid ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.82rem' }}>
          <div style={{ backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)', padding: '0.6rem 0.75rem', borderRadius: '6px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem', display: 'block' }}>ESTIMATED COORDINATES</span>
            <strong style={{ color: '#f8fafc', fontSize: '0.92rem' }}>
              {originCentroid.coordinates[0].toFixed(4)}°E, {originCentroid.coordinates[1].toFixed(4)}°N
            </strong>
          </div>

          <div style={{ backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)', padding: '0.6rem 0.75rem', borderRadius: '6px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem', display: 'block' }}>95% DISPERSION RADIUS</span>
            <strong style={{ color: 'var(--accent-cyan)', fontSize: '0.92rem' }}>
              ± {originUncertaintyKm.toFixed(2)} km
            </strong>
          </div>

          {slickCentroid && (
            <div style={{ gridColumn: 'span 2', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Displacement reference from observed SAR centroid: ({slickCentroid.coordinates[0].toFixed(3)}°E, {slickCentroid.coordinates[1].toFixed(3)}°N)
            </div>
          )}
        </div>
      ) : (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', padding: '0.5rem 0' }}>
          Run the drift simulation or forensic pipeline to estimate probable spill origin coordinates.
        </div>
      )}
    </div>
  );
};
