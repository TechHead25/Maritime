import React from 'react';

interface Props {
  uncertaintyRadiusKm?: number;
  confidenceInterval?: number;
}

export const UncertaintyPanel: React.FC<Props> = ({
  uncertaintyRadiusKm = 1.08,
  confidenceInterval = 0.90,
}) => {
  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--glass-border)',
      borderRadius: '8px',
      padding: '1.25rem',
      marginBottom: '1rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '1rem' }}>🛡</span>
        <h3 style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
          Uncertainty & Decision Support Notice
        </h3>
      </div>

      <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '0.75rem' }}>
        This platform provides <strong>investigative decision support intelligence</strong>.
        Estimated spill origins, drift paths, and attribution scores represent probabilistic evidence models and do <strong>not</strong> constitute an automated legal conclusion or accusation of liability.
      </p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.25rem', fontSize: '0.75rem', color: '#cbd5e1', backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)', padding: '0.6rem 0.75rem', borderRadius: '6px' }}>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Origin Uncertainty: </span>
          <strong style={{ color: 'var(--accent-cyan)' }}>±{uncertaintyRadiusKm.toFixed(2)} km (95% CI)</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Release Window Confidence: </span>
          <strong style={{ color: '#10b981' }}>{(confidenceInterval * 100).toFixed(0)}% Statistical Bound</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Wind Leeway Ratio: </span>
          <strong style={{ color: '#f59e0b' }}>3.0% (α = 0.03)</strong>
        </div>
      </div>
    </div>
  );
};
