import React from 'react';
import {
  Shield,
  Play,
  Download,
  Plus,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Compass,
  GitCompare,
} from 'lucide-react';
import { InvestigationCase, CaseStatus } from '../types';

interface Props {
  caseItem: InvestigationCase;
  cases: InvestigationCase[];
  onSelectCase: (caseId: string) => void;
  onOpenNewModal: () => void;
  readinessStatus?: 'READY' | 'PARTIAL' | 'UNAVAILABLE';
  lastAnalysisTime?: string;
  isRunningPipeline: boolean;
  onRunAnalysis: () => void;
  onExportReport: () => void;
  isDownloadingReport?: boolean;
  canCompare?: boolean;
  onOpenCompare?: () => void;
  isSurveillanceScanning?: boolean;
  onTriggerSurveillanceScan?: () => void;
  surveillanceAlertsCount?: number;
}

export const ConsoleHeader: React.FC<Props> = ({
  caseItem,
  cases,
  onSelectCase,
  onOpenNewModal,
  readinessStatus = 'READY',
  lastAnalysisTime,
  isRunningPipeline,
  onRunAnalysis,
  onExportReport,
  isDownloadingReport = false,
  canCompare = false,
  onOpenCompare,
  isSurveillanceScanning = false,
  onTriggerSurveillanceScan,
  surveillanceAlertsCount = 0,
}) => {
  const getStatusBadge = (status: CaseStatus) => {
    switch (status) {
      case 'ATTRIBUTION_COMPLETED':
        return { bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981', color: '#34d399', label: 'ATTRIBUTION VERIFIED' };
      case 'DRIFT_SIMULATED':
        return { bg: 'rgba(2, 132, 199, 0.15)', border: '#0284c7', color: '#38bdf8', label: 'DRIFT RECONSTRUCTED' };
      case 'AIS_INTERCEPTED':
        return { bg: 'rgba(168, 85, 247, 0.15)', border: '#a855f7', color: '#c084fc', label: 'VESSELS CORRELATED' };
      default:
        return { bg: 'rgba(100, 116, 139, 0.15)', border: '#64748b', color: '#94a3b8', label: status };
    }
  };

  const getReadinessBadge = (r: 'READY' | 'PARTIAL' | 'UNAVAILABLE') => {
    switch (r) {
      case 'READY':
        return { bg: 'rgba(16, 185, 129, 0.12)', border: '#10b981', color: '#34d399', icon: <CheckCircle2 size={12} /> };
      case 'PARTIAL':
        return { bg: 'rgba(245, 158, 11, 0.12)', border: '#f59e0b', color: '#fbbf24', icon: <AlertTriangle size={12} /> };
      default:
        return { bg: 'rgba(239, 68, 68, 0.12)', border: '#ef4444', color: '#f87171', icon: <XCircle size={12} /> };
    }
  };

  const statusStyle = getStatusBadge(caseItem.status);
  const readinessStyle = getReadinessBadge(readinessStatus);

  const getAreaCoordinates = () => {
    if (caseItem.region_of_interest?.coordinates?.[0]) {
      const coords = caseItem.region_of_interest.coordinates[0];
      const lons = coords.map((c) => c[0]);
      const lats = coords.map((c) => c[1]);
      const minLon = Math.min(...lons).toFixed(2);
      const maxLon = Math.max(...lons).toFixed(2);
      const minLat = Math.min(...lats).toFixed(2);
      const maxLat = Math.max(...lats).toFixed(2);
      return `${minLat}°N–${maxLat}°N, ${minLon}°E–${maxLon}°E`;
    }
    return 'AOI Coordinates Configured';
  };

  const incidentTimestamp = caseItem.metadata?.incident_timestamp_utc || caseItem.created_at;
  const formattedIncidentTime = incidentTimestamp
    ? new Date(incidentTimestamp).toISOString().replace('T', ' ').slice(0, 16) + ' UTC'
    : 'Unknown UTC';

  const formattedAnalysisTime = lastAnalysisTime
    ? new Date(lastAnalysisTime).toISOString().replace('T', ' ').slice(0, 16) + ' UTC'
    : 'Not yet executed';

  return (
    <header style={{
      backgroundColor: '#0c1322',
      border: '1px solid #1e293b',
      borderRadius: '8px',
      padding: '0.85rem 1.25rem',
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '1rem',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)',
    }}>
      {/* Left: Investigation Selector & Incident Metadata */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: '6px',
            backgroundColor: 'rgba(2, 132, 199, 0.15)',
            border: '1px solid #0284c7',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#38bdf8',
          }}>
            <Shield size={18} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <select
                value={caseItem.id}
                onChange={(e) => onSelectCase(e.target.value)}
                style={{
                  backgroundColor: '#131b2e',
                  border: '1px solid #334155',
                  color: '#f8fafc',
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  padding: '0.25rem 0.5rem',
                  borderRadius: '4px',
                  outline: 'none',
                  cursor: 'pointer',
                  maxWidth: '320px',
                }}
              >
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title}
                  </option>
                ))}
              </select>

              {/* Status Badge */}
              <span style={{
                backgroundColor: statusStyle.bg,
                border: `1px solid ${statusStyle.border}`,
                color: statusStyle.color,
                fontSize: '0.65rem',
                fontWeight: 700,
                padding: '0.15rem 0.5rem',
                borderRadius: '4px',
                letterSpacing: '0.03em',
              }}>
                {statusStyle.label}
              </span>
            </div>

            {/* Subline: Metadata Strip */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem', fontSize: '0.70rem', color: '#94a3b8', marginTop: '0.25rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <Clock size={11} color="#64748b" />
                <span>Incident: <strong style={{ color: '#cbd5e1' }}>{formattedIncidentTime}</strong></span>
              </span>

              <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <Compass size={11} color="#64748b" />
                <span>Area: <strong style={{ color: '#cbd5e1' }}>{getAreaCoordinates()}</strong></span>
              </span>

              <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  backgroundColor: readinessStyle.bg,
                  border: `1px solid ${readinessStyle.border}`,
                  color: readinessStyle.color,
                  padding: '0.1rem 0.4rem',
                  borderRadius: '3px',
                  fontWeight: 700,
                  fontSize: '0.62rem',
                }}>
                  {readinessStyle.icon} READINESS: {readinessStatus}
                </span>
              </span>

              <span>
                Last Analysis: <strong style={{ color: '#cbd5e1' }}>{formattedAnalysisTime}</strong>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Right: Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
        {onTriggerSurveillanceScan && (
          <button
            onClick={onTriggerSurveillanceScan}
            disabled={isSurveillanceScanning}
            style={{
              backgroundColor: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.35)',
              color: '#38bdf8',
              padding: '0.42rem 0.85rem',
              borderRadius: '5px',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: isSurveillanceScanning ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              transition: 'all 0.15s ease',
            }}
            title="Scan satellite radar footprints across high-risk sectors for automated spill anomalies"
          >
            <RefreshCw size={13} className={isSurveillanceScanning ? 'spin-icon' : ''} />
            {isSurveillanceScanning ? 'Sweeping Satellites...' : 'Sweep Satellites'}
            {surveillanceAlertsCount > 0 && (
              <span style={{
                backgroundColor: '#ef4444',
                color: '#ffffff',
                borderRadius: '10px',
                padding: '0.05rem 0.35rem',
                fontSize: '0.65rem',
                fontWeight: 700,
                marginLeft: '0.2rem',
              }}>
                {surveillanceAlertsCount}
              </span>
            )}
          </button>
        )}

        {canCompare && onOpenCompare && (
          <button
            onClick={onOpenCompare}
            style={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              color: '#cbd5e1',
              padding: '0.42rem 0.85rem',
              borderRadius: '5px',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              transition: 'all 0.15s ease',
            }}
            title="Compare two historical runs"
          >
            <GitCompare size={14} /> Compare Runs
          </button>
        )}

        <button
          onClick={onOpenNewModal}
          style={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            color: '#cbd5e1',
            padding: '0.42rem 0.85rem',
            borderRadius: '5px',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            transition: 'all 0.15s ease',
          }}
          title="Create a new historical investigation"
        >
          <Plus size={14} /> New Incident
        </button>

        <button
          onClick={onExportReport}
          disabled={isDownloadingReport}
          style={{
            backgroundColor: '#1e293b',
            border: '1px solid #0284c7',
            color: '#38bdf8',
            padding: '0.42rem 0.95rem',
            borderRadius: '5px',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: isDownloadingReport ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.15s ease',
          }}
          title="Download verified forensic report dossier based on current analysis"
        >
          {isDownloadingReport ? <RefreshCw size={13} className="spin-icon" /> : <Download size={13} />}
          {isDownloadingReport ? 'Generating Dossier...' : 'Export Report'}
        </button>

        <button
          onClick={onRunAnalysis}
          disabled={isRunningPipeline}
          style={{
            backgroundColor: isRunningPipeline ? '#475569' : '#0284c7',
            border: 'none',
            color: '#ffffff',
            padding: '0.42rem 1.15rem',
            borderRadius: '5px',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: isRunningPipeline ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            boxShadow: '0 2px 10px rgba(2, 132, 199, 0.4)',
            transition: 'all 0.15s ease',
          }}
        >
          {isRunningPipeline ? <RefreshCw size={13} className="spin-icon" /> : <Play size={13} />}
          {isRunningPipeline ? 'Executing Analysis...' : 'Run Analysis'}
        </button>
      </div>
    </header>
  );
};
