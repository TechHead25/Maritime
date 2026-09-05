import React from 'react';
import { AttributionScore } from '../types';

interface AttributionLeaderboardProps {
  scores: AttributionScore[];
  onSelectCandidate: (score: AttributionScore) => void;
}

export const AttributionLeaderboard: React.FC<AttributionLeaderboardProps> = ({ scores, onSelectCandidate }) => {
  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      borderRadius: '12px',
      border: '1px solid var(--border)',
      padding: '1.5rem'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: '700' }}>Candidate Vessel Attribution Ranking</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Ranked by multi-factor spatiotemporal proximity, trajectory alignment, and AIS behavior
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {scores.map((item) => {
          const isHighRisk = item.risk_level === 'VERY_HIGH' || item.risk_level === 'HIGH';
          return (
            <div
              key={item.id}
              onClick={() => onSelectCandidate(item)}
              style={{
                backgroundColor: 'var(--bg-card)',
                padding: '1rem',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                transition: 'border-color 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-cyan)')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border)')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  backgroundColor: item.rank === 1 ? '#ef444425' : '#334155',
                  color: item.rank === 1 ? '#ef4444' : '#94a3b8',
                  border: `2px solid ${item.rank === 1 ? '#ef4444' : '#475569'}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: '700',
                  fontSize: '0.9rem'
                }}>
                  #{item.rank}
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: '700', fontSize: '1rem' }}>{item.candidate_name}</span>
                    <span style={{
                      fontSize: '0.7rem',
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      backgroundColor: isHighRisk ? '#ef444420' : '#10b98120',
                      color: isHighRisk ? '#ef4444' : '#10b981',
                      border: `1px solid ${isHighRisk ? '#ef4444' : '#10b981'}`
                    }}>
                      {item.risk_level} RISK
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    MMSI: {item.mmsi} • Type: {item.vessel_type} • Evidence Items: {item.evidence_items.length}
                  </div>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.25rem', fontWeight: '800', color: isHighRisk ? '#ef4444' : 'var(--text-main)' }}>
                  {item.total_score}
                  <span style={{ fontSize: '0.75rem', fontWeight: '400', color: 'var(--text-muted)' }}>/100</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', marginTop: '0.2rem' }}>
                  View Evidence Dossier →
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
