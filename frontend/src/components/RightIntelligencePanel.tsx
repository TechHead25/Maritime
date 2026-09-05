import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  Eye,
  Ship,
  Droplets,
  Compass,
  ChevronRight,
  Radio,
  FileText,
} from 'lucide-react';
import {
  AttributionScore,
  VesselTrack,
  SlickDetection,
  CaseDetails,
} from '../types';
import { ScoreBreakdown } from './ScoreBreakdown';
import { EvidencePanel } from './EvidencePanel';
import { UncertaintyPanel } from './UncertaintyPanel';
import { VesselIntelligenceModal } from './VesselIntelligenceModal';

export type IntelligenceViewMode = 'summary' | 'slick' | 'vessel' | 'candidate';

interface Props {
  details: CaseDetails | null;
  selectedSlick: SlickDetection | null;
  selectedVessel: VesselTrack | null;
  selectedCandidateScore: AttributionScore | null;
  onClearSelection: () => void;
  onSelectCandidateByMmsi: (mmsi: string) => void;
  onFollowVesselToggle?: (mmsi: string) => void;
  isFollowingVessel?: boolean;
}

export const RightIntelligencePanel: React.FC<Props> = ({
  details,
  selectedSlick,
  selectedVessel,
  selectedCandidateScore,
  onClearSelection,
  onSelectCandidateByMmsi,
  onFollowVesselToggle,
  isFollowingVessel = false,
}) => {
  const navigate = useNavigate();
  const [activeEvidenceTab, setActiveEvidenceTab] = useState<'breakdown' | 'evidence' | 'uncertainty'>('breakdown');
  const [profileModalMmsi, setProfileModalMmsi] = useState<string | null>(null);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState<boolean>(false);

  // Determine current active intelligence view mode
  let mode: IntelligenceViewMode = 'summary';
  if (selectedCandidateScore) {
    mode = 'candidate';
  } else if (selectedVessel) {
    mode = 'vessel';
  } else if (selectedSlick) {
    mode = 'slick';
  }

  const primarySar = details?.sar_scenes?.[0];
  const primarySlick = details?.slicks?.[0];
  const primaryReleaseWindow = details?.release_windows?.[0];
  const originCloud = (details?.probability_clouds && details.probability_clouds.length > 0)
    ? details.probability_clouds[details.probability_clouds.length - 1]
    : undefined;
  const originUncertainty = originCloud?.dispersion_radius_km || 1.08;
  const topScore = details?.attribution_scores?.[0];

  return (
    <aside style={{
      width: '440px',
      backgroundColor: '#0c1322',
      border: '1px solid #1e293b',
      borderRadius: '8px',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      overflow: 'hidden',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)',
    }}>
      {/* Header Bar with Context Mode & Deselect */}
      <div style={{
        padding: '0.75rem 1rem',
        borderBottom: '1px solid #1e293b',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#090d16',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#38bdf8' }}>
            {mode === 'candidate' && <Ship size={16} />}
            {mode === 'vessel' && <Compass size={16} />}
            {mode === 'slick' && <Droplets size={16} />}
            {mode === 'summary' && <Shield size={16} />}
          </span>
          <div>
            <h2 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
              {mode === 'candidate' && `Candidate Intelligence: ${selectedCandidateScore?.candidate_name}`}
              {mode === 'vessel' && `Vessel Telemetry: ${selectedVessel?.vessel_name}`}
              {mode === 'slick' && 'SAR Slick Feature Inspection'}
              {mode === 'summary' && 'Investigation Intelligence Dossier'}
            </h2>
            <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>
              {mode === 'summary' ? 'Comprehensive incident overview & decision support' : 'Context-sensitive forensic object inspection'}
            </div>
          </div>
        </div>

        {mode !== 'summary' && (
          <button
            onClick={onClearSelection}
            style={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              color: '#94a3b8',
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              fontSize: '0.68rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Overview ✕
          </button>
        )}
      </div>

      {/* Main Body (Scrollable) */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {/* ============================================================= */}
        {/* VIEW 1: INVESTIGATION SUMMARY (Default when nothing selected) */}
        {/* ============================================================= */}
        {mode === 'summary' && (
          <>
            {/* Scientific Transparency Notice */}
            <div style={{
              backgroundColor: '#111827',
              border: '1px solid #1e293b',
              borderRadius: '6px',
              padding: '0.75rem',
              fontSize: '0.72rem',
              color: '#94a3b8',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.4rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ color: '#f8fafc', fontSize: '0.75rem' }}>EVIDENCE & TRANSPARENCY TAXONOMY</strong>
                <span style={{ fontSize: '0.65rem', color: '#38bdf8' }}>Forensically Calibrated Matrix</span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.2rem' }}>
                <span style={observedTagStyle}>OBSERVED (Raw Sensor)</span>
                <span style={derivedTagStyle}>MODEL-DERIVED (Simulated)</span>
                <span style={assumptionTagStyle}>ASSUMPTION (Empirical)</span>
                <span style={uncertaintyTagStyle}>UNCERTAINTY (Confidence)</span>
              </div>
            </div>

            {/* Forensic Summary Statement */}
            <div style={{
              backgroundColor: 'rgba(2, 132, 199, 0.12)',
              border: '1px solid #0284c7',
              borderRadius: '6px',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.35rem',
            }}>
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#38bdf8', letterSpacing: '0.04em' }}>
                FORENSIC SUMMARY STATEMENT
              </div>
              <p style={{ fontSize: '0.78rem', color: '#f1f5f9', margin: 0, lineHeight: 1.45 }}>
                {details?.attribution_scores && details.attribution_scores.length > 0
                  ? `This vessel (${topScore?.candidate_name}, MMSI ${topScore?.mmsi}) is the highest-ranked candidate based on the available spatial, temporal, and navigational evidence (Attribution Score: ${topScore?.total_score.toFixed(1)}/100, Risk Level: ${topScore?.risk_level}).`
                  : 'Analysis complete. No candidate vessels intersected the reconstructed release envelope during the estimated discharge window.'}
              </p>
            </div>

            {/* Key Metric Blocks */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div style={metricCardStyle}>
                <div style={metricHeaderStyle}>
                  <span>SAR SLICK EXTENT</span>
                  <span style={observedTagStyle}>OBSERVED</span>
                </div>
                <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ef4444', marginTop: '0.25rem' }}>
                  {primarySlick ? `${primarySlick.area_sq_km.toFixed(1)} km²` : 'None'}
                </div>
                <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
                  Confidence: {primarySlick ? `${(primarySlick.confidence_score * 100).toFixed(1)}%` : 'N/A'}
                </div>
              </div>

              <div style={metricCardStyle}>
                <div style={metricHeaderStyle}>
                  <span>PROBABLE ORIGIN</span>
                  <span style={derivedTagStyle}>DERIVED</span>
                </div>
                <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#38bdf8', marginTop: '0.25rem' }}>
                  {originCloud ? `±${originUncertainty.toFixed(2)} km` : 'Pending'}
                </div>
                <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
                  90% Monte Carlo Dispersion
                </div>
              </div>

              <div style={metricCardStyle}>
                <div style={metricHeaderStyle}>
                  <span>DISCHARGE WINDOW</span>
                  <span style={derivedTagStyle}>DERIVED</span>
                </div>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fbbf24', marginTop: '0.25rem' }}>
                  {primaryReleaseWindow
                    ? `${new Date(primaryReleaseWindow.estimated_start_time).toISOString().slice(11, 16)}–${new Date(primaryReleaseWindow.estimated_end_time).toISOString().slice(11, 16)} UTC`
                    : 'Pending'}
                </div>
                <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
                  Estimated Release Envelope
                </div>
              </div>

              <div style={metricCardStyle}>
                <div style={metricHeaderStyle}>
                  <span>CANDIDATES RANKED</span>
                  <span style={derivedTagStyle}>DERIVED</span>
                </div>
                <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#a855f7', marginTop: '0.25rem' }}>
                  {details?.attribution_scores?.length || 0} Vessels
                </div>
                <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
                  Correlated against release zone
                </div>
              </div>
            </div>

            {/* Priority Candidate Quick List */}
            {details?.attribution_scores && details.attribution_scores.length > 0 && (
              <div style={{
                backgroundColor: '#111827',
                border: '1px solid #1e293b',
                borderRadius: '6px',
                padding: '0.85rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.6rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f8fafc' }}>
                    PRIORITY CANDIDATE VESSELS
                  </span>
                  <span style={{ fontSize: '0.65rem', color: '#64748b' }}>
                    Click to inspect full dossier
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {details.attribution_scores.map((score, idx) => (
                    <button
                      key={score.mmsi}
                      onClick={() => onSelectCandidateByMmsi(score.mmsi)}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.55rem 0.75rem',
                        borderRadius: '4px',
                        border: '1px solid #1e293b',
                        backgroundColor: idx === 0 ? 'rgba(239, 68, 68, 0.12)' : '#131b2e',
                        color: '#f8fafc',
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{
                          fontWeight: 700,
                          fontSize: '0.72rem',
                          color: idx === 0 ? '#ef4444' : '#94a3b8',
                        }}>
                          #{score.rank || idx + 1}
                        </span>
                        <div>
                          <strong style={{ fontSize: '0.78rem', display: 'block' }}>{score.candidate_name}</strong>
                          <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>MMSI: {score.mmsi} • {score.vessel_type}</span>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: '0.82rem', fontWeight: 700, color: idx === 0 ? '#ef4444' : '#38bdf8' }}>
                            {score.total_score.toFixed(1)}/100
                          </span>
                          <span style={{ display: 'block', fontSize: '0.60rem', color: '#94a3b8' }}>{score.risk_level}</span>
                        </div>
                        <ChevronRight size={14} color="#64748b" />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* ============================================================= */}
        {/* VIEW 2: SLICK INSPECTION (When detected slick polygon clicked) */}
        {/* ============================================================= */}
        {mode === 'slick' && selectedSlick && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid #ef4444',
              borderRadius: '6px',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.4rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, color: '#f87171', fontSize: '0.85rem' }}>
                  CLASSIFICATION: MINERAL OIL SLICK
                </span>
                <span style={observedTagStyle}>OBSERVED</span>
              </div>
              <p style={{ fontSize: '0.75rem', color: '#e2e8f0', margin: 0 }}>
                SAR dark-patch extraction matched spatial damping characteristics of heavy mineral hydrocarbons. Lookalike probability was suppressed based on morphological aspect ratio and ocean wind state.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div style={metricCardStyle}>
                <span style={detailLabelStyle}>SURFACE AREA</span>
                <strong style={{ color: '#f8fafc', fontSize: '1rem' }}>{selectedSlick.area_sq_km.toFixed(2)} km²</strong>
                <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>{(selectedSlick.area_sq_km * 100).toFixed(0)} hectares</span>
              </div>

              <div style={metricCardStyle}>
                <span style={detailLabelStyle}>PERIMETER</span>
                <strong style={{ color: '#f8fafc', fontSize: '1rem' }}>{selectedSlick.perimeter_km.toFixed(2)} km</strong>
                <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Boundary length</span>
              </div>

              <div style={metricCardStyle}>
                <span style={detailLabelStyle}>DETECTION CONFIDENCE</span>
                <strong style={{ color: '#34d399', fontSize: '1rem' }}>{(selectedSlick.confidence_score * 100).toFixed(1)}%</strong>
                <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>CFAR thresholding</span>
              </div>

              <div style={metricCardStyle}>
                <span style={detailLabelStyle}>LOOKALIKE RISK</span>
                <strong style={{ color: '#38bdf8', fontSize: '1rem' }}>{((selectedSlick.lookalike_probability ?? 0) * 100).toFixed(1)}%</strong>
                <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Biogenic / Wind shelter</span>
              </div>
            </div>

            {/* Geometry & Sensor Provenance */}
            <div style={{
              backgroundColor: '#111827',
              border: '1px solid #1e293b',
              borderRadius: '6px',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              fontSize: '0.75rem',
            }}>
              <strong style={{ color: '#f8fafc' }}>GEOMETRY & SENSOR LINEAGE</strong>
              <div>
                <span style={detailLabelStyle}>CENTROID COORDINATES</span>
                <div style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>
                  {selectedSlick.centroid.coordinates[1].toFixed(5)}°N, {selectedSlick.centroid.coordinates[0].toFixed(5)}°E
                </div>
              </div>
              <div>
                <span style={detailLabelStyle}>MAJOR AXIS ORIENTATION</span>
                <div style={{ color: '#cbd5e1' }}>{selectedSlick.major_axis_orientation_deg}° from True North</div>
              </div>
              <div>
                <span style={detailLabelStyle}>SATELLITE PLATFORM & SENSOR</span>
                <div style={{ color: '#cbd5e1' }}>
                  {primarySar?.satellite_platform || 'Sentinel-1A'} ({primarySar?.sensor_mode || 'IW'} mode, {primarySar?.polarization || 'VV'} polarization)
                </div>
              </div>
              <div>
                <span style={detailLabelStyle}>OBSERVATION TIMESTAMP</span>
                <div style={{ color: '#cbd5e1' }}>
                  {primarySar?.acquisition_timestamp ? new Date(primarySar.acquisition_timestamp).toISOString().replace('T', ' ') + ' UTC' : 'N/A'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================= */}
        {/* VIEW 3: UNRANKED AIS VESSEL (When generic track/marker clicked) */}
        {/* ============================================================= */}
        {mode === 'vessel' && selectedVessel && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{
              backgroundColor: '#111827',
              border: '1px solid #1e293b',
              borderRadius: '6px',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.4rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ color: '#f8fafc', fontSize: '0.88rem' }}>{selectedVessel.vessel_name}</strong>
                <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>NON-PRIORITY VESSEL</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                MMSI: {selectedVessel.mmsi} • Flag: {selectedVessel.flag_country} • Type: {selectedVessel.vessel_type}
              </div>

              <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.35rem' }}>
                <button
                  onClick={() => navigate(`/app/live?mmsi=${selectedVessel.mmsi}`)}
                  style={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #0284c7',
                    color: '#38bdf8',
                    padding: '0.25rem 0.55rem',
                    borderRadius: '4px',
                    fontSize: '0.68rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                  }}
                  title="Track vessel live on live maritime tracking map"
                >
                  <Radio size={11} /> View Live
                </button>
                <button
                  onClick={() => {
                    setProfileModalMmsi(selectedVessel.mmsi);
                    setIsProfileModalOpen(true);
                  }}
                  style={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    color: '#cbd5e1',
                    padding: '0.25rem 0.55rem',
                    borderRadius: '4px',
                    fontSize: '0.68rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                  }}
                  title="Open unified vessel profile"
                >
                  <FileText size={11} /> Vessel Profile
                </button>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div style={metricCardStyle}>
                <span style={detailLabelStyle}>AIS WAYPOINTS</span>
                <strong style={{ color: '#f8fafc', fontSize: '1rem' }}>{selectedVessel.waypoints.length}</strong>
                <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Total recorded pings</span>
              </div>

              <div style={metricCardStyle}>
                <span style={detailLabelStyle}>TRANSPONDER GAPS</span>
                <strong style={{ color: selectedVessel.has_ais_gaps ? '#ef4444' : '#10b981', fontSize: '1rem' }}>
                  {selectedVessel.has_ais_gaps ? `${selectedVessel.gap_intervals.length} Outage(s)` : 'None'}
                </strong>
                <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Signal integrity</span>
              </div>
            </div>

            <div style={{
              backgroundColor: '#111827',
              border: '1px solid #1e293b',
              borderRadius: '6px',
              padding: '0.85rem',
              fontSize: '0.75rem',
              color: '#94a3b8',
              lineHeight: 1.45,
            }}>
              <strong style={{ color: '#f8fafc', display: 'block', marginBottom: '0.3rem' }}>
                SPATIOTEMPORAL CORRELATION STATUS
              </strong>
              This vessel was analyzed against the reconstructed Lagrangian backward drift trajectory. It did not penetrate the high-probability dispersion envelope during the estimated release window, or its closest point of approach was beyond the correlation threshold.
            </div>
          </div>
        )}

        {/* ============================================================= */}
        {/* VIEW 4: CANDIDATE ATTRIBUTION & EVIDENCE (Ranked Candidate)  */}
        {/* ============================================================= */}
        {mode === 'candidate' && selectedCandidateScore && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Candidate Header Summary */}
            <div style={{
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid #ef4444',
              borderRadius: '6px',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.4rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, color: '#f87171', fontSize: '0.85rem' }}>
                  PRIORITY CANDIDATE (RANK #{selectedCandidateScore.rank || 1})
                </span>
                <span style={derivedTagStyle}>MODEL-DERIVED</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>
                    {selectedCandidateScore.total_score.toFixed(1)} <span style={{ fontSize: '0.80rem', color: '#94a3b8' }}>/ 100</span>
                  </div>
                  <div style={{ fontSize: '0.68rem', color: '#cbd5e1' }}>
                    Risk Classification: <strong style={{ color: '#f87171' }}>{selectedCandidateScore.risk_level}</strong>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => navigate(`/app/live?mmsi=${selectedCandidateScore.mmsi}`)}
                    style={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #0284c7',
                      color: '#38bdf8',
                      padding: '0.28rem 0.55rem',
                      borderRadius: '4px',
                      fontSize: '0.68rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                    }}
                    title="Track vessel live on live maritime tracking map"
                  >
                    <Radio size={11} /> View Live
                  </button>

                  <button
                    onClick={() => {
                      setProfileModalMmsi(selectedCandidateScore.mmsi);
                      setIsProfileModalOpen(true);
                    }}
                    style={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      color: '#cbd5e1',
                      padding: '0.28rem 0.55rem',
                      borderRadius: '4px',
                      fontSize: '0.68rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                    }}
                    title="Open unified vessel profile"
                  >
                    <FileText size={11} /> Profile
                  </button>

                  {onFollowVesselToggle && (
                    <button
                      onClick={() => onFollowVesselToggle(selectedCandidateScore.mmsi)}
                      style={{
                        backgroundColor: isFollowingVessel ? '#0284c7' : '#1e293b',
                        border: '1px solid #334155',
                        color: '#ffffff',
                        padding: '0.28rem 0.55rem',
                        borderRadius: '4px',
                        fontSize: '0.68rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                      }}
                    >
                      <Eye size={11} /> {isFollowingVessel ? 'Tracking' : 'Track'}
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Non-Accusatory Scientific Guardrail Banner */}
            <div style={{
              backgroundColor: 'rgba(245, 158, 11, 0.10)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '6px',
              padding: '0.6rem 0.8rem',
              fontSize: '0.68rem',
              color: '#fbbf24',
              lineHeight: 1.4,
            }}>
              <strong>Decision Support Guidance:</strong> Attribution scores represent spatiotemporal consistency with the physical release envelope, not legal determination of guilt. Verification requires port state inspection.
            </div>

            {/* Sub-Tabs: Breakdown / Evidence Chain / Uncertainty */}
            <div style={{ display: 'flex', gap: '0.4rem', borderBottom: '1px solid #1e293b', paddingBottom: '0.4rem' }}>
              <button
                onClick={() => setActiveEvidenceTab('breakdown')}
                style={tabButtonStyle(activeEvidenceTab === 'breakdown')}
              >
                Factor Breakdown
              </button>
              <button
                onClick={() => setActiveEvidenceTab('evidence')}
                style={tabButtonStyle(activeEvidenceTab === 'evidence')}
              >
                Evidence Chain ({selectedCandidateScore.evidence_items?.length || 0})
              </button>
              <button
                onClick={() => setActiveEvidenceTab('uncertainty')}
                style={tabButtonStyle(activeEvidenceTab === 'uncertainty')}
              >
                Uncertainty & QA
              </button>
            </div>

            {activeEvidenceTab === 'breakdown' && (
              <ScoreBreakdown score={selectedCandidateScore} />
            )}

            {activeEvidenceTab === 'evidence' && (
              <EvidencePanel score={selectedCandidateScore} />
            )}

            {activeEvidenceTab === 'uncertainty' && (
              <UncertaintyPanel
                uncertaintyRadiusKm={originUncertainty}
                confidenceInterval={0.90}
              />
            )}
          </div>
        )}
      </div>

      {/* Unified Vessel Profile Modal */}
      <VesselIntelligenceModal
        mmsi={profileModalMmsi}
        isOpen={isProfileModalOpen}
        onClose={() => {
          setIsProfileModalOpen(false);
          setProfileModalMmsi(null);
        }}
      />
    </aside>
  );
};

const metricCardStyle: React.CSSProperties = {
  backgroundColor: '#111827',
  border: '1px solid #1e293b',
  borderRadius: '6px',
  padding: '0.65rem 0.8rem',
  display: 'flex',
  flexDirection: 'column',
};

const metricHeaderStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  fontSize: '0.65rem',
  fontWeight: 700,
  color: '#64748b',
};

const detailLabelStyle: React.CSSProperties = {
  fontSize: '0.65rem',
  fontWeight: 700,
  color: '#64748b',
  display: 'block',
  marginBottom: '0.15rem',
};

const observedTagStyle: React.CSSProperties = {
  fontSize: '0.58rem',
  fontWeight: 700,
  padding: '0.1rem 0.35rem',
  borderRadius: '3px',
  backgroundColor: 'rgba(16, 185, 129, 0.15)',
  border: '1px solid #10b981',
  color: '#34d399',
};

const derivedTagStyle: React.CSSProperties = {
  fontSize: '0.58rem',
  fontWeight: 700,
  padding: '0.1rem 0.35rem',
  borderRadius: '3px',
  backgroundColor: 'rgba(2, 132, 199, 0.15)',
  border: '1px solid #0284c7',
  color: '#38bdf8',
};

const assumptionTagStyle: React.CSSProperties = {
  fontSize: '0.58rem',
  fontWeight: 700,
  padding: '0.1rem 0.35rem',
  borderRadius: '3px',
  backgroundColor: 'rgba(245, 158, 11, 0.15)',
  border: '1px solid #f59e0b',
  color: '#fbbf24',
};

const uncertaintyTagStyle: React.CSSProperties = {
  fontSize: '0.58rem',
  fontWeight: 700,
  padding: '0.1rem 0.35rem',
  borderRadius: '3px',
  backgroundColor: 'rgba(168, 85, 247, 0.15)',
  border: '1px solid #a855f7',
  color: '#c084fc',
};

const tabButtonStyle = (isActive: boolean): React.CSSProperties => ({
  backgroundColor: isActive ? '#1e293b' : 'transparent',
  border: '1px solid',
  borderColor: isActive ? '#334155' : 'transparent',
  color: isActive ? '#38bdf8' : '#94a3b8',
  padding: '0.3rem 0.6rem',
  borderRadius: '4px',
  fontSize: '0.72rem',
  fontWeight: isActive ? 700 : 500,
  cursor: 'pointer',
});
