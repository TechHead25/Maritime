import React from 'react';
import { AttributionScore } from '../types';

interface Props {
  scores: AttributionScore[];
  selectedScoreId?: string;
  onSelectScore: (score: AttributionScore) => void;
}

export const CandidateRanking: React.FC<Props> = ({
  scores,
  selectedScoreId,
  onSelectScore,
}) => {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'VERY_HIGH':
        return { bg: '#ef444425', border: '#ef4444', text: '#ef4444' };
      case 'HIGH':
        return { bg: '#f9731625', border: '#f97316', text: '#f97316' };
      case 'MEDIUM':
        return { bg: '#eab30825', border: '#eab308', text: '#eab308' };
      case 'LOW':
        return { bg: '#10b98125', border: '#10b981', text: '#10b981' };
      default:
        return { bg: '#64748b25', border: '#64748b', text: '#94a3b8' };
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#f8fafc' }}>
            🏆 Ranked Candidate Vessels
          </h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Attribution Confidence Score & Decision Support Ranking (0–100 pts)
          </span>
        </div>
      </div>

      <div style={{
        fontSize: '0.72rem',
        color: '#cbd5e1',
        backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
        padding: '0.45rem 0.75rem',
        borderRadius: '6px',
        marginBottom: '0.85rem',
        borderLeft: '3px solid var(--accent-cyan)',
      }}>
        ℹ <strong>Investigative Ranking Notice:</strong> Scores reflect probabilistic forensic correlation based on available evidence and do not constitute an automated legal accusation.
      </div>

      {scores.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          No candidate attribution scores available. Execute the forensic pipeline to calculate rankings.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {scores.map((s) => {
            const isSelected = selectedScoreId === s.id;
            const risk = getRiskColor(s.risk_level);

            return (
              <div
                key={s.id}
                onClick={() => onSelectScore(s)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  backgroundColor: isSelected ? '#1e293b' : 'rgba(30, 41, 59, 0.5)',
                  border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid #334155',
                  borderRadius: '6px',
                  padding: '0.75rem 1rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  {/* Rank Badge */}
                  <span style={{
                    fontSize: '0.9rem',
                    fontWeight: 700,
                    color: s.rank === 1 ? '#f59e0b' : '#94a3b8',
                    minWidth: '28px',
                  }}>
                    #{s.rank}
                  </span>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <strong style={{ fontSize: '0.9rem', color: '#f8fafc' }}>{s.candidate_name}</strong>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>MMSI: {s.mmsi}</span>
                    </div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)' }}>{s.vessel_type}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                  {/* Score */}
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Attribution Score</div>
                    <span style={{ fontSize: '1.1rem', fontWeight: 700, color: s.rank === 1 ? '#f59e0b' : '#f8fafc' }}>
                      {s.total_score.toFixed(1)}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}> / 100</span>
                  </div>

                  {/* Risk Badge */}
                  <span style={{
                    backgroundColor: risk.bg,
                    border: `1px solid ${risk.border}`,
                    color: risk.text,
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    minWidth: '70px',
                    textAlign: 'center',
                  }}>
                    {s.risk_level}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
