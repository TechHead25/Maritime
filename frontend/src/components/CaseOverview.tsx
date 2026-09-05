import React from 'react';
import { CaseDetails } from '../types';

interface CaseOverviewProps {
  details: CaseDetails;
  onRunPipeline: () => void;
  isRunningPipeline: boolean;
}

export const CaseOverview: React.FC<CaseOverviewProps> = ({ details, onRunPipeline, isRunningPipeline }) => {
  const { case: investigationCase, slicks, release_windows, candidates } = details;
  const primarySlick = slicks[0];
  const primaryRelease = release_windows[0];

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      borderRadius: '12px',
      border: '1px solid var(--border)',
      padding: '1.5rem',
      marginBottom: '1.5rem'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.25rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <span style={{
              backgroundColor: '#3b82f620',
              color: 'var(--accent-cyan)',
              border: '1px solid #3b82f640',
              padding: '0.2rem 0.6rem',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: '600'
            }}>
              CASE ID: {investigationCase.id}
            </span>
            <span style={{
              backgroundColor: '#10b98120',
              color: '#10b981',
              border: '1px solid #10b98140',
              padding: '0.2rem 0.6rem',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: '600'
            }}>
              STATUS: {investigationCase.status}
            </span>
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: '700' }}>{investigationCase.title}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
            {investigationCase.metadata?.notes || 'Historical maritime investigation case'}
          </p>
        </div>

        <button
          onClick={onRunPipeline}
          disabled={isRunningPipeline}
          style={{
            backgroundColor: 'var(--accent-blue)',
            color: '#fff',
            padding: '0.65rem 1.25rem',
            fontSize: '0.9rem',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)'
          }}
        >
          {isRunningPipeline ? '⏳ Executing Pipeline...' : '⚡ Re-Run Investigation Pipeline'}
        </button>
      </div>

      {/* Metrics Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem'
      }}>
        <div style={{
          backgroundColor: 'var(--bg-card)',
          padding: '1rem',
          borderRadius: '8px',
          border: '1px solid var(--border)'
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DETECTED SLICK AREA</div>
          <div style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--accent-cyan)', marginTop: '0.25rem' }}>
            {primarySlick ? `${primarySlick.area_sq_km} km²` : 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Confidence: {primarySlick ? `${Math.round(primarySlick.confidence_score * 100)}%` : 'N/A'}
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-card)',
          padding: '1rem',
          borderRadius: '8px',
          border: '1px solid var(--border)'
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ESTIMATED RELEASE WINDOW</div>
          <div style={{ fontSize: '1.05rem', fontWeight: '700', color: '#fff', marginTop: '0.25rem' }}>
            {primaryRelease ? new Date(primaryRelease.peak_probability_time).toUTCString().slice(5, 22) : 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Interval: 4-Hour Dispersion Band
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-card)',
          padding: '1rem',
          borderRadius: '8px',
          border: '1px solid var(--border)'
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>INTERCEPTED AIS VESSELS</div>
          <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#f59e0b', marginTop: '0.25rem' }}>
            {candidates.length} Vessels Flagged
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Within Origin Probability Cloud
          </div>
        </div>
      </div>
    </div>
  );
};
