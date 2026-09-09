import React from 'react';
import { ReleaseWindow } from '../types';

interface Props {
  releaseWindow?: ReleaseWindow;
}

export const ReleaseWindowPanel: React.FC<Props> = ({ releaseWindow }) => {
  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--glass-border)',
      borderRadius: '8px',
      padding: '1rem 1.25rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--accent-amber)' }}>
          ⏱ Estimated Discharge Release Window
        </h3>
        <span style={{ fontSize: '0.72rem', color: '#10b981', backgroundColor: '#10b98115', border: '1px solid var(--glass-border)', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
          {releaseWindow ? `${(releaseWindow.confidence_interval * 100).toFixed(0)}% CI` : 'Pending'}
        </span>
      </div>

      {releaseWindow ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', fontSize: '0.8rem' }}>
          <div style={{ backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)', padding: '0.5rem 0.6rem', borderRadius: '6px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem', display: 'block' }}>WINDOW START</span>
            <strong style={{ color: '#cbd5e1' }}>
              {new Date(releaseWindow.estimated_start_time).toUTCString().slice(17, 25)} UTC
            </strong>
          </div>

          <div style={{ backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)', padding: '0.5rem 0.6rem', borderRadius: '6px', border: '1px solid var(--glass-border)' }}>
            <span style={{ color: 'var(--accent-amber)', fontSize: '0.68rem', display: 'block', fontWeight: 600 }}>PEAK DISCHARGE</span>
            <strong style={{ color: 'var(--accent-amber)' }}>
              {new Date(releaseWindow.peak_probability_time).toUTCString().slice(17, 25)} UTC
            </strong>
          </div>

          <div style={{ backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)', padding: '0.5rem 0.6rem', borderRadius: '6px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem', display: 'block' }}>WINDOW END</span>
            <strong style={{ color: '#cbd5e1' }}>
              {new Date(releaseWindow.estimated_end_time).toUTCString().slice(17, 25)} UTC
            </strong>
          </div>
        </div>
      ) : (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', padding: '0.5rem 0' }}>
          Lagrangian release window calculation pending.
        </div>
      )}
    </div>
  );
};
