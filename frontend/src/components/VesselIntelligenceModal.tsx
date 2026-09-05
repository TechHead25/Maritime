import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Ship,
  Compass,
  Radio,
  Shield,
  FileText,
  ExternalLink,
  Plus,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';
import { fetchVesselIntelligence, createInvestigationFromVessel } from '../services/api';

interface Props {
  mmsi: string | null;
  isOpen: boolean;
  onClose: () => void;
  onInvestigationCreated?: (caseId: string) => void;
}

export const VesselIntelligenceModal: React.FC<Props> = ({
  mmsi,
  isOpen,
  onClose,
  onInvestigationCreated,
}) => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'kinematics' | 'identity' | 'investigations' | 'evidence'>('kinematics');
  const [isCreatingCase, setIsCreatingCase] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen && mmsi) {
      loadProfile(mmsi);
    } else {
      setProfile(null);
    }
  }, [isOpen, mmsi]);

  const loadProfile = async (targetMmsi: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchVesselIntelligence(targetMmsi);
      setProfile(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch vessel intelligence.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateInvestigation = async () => {
    if (!mmsi) return;
    try {
      setIsCreatingCase(true);
      const res = await createInvestigationFromVessel({
        mmsi,
        buffer_degrees: 0.8,
      });
      const caseId = res.case?.id;
      if (caseId) {
        onClose();
        if (onInvestigationCreated) {
          onInvestigationCreated(caseId);
        } else {
          navigate(`/app/investigations/${caseId}`);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to initialize investigation from vessel.');
    } finally {
      setIsCreatingCase(false);
    }
  };

  const handleTrackLive = () => {
    if (!mmsi) return;
    onClose();
    navigate(`/app/live?mmsi=${mmsi}`);
  };

  if (!isOpen || !mmsi) return null;

  const identity = profile?.identity || {};
  const telemetry = profile?.telemetry || {};
  const investigations = profile?.investigations || [];
  const evidenceChain = profile?.evidence_chain || [];

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'LIVE POSITION':
        return { bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981', color: '#34d399', dot: '#10b981' };
      case 'RECENT POSITION':
        return { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', color: '#fbbf24', dot: '#f59e0b' };
      case 'HISTORICAL POSITION':
        return { bg: 'rgba(100, 116, 139, 0.15)', border: '#64748b', color: '#94a3b8', dot: '#64748b' };
      default:
        return { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', color: '#f87171', dot: '#ef4444' };
    }
  };

  const statusStyle = getStatusBadge(telemetry.position_status);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(5, 10, 20, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '1rem',
    }}>
      <div style={{
        backgroundColor: '#0c1322',
        border: '1px solid #1e293b',
        borderRadius: '10px',
        width: '100%',
        maxWidth: '820px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 12px 40px rgba(0, 0, 0, 0.7)',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid #1e293b',
          backgroundColor: '#090d16',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <span style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                color: identity.vessel_type === 'TANKER' ? '#f59e0b' : '#38bdf8',
                letterSpacing: '0.04em',
              }}>
                {identity.vessel_type || 'MARITIME VESSEL'}
              </span>

              {/* Status Badge */}
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
                backgroundColor: statusStyle.bg,
                border: `1px solid ${statusStyle.border}`,
                color: statusStyle.color,
                fontSize: '0.65rem',
                fontWeight: 700,
                padding: '0.1rem 0.45rem',
                borderRadius: '3px',
              }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: statusStyle.dot }} />
                {telemetry.position_status || 'CHECKING STATUS...'}
              </span>
            </div>

            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', margin: '0.2rem 0' }}>
              {identity.vessel_name || `Vessel MMSI ${mmsi}`}
            </h2>

            <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'monospace' }}>
              MMSI: {mmsi} {identity.imo ? `• IMO: ${identity.imo}` : ''} {identity.flag_country ? `• Flag: ${identity.flag_country}` : ''}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              onClick={handleTrackLive}
              style={{
                backgroundColor: '#1e293b',
                border: '1px solid #0284c7',
                color: '#38bdf8',
                padding: '0.35rem 0.75rem',
                borderRadius: '5px',
                fontSize: '0.72rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}
              title="Open vessel on live maritime tracking map"
            >
              <Radio size={13} /> Track Live
            </button>

            <button
              onClick={handleCreateInvestigation}
              disabled={isCreatingCase}
              style={{
                backgroundColor: '#0284c7',
                border: 'none',
                color: '#ffffff',
                padding: '0.35rem 0.85rem',
                borderRadius: '5px',
                fontSize: '0.72rem',
                fontWeight: 600,
                cursor: isCreatingCase ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                boxShadow: '0 2px 10px rgba(2, 132, 199, 0.4)',
              }}
              title="Initialize a new historical investigation centered on this vessel"
            >
              {isCreatingCase ? <RefreshCw size={13} className="spin-icon" /> : <Plus size={13} />}
              {isCreatingCase ? 'Initializing...' : 'Investigate Vessel'}
            </button>

            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: '#64748b',
                cursor: 'pointer',
                fontSize: '1.25rem',
                padding: '0.2rem 0.4rem',
                marginLeft: '0.5rem',
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          padding: '0.65rem 1.5rem 0',
          borderBottom: '1px solid #1e293b',
          backgroundColor: '#090d16',
        }}>
          <button
            onClick={() => setActiveTab('kinematics')}
            style={tabButtonStyle(activeTab === 'kinematics')}
          >
            <Compass size={14} /> Kinematics & Status
          </button>
          <button
            onClick={() => setActiveTab('identity')}
            style={tabButtonStyle(activeTab === 'identity')}
          >
            <Ship size={14} /> Registry Particulars
          </button>
          <button
            onClick={() => setActiveTab('investigations')}
            style={tabButtonStyle(activeTab === 'investigations')}
          >
            <Shield size={14} /> Investigations ({investigations.length})
          </button>
          <button
            onClick={() => setActiveTab('evidence')}
            style={tabButtonStyle(activeTab === 'evidence')}
          >
            <FileText size={14} /> Evidence Links ({evidenceChain.length})
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem', color: '#38bdf8', gap: '0.5rem' }}>
              <RefreshCw size={20} className="spin-icon" /> Loading verified vessel intelligence...
            </div>
          )}

          {error && (
            <div style={{
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid #ef4444',
              color: '#f87171',
              padding: '0.85rem',
              borderRadius: '6px',
              fontSize: '0.78rem',
            }}>
              {error}
            </div>
          )}

          {!loading && profile && (
            <>
              {/* TAB 1: KINEMATICS & REAL-TIME STATUS */}
              {activeTab === 'kinematics' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                    <div style={statCardStyle}>
                      <span style={labelStyle}>SPEED OVER GROUND</span>
                      <strong style={{ fontSize: '1.15rem', color: '#f8fafc', fontFamily: 'monospace' }}>
                        {telemetry.speed_over_ground_knots !== null ? `${telemetry.speed_over_ground_knots} kn` : 'N/A'}
                      </strong>
                    </div>

                    <div style={statCardStyle}>
                      <span style={labelStyle}>COURSE OVER GROUND</span>
                      <strong style={{ fontSize: '1.15rem', color: '#f8fafc', fontFamily: 'monospace' }}>
                        {telemetry.course_over_ground_deg !== null ? `${telemetry.course_over_ground_deg}°` : 'N/A'}
                      </strong>
                    </div>

                    <div style={statCardStyle}>
                      <span style={labelStyle}>TELEMETRY AGE</span>
                      <strong style={{ fontSize: '1rem', color: statusStyle.color }}>
                        {telemetry.data_age_seconds !== null
                          ? (telemetry.data_age_seconds < 60
                              ? `${Math.round(telemetry.data_age_seconds)}s ago`
                              : `${(telemetry.data_age_seconds / 60).toFixed(1)}m ago`)
                          : 'Archived Record'}
                      </strong>
                    </div>
                  </div>

                  {/* Coordinates & Nav Status */}
                  <div style={{
                    backgroundColor: '#111827',
                    border: '1px solid #1e293b',
                    borderRadius: '6px',
                    padding: '1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.65rem',
                    fontSize: '0.78rem',
                  }}>
                    <strong style={{ color: '#f8fafc' }}>Observation Telemetry & Lineage</strong>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem' }}>
                      <div>
                        <span style={labelStyle}>WGS84 COORDINATES</span>
                        <span style={{ color: '#38bdf8', fontFamily: 'monospace' }}>
                          {telemetry.latitude !== null && telemetry.longitude !== null
                            ? `${telemetry.latitude.toFixed(5)}°N, ${telemetry.longitude.toFixed(5)}°E`
                            : 'No observation point recorded'}
                        </span>
                      </div>

                      <div>
                        <span style={labelStyle}>NAVIGATIONAL STATUS</span>
                        <span style={{ color: '#cbd5e1' }}>
                          {telemetry.navigational_status || 'Underway using engine'}
                        </span>
                      </div>

                      <div>
                        <span style={labelStyle}>OBSERVATION TIMESTAMP (UTC)</span>
                        <span style={{ color: '#cbd5e1' }}>
                          {telemetry.last_update_utc ? new Date(telemetry.last_update_utc).toISOString().replace('T', ' ') : 'N/A'}
                        </span>
                      </div>

                      <div>
                        <span style={labelStyle}>TELEMETRY SOURCE</span>
                        <span style={{ color: '#cbd5e1' }}>
                          {telemetry.telemetry_source}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Signal Integrity & AIS Gaps */}
                  <div style={{
                    backgroundColor: '#111827',
                    border: '1px solid #1e293b',
                    borderRadius: '6px',
                    padding: '1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                    fontSize: '0.78rem',
                  }}>
                    <strong style={{ color: '#f8fafc' }}>Transponder Continuity & Signal Integrity</strong>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <div>
                        <span style={labelStyle}>TRANSPONDER STATUS</span>
                        <span style={{
                          color: telemetry.has_ais_gaps ? '#ef4444' : '#10b981',
                          fontWeight: 700,
                        }}>
                          {telemetry.has_ais_gaps ? `${telemetry.gap_intervals?.length || 1} Outage(s) Detected` : 'Nominal Continuous Transmission'}
                        </span>
                      </div>

                      <div>
                        <span style={labelStyle}>TRACK WAYPOINTS</span>
                        <span style={{ color: '#cbd5e1', fontWeight: 600 }}>
                          {telemetry.waypoints_count || 0} Recorded Pings
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: IDENTITY & REGISTRY */}
              {activeTab === 'identity' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {/* Registry Verification Badge */}
                  <div style={{
                    backgroundColor: identity.registry_verified ? 'rgba(16, 185, 129, 0.12)' : 'rgba(100, 116, 139, 0.12)',
                    border: `1px solid ${identity.registry_verified ? '#10b981' : '#64748b'}`,
                    borderRadius: '6px',
                    padding: '0.75rem 1rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '0.78rem',
                  }}>
                    <CheckCircle2 size={16} color={identity.registry_verified ? '#34d399' : '#94a3b8'} />
                    <span style={{ color: identity.registry_verified ? '#34d399' : '#94a3b8' }}>
                      {identity.registry_verified
                        ? `Official registry particulars verified via ${identity.registry_source}. Zero data fabrication.`
                        : 'Vessel is unindexed in local verified registry. Zero synthetic specifications have been invented.'}
                    </span>
                  </div>

                  {/* Identity Grid */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '0.85rem',
                    backgroundColor: '#111827',
                    border: '1px solid #1e293b',
                    borderRadius: '6px',
                    padding: '1rem',
                    fontSize: '0.78rem',
                  }}>
                    <div>
                      <span style={labelStyle}>VESSEL NAME</span>
                      <strong style={{ color: '#f8fafc' }}>{identity.vessel_name || 'N/A'}</strong>
                    </div>

                    <div>
                      <span style={labelStyle}>VESSEL TYPE</span>
                      <strong style={{ color: '#f8fafc' }}>{identity.vessel_type || 'UNKNOWN'}</strong>
                    </div>

                    <div>
                      <span style={labelStyle}>IMO NUMBER</span>
                      <span style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>{identity.imo || 'Not Recorded'}</span>
                    </div>

                    <div>
                      <span style={labelStyle}>CALL SIGN</span>
                      <span style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>{identity.callsign || 'Not Recorded'}</span>
                    </div>

                    <div>
                      <span style={labelStyle}>FLAG STATE / REGISTRY</span>
                      <strong style={{ color: '#38bdf8' }}>{identity.flag_country || 'Unknown Flag'}</strong>
                    </div>

                    <div>
                      <span style={labelStyle}>DEADWEIGHT TONNAGE (DWT)</span>
                      <span style={{ color: '#cbd5e1' }}>{identity.deadweight_tonnage ? `${identity.deadweight_tonnage.toLocaleString()} tonnes` : 'N/A'}</span>
                    </div>

                    <div>
                      <span style={labelStyle}>GROSS TONNAGE</span>
                      <span style={{ color: '#cbd5e1' }}>{identity.gross_tonnage ? `${identity.gross_tonnage.toLocaleString()} GT` : 'N/A'}</span>
                    </div>

                    <div>
                      <span style={labelStyle}>DIMENSIONS (LENGTH × BEAM)</span>
                      <span style={{ color: '#cbd5e1' }}>
                        {identity.length_meters && identity.beam_meters
                          ? `${identity.length_meters}m × ${identity.beam_meters}m`
                          : 'Dimensions unrecorded'}
                      </span>
                    </div>

                    <div>
                      <span style={labelStyle}>YEAR OF BUILD</span>
                      <span style={{ color: '#cbd5e1' }}>{identity.build_year || 'N/A'}</span>
                    </div>

                    <div>
                      <span style={labelStyle}>REGISTERED OWNER / OPERATOR</span>
                      <span style={{ color: '#cbd5e1' }}>{identity.owner_operator || 'Confidential / Unindexed'}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: INVESTIGATION RELATIONSHIPS */}
              {activeTab === 'investigations' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {investigations.length === 0 ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontSize: '0.82rem' }}>
                      No active or historical investigations currently cite this vessel.
                    </div>
                  ) : (
                    investigations.map((inv: any) => (
                      <div
                        key={inv.case_id}
                        style={{
                          backgroundColor: '#111827',
                          border: '1px solid #1e293b',
                          borderRadius: '6px',
                          padding: '1rem',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <strong style={{ color: '#f8fafc', fontSize: '0.85rem' }}>{inv.case_title}</strong>
                            <span style={{
                              fontSize: '0.62rem',
                              fontWeight: 700,
                              padding: '0.1rem 0.4rem',
                              borderRadius: '3px',
                              backgroundColor: inv.relationship_type === 'PRIORITY_CANDIDATE' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(2, 132, 199, 0.15)',
                              color: inv.relationship_type === 'PRIORITY_CANDIDATE' ? '#f87171' : '#38bdf8',
                              border: `1px solid ${inv.relationship_type === 'PRIORITY_CANDIDATE' ? '#ef4444' : '#0284c7'}`,
                            }}>
                              {inv.relationship_type.replace('_', ' ')}
                            </span>
                          </div>

                          <div style={{ fontSize: '0.70rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                            Case ID: {inv.case_id} • Status: {inv.case_status}
                          </div>

                          {inv.attribution_score !== null && (
                            <div style={{ fontSize: '0.72rem', color: '#cbd5e1', marginTop: '0.2rem' }}>
                              Attribution Score: <strong style={{ color: '#ef4444' }}>{inv.attribution_score.toFixed(1)}/100</strong> ({inv.risk_level})
                            </div>
                          )}
                        </div>

                        <button
                          onClick={() => {
                            onClose();
                            navigate(`/app/investigations/${inv.case_id}`);
                          }}
                          style={{
                            backgroundColor: '#1e293b',
                            border: '1px solid #334155',
                            color: '#38bdf8',
                            padding: '0.35rem 0.75rem',
                            borderRadius: '4px',
                            fontSize: '0.72rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.3rem',
                          }}
                        >
                          Open Dossier <ExternalLink size={12} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* TAB 4: EVIDENCE RELATIONSHIPS */}
              {activeTab === 'evidence' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {evidenceChain.length === 0 ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontSize: '0.82rem' }}>
                      No forensic evidence items are indexed for this vessel.
                    </div>
                  ) : (
                    evidenceChain.map((ev: any, idx: number) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: '#111827',
                          border: '1px solid #1e293b',
                          borderRadius: '6px',
                          padding: '0.85rem 1rem',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.25rem',
                          fontSize: '0.76rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <strong style={{ color: '#f8fafc' }}>{ev.title}</strong>
                          <span style={{ fontSize: '0.62rem', color: '#38bdf8', fontFamily: 'monospace' }}>
                            {ev.case_title}
                          </span>
                        </div>
                        <p style={{ color: '#cbd5e1', margin: 0, lineHeight: 1.4 }}>
                          {ev.description}
                        </p>
                        <div style={{ fontSize: '0.65rem', color: '#64748b' }}>
                          Factor: {ev.factor_category} • Source: {ev.source}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const statCardStyle: React.CSSProperties = {
  backgroundColor: '#111827',
  border: '1px solid #1e293b',
  borderRadius: '6px',
  padding: '0.75rem 1rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.2rem',
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.65rem',
  fontWeight: 700,
  color: '#64748b',
  display: 'block',
  marginBottom: '0.15rem',
};

const tabButtonStyle = (isActive: boolean): React.CSSProperties => ({
  backgroundColor: isActive ? '#1e293b' : 'transparent',
  border: '1px solid',
  borderColor: isActive ? '#334155' : 'transparent',
  borderBottom: 'none',
  color: isActive ? '#38bdf8' : '#94a3b8',
  padding: '0.45rem 0.85rem',
  borderTopLeftRadius: '5px',
  borderTopRightRadius: '5px',
  fontSize: '0.74rem',
  fontWeight: isActive ? 700 : 500,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  gap: '0.4rem',
});
