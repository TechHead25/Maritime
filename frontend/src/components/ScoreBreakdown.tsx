import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { AttributionScore } from '../types';

interface Props {
  score?: AttributionScore;
}

export const ScoreBreakdown: React.FC<Props> = ({ score }) => {
  if (!score) return null;

  const subs = score.sub_scores;

  const data = [
    { factor: 'Proximity (40%)', score: subs.proximity_score, max: 40, color: '#38bdf8' },
    { factor: 'Timing (25%)', score: subs.trajectory_alignment_score, max: 25, color: '#f59e0b' },
    { factor: 'Behaviour (15%)', score: subs.navigational_anomaly_score, max: 15, color: '#a855f7' },
    { factor: 'AIS Gap (10%)', score: subs.ais_integrity_penalty, max: 10, color: '#ef4444' },
    { factor: 'Vessel Type (10%)', score: subs.vessel_type_risk_score, max: 10, color: '#10b981' },
  ];

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid #1e293b',
      borderRadius: '8px',
      padding: '1.25rem',
      marginBottom: '1rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc' }}>
            📊 Attribution Factor Breakdown — {score.candidate_name}
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Individual points contribution across 5 forensic pillars (Total: {score.total_score.toFixed(1)} / 100)
          </span>
        </div>
      </div>

      <div style={{ height: '200px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 70, bottom: 5 }}
          >
            <XAxis type="number" domain={[0, 40]} stroke="#64748b" fontSize={11} />
            <YAxis
              type="category"
              dataKey="factor"
              stroke="#cbd5e1"
              fontSize={11}
              width={100}
            />
            <Tooltip
              formatter={(value: any, _name: any, props: any) => [`${value} / ${props?.payload?.max ?? 40} pts`, 'Score Contribution']}
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc', fontSize: '0.8rem' }}
            />
            <Bar dataKey="score" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
