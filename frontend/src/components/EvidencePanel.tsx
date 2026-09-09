import React, { useState } from 'react';
import { AttributionScore, EvidenceItem, EvidenceCategory } from '../types';

interface Props {
  score?: AttributionScore;
}

export const EvidencePanel: React.FC<Props> = ({ score }) => {
  const [activeCategory, setActiveCategory] = useState<string>('ALL');

  if (!score) return null;

  const supporting = score.supporting_evidence || score.evidence_items.filter(e => e.category === 'SUPPORTING_EVIDENCE' || !e.category);
  const contradicting = score.contradicting_evidence || score.evidence_items.filter(e => e.category === 'CONTRADICTING_EVIDENCE');
  const exculpatory = score.exculpatory_evidence || score.evidence_items.filter(e => e.category === 'EXCULPATORY_EVIDENCE');
  const dataQuality = score.data_quality_items || score.evidence_items.filter(e => e.category === 'DATA_QUALITY');
  const uncertainty = score.uncertainty_items || score.evidence_items.filter(e => e.category === 'UNCERTAINTY');

  const filteredItems: EvidenceItem[] = (() => {
    switch (activeCategory) {
      case 'SUPPORTING':
        return supporting;
      case 'CONTRADICTING':
        return contradicting;
      case 'EXCULPATORY':
        return exculpatory;
      case 'DATA_QUALITY':
        return dataQuality;
      case 'UNCERTAINTY':
        return uncertainty;
      default:
        return score.evidence_items;
    }
  })();

  const getCategoryTheme = (category?: EvidenceCategory | string) => {
    switch (category) {
      case 'SUPPORTING_EVIDENCE':
        return { color: '#10b981', bg: '#064e3b25', border: '#10b981', label: 'SUPPORTING' };
      case 'CONTRADICTING_EVIDENCE':
        return { color: '#f59e0b', bg: '#78350f25', border: '#f59e0b', label: 'CONTRADICTING' };
      case 'EXCULPATORY_EVIDENCE':
        return { color: '#60a5fa', bg: '#1e3a8a25', border: '#3b82f6', label: 'EXCULPATORY' };
      case 'DATA_QUALITY':
        return { color: '#a855f7', bg: '#581c8725', border: '#a855f7', label: 'DATA QUALITY' };
      case 'UNCERTAINTY':
        return { color: '#94a3b8', bg: '#1e293b50', border: '#64748b', label: 'UNCERTAINTY' };
      default:
        return { color: '#38bdf8', bg: '#0c4a6e25', border: '#0284c7', label: 'EVIDENCE' };
    }
  };

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--glass-border)',
      borderRadius: '8px',
      padding: '1.25rem',
      marginBottom: '1rem',
    }}>
      <div style={{ marginBottom: '0.85rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc' }}>
            📑 Forensic Evidence & Attribution Dossier — {score.candidate_name}
          </h3>
          <span style={{
            fontSize: '0.70rem',
            fontWeight: 700,
            padding: '0.2rem 0.5rem',
            borderRadius: '4px',
            backgroundColor: score.risk_level === 'VERY_HIGH' ? '#ef444420' : '#10b98120',
            color: score.risk_level === 'VERY_HIGH' ? '#ef4444' : '#10b981',
            border: `1px solid ${score.risk_level === 'VERY_HIGH' ? '#ef4444' : '#10b981'}`,
          }}>
            RANK #{score.rank} • {score.total_score} / 100
          </span>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Transparent breakdown of supporting, contradicting, exculpatory, and telemetry data quality
        </span>
      </div>

      {/* Category Filter Pills */}
      <div style={{ display: 'flex', gap: '0.35rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {[
          { id: 'ALL', label: `All Evidence (${score.evidence_items.length})` },
          { id: 'SUPPORTING', label: `Supporting (${supporting.length})`, count: supporting.length, color: '#10b981' },
          { id: 'CONTRADICTING', label: `Contradicting (${contradicting.length})`, count: contradicting.length, color: '#f59e0b' },
          { id: 'EXCULPATORY', label: `Exculpatory (${exculpatory.length})`, count: exculpatory.length, color: '#60a5fa' },
          { id: 'DATA_QUALITY', label: `Data Quality (${dataQuality.length})`, count: dataQuality.length, color: '#a855f7' },
          { id: 'UNCERTAINTY', label: `Uncertainty (${uncertainty.length})`, count: uncertainty.length, color: '#94a3b8' },
        ].map((tab) => {
          const isActive = activeCategory === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveCategory(tab.id)}
              style={{
                fontSize: '0.72rem',
                fontWeight: isActive ? 700 : 500,
                padding: '0.25rem 0.6rem',
                borderRadius: '6px',
                border: `1px solid ${isActive ? '#38bdf8' : '#334155'}`,
                backgroundColor: isActive ? '#0369a130' : '#0f172a',
                color: isActive ? '#38bdf8' : '#94a3b8',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Evidence Cards List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {filteredItems.length === 0 ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: '#64748b', fontSize: '0.80rem' }}>
            No evidence records found in this category for this candidate.
          </div>
        ) : (
          filteredItems.map((ev: EvidenceItem) => {
            const theme = getCategoryTheme(ev.category);

            return (
              <div
                key={ev.id}
                style={{
                  backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                  borderLeft: `3px solid ${theme.border}`,
                  borderRadius: '0 6px 6px 0',
                  padding: '0.75rem 1rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                    <span style={{
                      fontSize: '0.65rem',
                      fontWeight: 700,
                      color: theme.color,
                      backgroundColor: theme.bg,
                      padding: '0.1rem 0.4rem',
                      borderRadius: '3px',
                      border: `1px solid ${theme.border}40`,
                    }}>
                      {theme.label}
                    </span>
                    <span style={{ fontSize: '0.70rem', color: '#94a3b8', fontWeight: 600 }}>
                      {ev.factor_category}
                    </span>
                  </div>

                  {ev.score_impact !== 0 ? (
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: ev.score_impact > 0 ? '#10b981' : '#f59e0b',
                      backgroundColor: '#0f172a',
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                    }}>
                      {ev.score_impact > 0 ? `+${ev.score_impact.toFixed(1)}` : ev.score_impact.toFixed(1)} pts
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.70rem', color: '#64748b', backgroundColor: '#0f172a', padding: '0.15rem 0.40rem', borderRadius: '4px' }}>
                      Informational
                    </span>
                  )}
                </div>

                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc', marginBottom: '0.25rem' }}>
                  {ev.title}
                </h4>

                <p style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: 1.45, marginBottom: '0.45rem' }}>
                  {ev.description}
                </p>

                {/* Structured Value Badges */}
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', fontSize: '0.70rem' }}>
                  {ev.calculated_value && (
                    <span style={{ backgroundColor: '#0f172a', color: '#38bdf8', padding: '0.15rem 0.45rem', borderRadius: '4px', border: '1px solid var(--glass-border)' }}>
                      <strong>Observed:</strong> {ev.calculated_value}
                    </span>
                  )}
                  {ev.threshold_used && (
                    <span style={{ backgroundColor: '#0f172a', color: '#f59e0b', padding: '0.15rem 0.45rem', borderRadius: '4px', border: '1px solid var(--glass-border)' }}>
                      <strong>Threshold:</strong> {ev.threshold_used}
                    </span>
                  )}
                  {ev.uncertainty && (
                    <span style={{ backgroundColor: '#0f172a', color: '#a855f7', padding: '0.15rem 0.45rem', borderRadius: '4px', border: '1px solid var(--glass-border)' }}>
                      <strong>Uncertainty:</strong> {ev.uncertainty}
                    </span>
                  )}
                  {ev.source && (
                    <span style={{ backgroundColor: '#0f172a', color: '#94a3b8', padding: '0.15rem 0.45rem', borderRadius: '4px', border: '1px solid var(--glass-border)' }}>
                      <strong>Source:</strong> {ev.source}
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
