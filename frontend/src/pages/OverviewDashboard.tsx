import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderKanban,
  Satellite,
  Radio,
  Waves,
  Activity,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';
import { fetchCases, fetchCaseDetails } from '../services/api';
import { InvestigationCase, CaseDetails } from '../types';

export const OverviewDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState<InvestigationCase[]>([]);
  const [recentDetails, setRecentDetails] = useState<CaseDetails | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setError(null);
    try {
      const casesData = await fetchCases();
      setCases(casesData);

      if (casesData.length > 0) {
        const latestCase = casesData[0];
        try {
          const det = await fetchCaseDetails(latestCase.id);
          setRecentDetails(det);
        } catch (e) {
          console.warn('Could not load latest case details:', e);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load telemetry state.');
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const completedCount = cases.filter((c) => c.status === 'ATTRIBUTION_COMPLETED').length;
  const activeCount = cases.length - completedCount;

  // Derive alerts from actual cases
  const alerts: { type: 'warning' | 'info'; message: string; caseId?: string }[] = [];
  cases.forEach((c) => {
    if (c.status === 'CREATED') {
      alerts.push({
        type: 'warning',
        message: `Investigation '${c.title}' has not yet executed the hydrodynamic backward drift simulation.`,
        caseId: c.id,
      });
    }
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            Operational Intelligence Dashboard
          </h1>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.25rem', marginBottom: 0 }}>
            Real-time status of loaded marine pollution investigations, satellite observations, AIS tracking, and environmental models.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={loadData}
            style={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              color: '#cbd5e1',
              padding: '0.45rem 0.85rem',
              borderRadius: '6px',
              fontSize: '0.80rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <RefreshCw size={14} /> Refresh
          </button>
          <button
            onClick={() => navigate('/app/investigations')}
            style={{
              backgroundColor: '#0284c7',
              border: 'none',
              color: '#ffffff',
              padding: '0.45rem 1rem',
              borderRadius: '6px',
              fontSize: '0.80rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <FolderKanban size={14} /> View Investigations
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
          padding: '0.85rem 1.25rem',
          borderRadius: '6px',
          fontSize: '0.82rem',
        }}>
          <strong>System Warning:</strong> {error}
        </div>
      )}

      {/* 1. Status Telemetry Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        {/* Active Investigations */}
        <div style={metricCardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={metricLabelStyle}>ACTIVE INVESTIGATIONS</span>
            <FolderKanban size={18} color="#38bdf8" />
          </div>
          <div style={metricValueStyle}>{activeCount}</div>
          <div style={metricSubStyle}>
            {cases.length} total registered cases ({completedCount} completed)
          </div>
        </div>

        {/* Live AIS Telemetry */}
        <div style={metricCardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={metricLabelStyle}>AIS VESSEL TELEMETRY</span>
            <Radio size={18} color="#10b981" />
          </div>
          <div style={metricValueStyle}>
            {recentDetails ? recentDetails.vessel_tracks.length : '0'}
          </div>
          <div style={metricSubStyle}>
            Tracked vessels in active ROI
          </div>
        </div>

        {/* Latest SAR Satellite Observations */}
        <div style={metricCardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={metricLabelStyle}>SAR RADAR SCENES</span>
            <Satellite size={18} color="#38bdf8" />
          </div>
          <div style={metricValueStyle}>
            {recentDetails ? recentDetails.sar_scenes.length : '0'}
          </div>
          <div style={metricSubStyle}>
            {recentDetails?.sar_scenes?.[0]?.satellite_platform || 'Sentinel-1A'} scenes loaded
          </div>
        </div>

        {/* Environmental Model Freshness */}
        <div style={metricCardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={metricLabelStyle}>HYDRODYNAMIC GRIDS</span>
            <Waves size={18} color="#38bdf8" />
          </div>
          <div style={metricValueStyle}>Active</div>
          <div style={metricSubStyle}>
            CMEMS GLORYS12V1 & ERA5 Winds
          </div>
        </div>
      </div>

      {/* 2. Middle Section: Recent Investigations & Live Observations */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem', alignItems: 'start' }}>
        {/* Left: Recent Investigations Table */}
        <div style={panelContainerStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
              Recent Investigation Cases
            </h3>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
              Showing {Math.min(cases.length, 5)} of {cases.length} cases
            </span>
          </div>

          {cases.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#64748b', fontSize: '0.85rem' }}>
              No investigation cases recorded. Click "New Investigation" to initiate a forensic analysis.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.80rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1e293b', color: '#64748b', textAlign: 'left' }}>
                    <th style={{ padding: '0.65rem 0.75rem' }}>CASE TITLE</th>
                    <th style={{ padding: '0.65rem 0.75rem' }}>INCIDENT TIME</th>
                    <th style={{ padding: '0.65rem 0.75rem' }}>STATUS</th>
                    <th style={{ padding: '0.65rem 0.75rem' }}>DATA TYPE</th>
                    <th style={{ padding: '0.65rem 0.75rem', textAlign: 'right' }}>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {cases.slice(0, 5).map((c) => {
                    const isCompleted = c.status === 'ATTRIBUTION_COMPLETED';
                    const isRealtime = Boolean(
                      c.metadata?.is_realtime ||
                      c.metadata?.operational_mode === 'REAL_TIME_SURVEILLANCE' ||
                      c.id.includes('autodetect') ||
                      c.id.includes('real_time') ||
                      c.title.includes('REAL-TIME')
                    );
                    const isSynthetic = !isRealtime && (c.metadata?.synthetic === true);

                    return (
                      <tr
                        key={c.id}
                        style={{ borderBottom: '1px solid #1e293b', transition: 'background 0.15s' }}
                      >
                        <td style={{ padding: '0.65rem 0.75rem', fontWeight: 600, color: '#f8fafc' }}>
                          <div>{c.title}</div>
                          <div style={{ fontSize: '0.70rem', color: '#64748b', fontFamily: 'monospace' }}>{c.id}</div>
                        </td>
                        <td style={{ padding: '0.65rem 0.75rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                          {(c.metadata?.incident_timestamp || c.created_at) ? new Date(c.metadata?.incident_timestamp || c.created_at).toISOString().replace('T', ' ').substring(0, 16) + 'Z' : 'N/A'}
                        </td>
                        <td style={{ padding: '0.65rem 0.75rem' }}>
                          <span style={{
                            padding: '0.2rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.68rem',
                            fontWeight: 700,
                            backgroundColor: isCompleted ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.12)',
                            color: isCompleted ? '#34d399' : '#fbbf24',
                            border: `1px solid ${isCompleted ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                          }}>
                            {c.status}
                          </span>
                        </td>
                        <td style={{ padding: '0.65rem 0.75rem' }}>
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            fontSize: '0.68rem',
                            fontWeight: 700,
                            color: isRealtime ? '#34d399' : (isSynthetic ? '#fbbf24' : '#38bdf8'),
                            backgroundColor: isRealtime ? 'rgba(16, 185, 129, 0.15)' : (isSynthetic ? 'rgba(245, 158, 11, 0.12)' : 'rgba(56, 189, 248, 0.12)'),
                            border: `1px solid ${isRealtime ? 'rgba(16, 185, 129, 0.35)' : (isSynthetic ? 'rgba(245, 158, 11, 0.3)' : 'rgba(56, 189, 248, 0.25)')}`,
                            padding: '0.15rem 0.45rem',
                            borderRadius: '4px',
                          }}>
                            {isRealtime && <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981', boxShadow: '0 0 6px #10b981' }} />}
                            {isRealtime ? 'REAL-TIME SENSOR' : (isSynthetic ? 'BENCHMARK' : 'HISTORICAL SENSOR')}
                          </span>
                        </td>
                        <td style={{ padding: '0.65rem 0.75rem', textAlign: 'right' }}>
                          <button
                            onClick={() => navigate(`/app/investigations/${c.id}`)}
                            style={{
                              background: 'none',
                              border: '1px solid #334155',
                              color: '#38bdf8',
                              padding: '0.3rem 0.65rem',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              cursor: 'pointer',
                              fontWeight: 600,
                            }}
                          >
                            Open Workspace
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right: Data Provider Health & Alerts */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Data Source Health */}
          <div style={panelContainerStyle}>
            <h3 style={{ fontSize: '0.90rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.85rem' }}>
              Data Provider Health
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.78rem' }}>
              <div style={providerRowStyle}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Satellite size={15} color="#38bdf8" />
                  <span style={{ color: '#cbd5e1' }}>Copernicus Sentinel-1 SAR</span>
                </div>
                <span style={{ color: '#34d399', fontWeight: 600 }}>READY</span>
              </div>

              <div style={providerRowStyle}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Radio size={15} color="#10b981" />
                  <span style={{ color: '#cbd5e1' }}>AIS Ingestion Stream</span>
                </div>
                <span style={{ color: '#34d399', fontWeight: 600 }}>CONNECTED</span>
              </div>

              <div style={providerRowStyle}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Waves size={15} color="#38bdf8" />
                  <span style={{ color: '#cbd5e1' }}>CMEMS GLORYS12V1 Currents</span>
                </div>
                <span style={{ color: '#34d399', fontWeight: 600 }}>ONLINE</span>
              </div>

              <div style={providerRowStyle}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Activity size={15} color="#f59e0b" />
                  <span style={{ color: '#cbd5e1' }}>ECMWF ERA5 Atmospheric Wind</span>
                </div>
                <span style={{ color: '#34d399', fontWeight: 600 }}>ONLINE</span>
              </div>
            </div>

            <button
              onClick={() => navigate('/app/data-sources')}
              style={{
                width: '100%',
                marginTop: '1rem',
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                color: '#38bdf8',
                padding: '0.45rem',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              View Data Provider Configuration
            </button>
          </div>

          {/* Operational Alerts / Issues */}
          <div style={panelContainerStyle}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.65rem' }}>
              <AlertTriangle size={16} color="#fbbf24" />
              <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                Operational Notices ({alerts.length})
              </h3>
            </div>

            {alerts.length === 0 ? (
              <div style={{ fontSize: '0.78rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <CheckCircle2 size={14} /> All cases and providers operating normally.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {alerts.slice(0, 3).map((a, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '0.55rem 0.75rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(245, 158, 11, 0.08)',
                      border: '1px solid rgba(245, 158, 11, 0.25)',
                      fontSize: '0.75rem',
                      color: '#fbbf24',
                    }}
                  >
                    {a.message}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const metricCardStyle: React.CSSProperties = {
  backgroundColor: '#0c1322',
  border: '1px solid #1e293b',
  borderRadius: '8px',
  padding: '1rem 1.25rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.35rem',
};

const metricLabelStyle: React.CSSProperties = {
  fontSize: '0.68rem',
  fontWeight: 700,
  letterSpacing: '0.04em',
  color: '#64748b',
};

const metricValueStyle: React.CSSProperties = {
  fontSize: '1.65rem',
  fontWeight: 800,
  color: '#f8fafc',
  fontFamily: 'monospace',
};

const metricSubStyle: React.CSSProperties = {
  fontSize: '0.72rem',
  color: '#94a3b8',
};

const panelContainerStyle: React.CSSProperties = {
  backgroundColor: '#0c1322',
  border: '1px solid #1e293b',
  borderRadius: '8px',
  padding: '1.25rem',
};

const providerRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '0.55rem 0.65rem',
  backgroundColor: '#131b2e',
  borderRadius: '4px',
  border: '1px solid #1e293b',
};
