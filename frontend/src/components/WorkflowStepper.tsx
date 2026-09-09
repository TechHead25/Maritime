import React from 'react';
import { CaseStatus } from '../types';

interface Props {
  status: CaseStatus;
  isRunning: boolean;
  onStartPipeline: () => void;
}

export const WorkflowStepper: React.FC<Props> = ({
  status,
  isRunning,
  onStartPipeline,
}) => {
  const steps = [
    {
      num: 1,
      title: 'SAR Detection',
      desc: 'Oil slick perimeter & centroid extraction',
      completed: status !== 'CREATED',
    },
    {
      num: 2,
      title: 'Backward Drift',
      desc: 'Reverse ocean & wind Lagrangian advection',
      completed: status === 'DRIFT_SIMULATED' || status === 'ATTRIBUTION_COMPLETED',
    },
    {
      num: 3,
      title: 'AIS Interception',
      desc: 'Trajectory interpolation & dark gap analysis',
      completed: status === 'ATTRIBUTION_COMPLETED',
    },
    {
      num: 4,
      title: 'Attribution Scoring',
      desc: '5-factor explainable liability ranking',
      completed: status === 'ATTRIBUTION_COMPLETED',
    },
  ];

  const isCompleted = status === 'ATTRIBUTION_COMPLETED';

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--glass-border)',
      borderRadius: '8px',
      padding: '1.25rem 1.5rem',
      marginBottom: '1rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#f8fafc' }}>
            🔍 Forensic Investigation Workflow
          </h2>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Follow the 4-stage forensic data flow from satellite observation back to candidate vessel ranking.
          </p>
        </div>

        {!isCompleted && (
          <button
            onClick={onStartPipeline}
            disabled={isRunning}
            style={{
              backgroundColor: isRunning ? '#334155' : 'var(--accent-blue)',
              color: '#ffffff',
              padding: '0.6rem 1.25rem',
              fontSize: '0.85rem',
              fontWeight: 600,
              borderRadius: '6px',
              boxShadow: '0 4px 12px rgba(2, 132, 199, 0.3)',
            }}
          >
            {isRunning ? '⏳ Running Analysis...' : '⚡ Start Investigation'}
          </button>
        )}
      </div>

      {/* 4 Step Boxes */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '0.75rem',
      }}>
        {steps.map((step) => {
          const isActive = isRunning && !step.completed;

          return (
            <div
              key={step.num}
              style={{
                backgroundColor: step.completed ? 'rgba(16, 185, 129, 0.08)' : isActive ? 'rgba(56, 189, 248, 0.08)' : '#1e293b',
                border: `1px solid ${step.completed ? '#10b98140' : isActive ? 'var(--accent-cyan)' : '#334155'}`,
                borderRadius: '6px',
                padding: '0.75rem 0.9rem',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
              }}
            >
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: step.completed ? '#10b981' : isActive ? 'var(--accent-cyan)' : '#334155',
                color: step.completed || isActive ? '#090e17' : '#94a3b8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: 800,
                flexShrink: 0,
              }}>
                {step.completed ? '✓' : step.num}
              </div>

              <div>
                <strong style={{ fontSize: '0.82rem', color: step.completed ? '#10b981' : '#f8fafc', display: 'block' }}>
                  {step.title}
                </strong>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.35 }}>
                  {step.desc}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
