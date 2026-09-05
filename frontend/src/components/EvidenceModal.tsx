import React, { useState } from 'react';
import { AttributionScore, EvidenceItem, EvidenceCategory } from '../types';

interface EvidenceModalProps {
  score: AttributionScore | null;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({ score, onClose }) => {
  const [activeTab, setActiveTab] = useState<string>('ALL');

  if (!score) return null;

  const supporting = score.supporting_evidence || score.evidence_items.filter(e => e.category === 'SUPPORTING_EVIDENCE' || !e.category);
  const contradicting = score.contradicting_evidence || score.evidence_items.filter(e => e.category === 'CONTRADICTING_EVIDENCE');
  const exculpatory = score.exculpatory_evidence || score.evidence_items.filter(e => e.category === 'EXCULPATORY_EVIDENCE');
  const dataQuality = score.data_quality_items || score.evidence_items.filter(e => e.category === 'DATA_QUALITY');
  const uncertainty = score.uncertainty_items || score.evidence_items.filter(e => e.category === 'UNCERTAINTY');

  const filteredItems: EvidenceItem[] = (() => {
    switch (activeTab) {
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
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.80)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem'
    }} onClick={onClose}>
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: '12px',
        border: '1px solid #334155',
        maxWidth: '720px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        padding: '1.5rem',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)'
      }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: '700',
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              backgroundColor: score.risk_level === 'VERY_HIGH' ? '#ef444420' : '#10b98120',
              color: score.risk_level === 'VERY_HIGH' ? '#ef4444' : '#10b981',
              border: `1px solid ${score.risk_level === 'VERY_HIGH' ? '#ef4444' : '#10b981'}`
            }}>
              RANK #{score.rank} • {score.risk_level} RISK
            </span>
            <h3 style={{ fontSize: '1.3rem', fontWeight: '700', marginTop: '0.4rem', color: '#f8fafc' }}>{score.candidate_name}</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>MMSI: {score.mmsi} • Vessel Type: {score.vessel_type}</p>
          </div>
          <button onClick={onClose} style={{
            background: 'transparent',
            color: 'var(--text-muted)',
            fontSize: '1.5rem',
            padding: '0.25rem 0.5rem',
            cursor: 'pointer',
            border: 'none',
          }}>✕</button>
        </div>

        {/* Score Breakdown Bars */}
        <div style={{
          backgroundColor: '#0f172a',
          padding: '1rem',
          borderRadius: '8px',
          border: '1px solid #1e293b',
          marginBottom: '1.25rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontWeight: '600', fontSize: '0.9rem', color: '#f8fafc' }}>Composite Attribution Rating</span>
            <span style={{ fontWeight: '700', fontSize: '1.1rem', color: '#38bdf8' }}>
              {score.total_score} / 100
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem', fontSize: '0.8rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px', color: '#cbd5e1' }}>
                <span>Spatiotemporal Proximity (Max 40)</span>
                <span>{score.sub_scores.proximity_score} pts</span>
              </div>
              <div style={{ background: '#334155', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ background: '#38bdf8', width: `${(score.sub_scores.proximity_score / 40) * 100}%`, height: '100%' }} />
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px', color: '#cbd5e1' }}>
                <span>Timing Alignment (Max 25)</span>
                <span>{score.sub_scores.trajectory_alignment_score} pts</span>
              </div>
              <div style={{ background: '#334155', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ background: '#818cf8', width: `${(score.sub_scores.trajectory_alignment_score / 25) * 100}%`, height: '100%' }} />
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px', color: '#cbd5e1' }}>
                <span>Navigational Anomaly (Max 15)</span>
                <span>{score.sub_scores.navigational_anomaly_score} pts</span>
              </div>
              <div style={{ background: '#334155', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ background: '#a855f7', width: `${(score.sub_scores.navigational_anomaly_score / 15) * 100}%`, height: '100%' }} />
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px', color: '#cbd5e1' }}>
                <span>AIS Integrity Penalty (Max 10)</span>
                <span>{score.sub_scores.ais_integrity_penalty} pts</span>
              </div>
              <div style={{ background: '#334155', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ background: '#ef4444', width: `${(score.sub_scores.ais_integrity_penalty / 10) * 100}%`, height: '100%' }} />
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px', color: '#cbd5e1' }}>
                <span>Vessel Type Risk (Max 10)</span>
                <span>{score.sub_scores.vessel_type_risk_score} pts</span>
              </div>
              <div style={{ background: '#334155', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ background: '#10b981', width: `${(score.sub_scores.vessel_type_risk_score / 10) * 100}%`, height: '100%' }} />
              </div>
            </div>
          </div>
        </div>

        {/* Evidence Category Filter Tabs */}
        <div style={{ display: 'flex', gap: '0.35rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          {[
            { id: 'ALL', label: `All (${score.evidence_items.length})` },
            { id: 'SUPPORTING', label: `Supporting (${supporting.length})` },
            { id: 'CONTRADICTING', label: `Contradicting (${contradicting.length})` },
            { id: 'EXCULPATORY', label: `Exculpatory (${exculpatory.length})` },
            { id: 'DATA_QUALITY', label: `Data Quality (${dataQuality.length})` },
            { id: 'UNCERTAINTY', label: `Uncertainty (${uncertainty.length})` },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  fontSize: '0.72rem',
                  fontWeight: isActive ? 700 : 500,
                  padding: '0.25rem 0.6rem',
                  borderRadius: '6px',
                  border: `1px solid ${isActive ? '#38bdf8' : '#334155'}`,
                  backgroundColor: isActive ? '#0369a130' : '#0f172a',
                  color: isActive ? '#38bdf8' : '#94a3b8',
                  cursor: 'pointer',
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Itemized Evidence Chain */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {filteredItems.map((item) => {
            const theme = getCategoryTheme(item.category);
            return (
              <div key={item.id} style={{
                backgroundColor: '#0f172a',
                padding: '0.85rem',
                borderRadius: '8px',
                border: '1px solid #1e293b',
                borderLeft: `4px solid ${theme.border}`
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
                    <span style={{ fontWeight: '600', fontSize: '0.85rem', color: '#f8fafc' }}>{item.title}</span>
                  </div>
                  {item.score_impact !== 0 ? (
                    <span style={{ fontSize: '0.75rem', color: item.score_impact > 0 ? '#10b981' : '#f59e0b', fontWeight: '700' }}>
                      {item.score_impact > 0 ? `+${item.score_impact.toFixed(1)}` : item.score_impact.toFixed(1)} pts
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.70rem', color: '#64748b' }}>Informational</span>
                  )}
                </div>
                <p style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '0.35rem', lineHeight: 1.45 }}>
                  {item.description}
                </p>
                {/* Structured badges */}
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.4rem', fontSize: '0.68rem' }}>
                  {item.calculated_value && (
                    <span style={{ backgroundColor: '#1e293b', color: '#38bdf8', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                      <strong>Observed:</strong> {item.calculated_value}
                    </span>
                  )}
                  {item.threshold_used && (
                    <span style={{ backgroundColor: '#1e293b', color: '#f59e0b', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                      <strong>Threshold:</strong> {item.threshold_used}
                    </span>
                  )}
                  {item.uncertainty && (
                    <span style={{ backgroundColor: '#1e293b', color: '#a855f7', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                      <strong>Uncertainty:</strong> {item.uncertainty}
                    </span>
                  )}
                  {item.source && (
                    <span style={{ backgroundColor: '#1e293b', color: '#94a3b8', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                      <strong>Source:</strong> {item.source}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
