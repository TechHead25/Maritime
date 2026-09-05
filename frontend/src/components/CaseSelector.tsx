import React from 'react';
import { InvestigationCase } from '../types';

interface Props {
  cases: InvestigationCase[];
  selectedCaseId: string;
  onSelectCase: (caseId: string) => void;
  isLoading?: boolean;
  onOpenNewCaseModal?: () => void;
}

export const CaseSelector: React.FC<Props> = ({
  cases,
  selectedCaseId,
  onSelectCase,
  isLoading,
  onOpenNewCaseModal,
}) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Active Case:
      </span>
      <select
        value={selectedCaseId}
        onChange={(e) => onSelectCase(e.target.value)}
        disabled={isLoading}
        style={{
          backgroundColor: '#0f172a',
          color: '#f8fafc',
          border: '1px solid #334155',
          padding: '0.35rem 0.75rem',
          borderRadius: '6px',
          fontSize: '0.85rem',
          fontWeight: 500,
          outline: 'none',
          cursor: 'pointer',
        }}
      >
        {cases.map((c) => (
          <option key={c.id} value={c.id}>
            {c.title} [{c.status}]
          </option>
        ))}
      </select>

      {onOpenNewCaseModal && (
        <button
          onClick={onOpenNewCaseModal}
          style={{
            backgroundColor: '#0284c7',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            padding: '0.35rem 0.75rem',
            fontSize: '0.80rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            boxShadow: '0 2px 4px rgba(2, 132, 199, 0.3)',
          }}
        >
          <span>➕</span>
          <span>New Investigation</span>
        </button>
      )}
    </div>
  );
};
