import React, { useState } from 'react';
import { InvestigationCase, SARScene, SlickDetection } from '../types';

interface Props {
  caseItem: InvestigationCase;
  sarScene?: SARScene;
  slick?: SlickDetection;
  onRunInvestigation: () => void;
  isRunningPipeline: boolean;
}

export const CaseHeader: React.FC<Props> = ({
  caseItem,
  sarScene,
  slick,
  onRunInvestigation,
  isRunningPipeline,
}) => {
  const isSynthetic = caseItem.metadata?.synthetic ?? true;
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ATTRIBUTION_COMPLETED':
        return { bg: '#04785720', border: '#059669', color: '#10b981', label: 'ATTRIBUTION COMPLETED' };
      case 'DRIFT_SIMULATED':
        return { bg: '#0284c720', border: '#0284c7', color: '#38bdf8', label: 'DRIFT RECONSTRUCTED' };
      default:
        return { bg: '#33415540', border: '#475569', color: '#94a3b8', label: status };
    }
  };

  const handleDownloadPdf = async () => {
    try {
      setIsDownloadingPdf(true);
      const url = `http://localhost:8000/api/cases/${caseItem.id}/report/pdf`;
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Maritime_Oil_Investigation_Report_${caseItem.id}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (e) {
      console.error('Failed to trigger PDF download:', e);
      alert('Failed to download PDF report. Ensure backend server is running.');
    } finally {
      setTimeout(() => setIsDownloadingPdf(false), 2000);
    }
  };

  const badge = getStatusBadge(caseItem.status);

  return (
    <div style={{
      backgroundColor: '#0f172a',
      border: '1px solid #1e293b',
      borderRadius: '8px',
      padding: '1.25rem 1.5rem',
      marginBottom: '1rem',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)',
    }}>
      {/* Telemetry Provenance Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            backgroundColor: isSynthetic ? '#f59e0b15' : '#10b98115',
            border: `1px solid ${isSynthetic ? '#f59e0b' : '#10b981'}`,
            color: isSynthetic ? '#f59e0b' : '#10b981',
            fontSize: '0.70rem',
            fontWeight: 700,
            padding: '0.15rem 0.55rem',
            borderRadius: '4px',
            letterSpacing: '0.04em',
          }}>
            {isSynthetic ? '⚠️ SYNTHETIC BENCHMARK DATASET' : '🛰️ HISTORICAL SENSOR DATASET'}
          </span>

          <span style={{
            fontSize: '0.70rem',
            color: '#64748b',
          }}>
            Case ID: <code style={{ color: '#94a3b8' }}>{caseItem.id}</code>
          </span>
        </div>

        <span style={{
          backgroundColor: badge.bg,
          border: `1px solid ${badge.border}`,
          color: badge.color,
          fontSize: '0.70rem',
          fontWeight: 700,
          padding: '0.15rem 0.55rem',
          borderRadius: '9999px',
          letterSpacing: '0.03em',
        }}>
          {badge.label}
        </span>
      </div>

      {/* Main Title & Action Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.35rem', letterSpacing: '-0.01em' }}>
            {caseItem.title}
          </h1>

          <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.80rem', color: '#94a3b8' }}>
            <span><strong>Incident Scope:</strong> {caseItem.metadata?.incident_location || 'Bay of Bengal / Sri Lanka'}</span>
            <span><strong>SAR Platform:</strong> {sarScene ? `${sarScene.satellite_platform} (${sarScene.sensor_mode} ${sarScene.polarization})` : 'Sentinel-1A'}</span>
            <span><strong>Detected Surface:</strong> {slick ? `${slick.area_sq_km.toFixed(2)} km²` : 'N/A'}</span>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <button
            onClick={handleDownloadPdf}
            disabled={isDownloadingPdf}
            style={{
              backgroundColor: '#1e293b',
              color: '#f8fafc',
              border: '1px solid #334155',
              padding: '0.60rem 1.0rem',
              borderRadius: '6px',
              fontSize: '0.82rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              cursor: 'pointer',
              transition: 'background-color 0.15s ease',
            }}
            title="Download official PDF forensic intelligence dossier"
          >
            {isDownloadingPdf ? '📄 Compiling PDF...' : '📥 Export Report (PDF)'}
          </button>

          <button
            onClick={onRunInvestigation}
            disabled={isRunningPipeline}
            style={{
              backgroundColor: isRunningPipeline ? '#334155' : '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              padding: '0.60rem 1.15rem',
              fontSize: '0.82rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              cursor: isRunningPipeline ? 'not-allowed' : 'pointer',
              boxShadow: '0 4px 12px rgba(2, 132, 199, 0.35)',
            }}
          >
            {isRunningPipeline ? '⏳ Executing Pipeline...' : '⚡ Run Forensic Pipeline'}
          </button>
        </div>
      </div>
    </div>
  );
};
