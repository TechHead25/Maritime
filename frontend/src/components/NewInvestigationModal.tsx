import React, { useState } from 'react';
import {
  Satellite,
  Radio,
  Waves,
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Search,
  Plus,
} from 'lucide-react';
import { InvestigationCase } from '../types';
import { createInvestigation, evaluateReadiness } from '../services/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onCaseCreated: (createdCase: InvestigationCase) => void;
}

const PRESET_REGIONS = [
  { name: 'Sri Lanka (Southern Shipping Corridor)', minLon: 80.0, minLat: 5.0, maxLon: 83.5, maxLat: 9.0 },
  { name: 'Strait of Malacca (Chokepoint)', minLon: 99.0, minLat: 1.0, maxLon: 104.5, maxLat: 5.0 },
  { name: 'Bay of Bengal (Regional)', minLon: 80.0, minLat: 10.0, maxLon: 93.0, maxLat: 21.0 },
  { name: 'Arabian Sea (West Coast)', minLon: 68.0, minLat: 15.0, maxLon: 75.0, maxLat: 24.0 },
];

export const NewInvestigationModal: React.FC<Props> = ({
  isOpen,
  onClose,
  onCaseCreated,
}) => {
  const [step, setStep] = useState<1 | 2>(1);

  // Form Fields
  const [title, setTitle] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [incidentTime, setIncidentTime] = useState<string>(
    new Date(Date.now() - 24 * 3600 * 1000).toISOString().slice(0, 16)
  );

  // Area of Interest Coordinates
  const [minLon, setMinLon] = useState<number>(80.0);
  const [minLat, setMinLat] = useState<number>(5.0);
  const [maxLon, setMaxLon] = useState<number>(83.5);
  const [maxLat, setMaxLat] = useState<number>(9.0);

  // Provider Choices
  const [sarSource, setSarSource] = useState<string>('COPERNICUS_CDSE');
  const [aisSource, setAisSource] = useState<string>('HISTORICAL_REGISTRY');
  const [oceanSource, setOceanSource] = useState<string>('CMEMS_GLORYS12V1');
  const [windSource, setWindSource] = useState<string>('ECMWF_ERA5');

  // Discovery & Readiness State
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [readinessData, setReadinessData] = useState<any>(null);
  const [evalError, setEvalError] = useState<string | null>(null);
  const [allowPartialData, setAllowPartialData] = useState<boolean>(false);

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSelectPreset = (preset: typeof PRESET_REGIONS[0]) => {
    setMinLon(preset.minLon);
    setMinLat(preset.minLat);
    setMaxLon(preset.maxLon);
    setMaxLat(preset.maxLat);
  };

  const handleQueryProvidersAndAssess = async () => {
    if (!title.trim()) {
      setSubmitError('Investigation Title is required before discovering data.');
      return;
    }
    setSubmitError(null);
    setIsEvaluating(true);
    setEvalError(null);

    try {
      const incIso = new Date(incidentTime).toISOString();
      const assessment = await evaluateReadiness({
        min_lon: minLon,
        min_lat: minLat,
        max_lon: maxLon,
        max_lat: maxLat,
        incident_time_utc: incIso,
        allow_partial_data: allowPartialData,
      });
      setReadinessData(assessment);
      setStep(2);
    } catch (err: any) {
      setEvalError(err.message || 'Failed to query provider catalogues and evaluate readiness.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleCreateAndLaunch = async () => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const formData = new FormData();
      formData.append('title', title.trim());
      formData.append('description', description.trim() || `Investigation for ${title.trim()}`);
      formData.append('incident_timestamp_utc', new Date(incidentTime).toISOString());
      formData.append('min_lon', minLon.toString());
      formData.append('min_lat', minLat.toString());
      formData.append('max_lon', maxLon.toString());
      formData.append('max_lat', maxLat.toString());

      const created = await createInvestigation(formData);
      onCaseCreated(created);
      onClose();
    } catch (err: any) {
      setSubmitError(err.message || 'Investigation creation failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(5, 10, 20, 0.85)',
      backdropFilter: 'blur(6px)',
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
        maxWidth: '740px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.7)',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid #1e293b',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
              {step === 1 ? 'Create Forensic Investigation' : 'Data Readiness Assessment Matrix'}
            </h2>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '0.2rem 0 0' }}>
              {step === 1
                ? 'Define incident metadata, geographic bounds, and connect operational provider catalogues.'
                : 'Verified data availability, spatiotemporal overlap, and pipeline execution readiness.'}
            </p>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#64748b',
              cursor: 'pointer',
              fontSize: '1.2rem',
              padding: '0.2rem 0.5rem',
            }}
          >
            ✕
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {step === 1 ? (
            <>
              {/* Incident Basics */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={labelStyle}>INVESTIGATION TITLE *</label>
                  <input
                    type="text"
                    placeholder="e.g., MT Horizon Spill Event - East Corridor"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    style={inputStyle}
                  />
                </div>

                <div>
                  <label style={labelStyle}>INCIDENT DATE / TIME (UTC) *</label>
                  <input
                    type="datetime-local"
                    value={incidentTime}
                    onChange={(e) => setIncidentTime(e.target.value)}
                    style={inputStyle}
                  />
                </div>

                <div>
                  <label style={labelStyle}>DESCRIPTION / SUMMARY</label>
                  <input
                    type="text"
                    placeholder="Initial surveillance notes or incident briefing..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    style={inputStyle}
                  />
                </div>
              </div>

              {/* Area of Interest & Presets */}
              <div style={{
                backgroundColor: '#111827',
                border: '1px solid #1e293b',
                borderRadius: '6px',
                padding: '1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label style={labelStyle}>AREA OF INTEREST (WGS84 BOUNDING BOX)</label>
                  <div style={{ display: 'flex', gap: '0.35rem' }}>
                    {PRESET_REGIONS.map((preset) => (
                      <button
                        key={preset.name}
                        type="button"
                        onClick={() => handleSelectPreset(preset)}
                        style={{
                          backgroundColor: '#1e293b',
                          border: '1px solid #334155',
                          color: '#94a3b8',
                          padding: '0.2rem 0.45rem',
                          borderRadius: '3px',
                          fontSize: '0.65rem',
                          cursor: 'pointer',
                        }}
                      >
                        {preset.name.split(' ')[0]}
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem' }}>
                  <div>
                    <span style={{ fontSize: '0.65rem', color: '#64748b' }}>MIN LON (°E)</span>
                    <input
                      type="number"
                      step="0.1"
                      value={minLon}
                      onChange={(e) => setMinLon(Number(e.target.value))}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <span style={{ fontSize: '0.65rem', color: '#64748b' }}>MIN LAT (°N)</span>
                    <input
                      type="number"
                      step="0.1"
                      value={minLat}
                      onChange={(e) => setMinLat(Number(e.target.value))}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <span style={{ fontSize: '0.65rem', color: '#64748b' }}>MAX LON (°E)</span>
                    <input
                      type="number"
                      step="0.1"
                      value={maxLon}
                      onChange={(e) => setMaxLon(Number(e.target.value))}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <span style={{ fontSize: '0.65rem', color: '#64748b' }}>MAX LAT (°N)</span>
                    <input
                      type="number"
                      step="0.1"
                      value={maxLat}
                      onChange={(e) => setMaxLat(Number(e.target.value))}
                      style={inputStyle}
                    />
                  </div>
                </div>
              </div>

              {/* Data Provider Modalities */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={providerBoxStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#38bdf8' }}>
                    <Satellite size={14} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>SAR Satellite Data</span>
                  </div>
                  <select
                    value={sarSource}
                    onChange={(e) => setSarSource(e.target.value)}
                    style={selectStyle}
                  >
                    <option value="COPERNICUS_CDSE">Copernicus Sentinel-1 (CDSE STAC)</option>
                    <option value="HISTORICAL_ARCHIVE">Local Calibrated SAR Archive</option>
                  </select>
                </div>

                <div style={providerBoxStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#38bdf8' }}>
                    <Radio size={14} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>AIS Telemetry Provider</span>
                  </div>
                  <select
                    value={aisSource}
                    onChange={(e) => setAisSource(e.target.value)}
                    style={selectStyle}
                  >
                    <option value="HISTORICAL_REGISTRY">Maritime AIS Database / Archive</option>
                    <option value="LIVE_STREAM">Live Streaming AIS (Server WebSocket)</option>
                  </select>
                </div>

                <div style={providerBoxStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#38bdf8' }}>
                    <Waves size={14} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>Hydrodynamic Currents</span>
                  </div>
                  <select
                    value={oceanSource}
                    onChange={(e) => setOceanSource(e.target.value)}
                    style={selectStyle}
                  >
                    <option value="CMEMS_GLORYS12V1">CMEMS Global Ocean Physics (GLORYS12V1)</option>
                  </select>
                </div>

                <div style={providerBoxStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#38bdf8' }}>
                    <Activity size={14} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>Atmospheric Winds</span>
                  </div>
                  <select
                    value={windSource}
                    onChange={(e) => setWindSource(e.target.value)}
                    style={selectStyle}
                  >
                    <option value="ECMWF_ERA5">ECMWF ERA5 / Open-Meteo Marine (10m Neutral)</option>
                  </select>
                </div>
              </div>
            </>
          ) : (
            /* Step 2: Readiness Assessment Matrix */
            <>
              {readinessData && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {/* Overall Status Banner */}
                  <div style={{
                    backgroundColor: readinessData.overall_readiness === 'READY'
                      ? 'rgba(16, 185, 129, 0.12)'
                      : (readinessData.overall_readiness === 'PARTIAL' ? 'rgba(245, 158, 11, 0.12)' : 'rgba(239, 68, 68, 0.12)'),
                    border: `1px solid ${readinessData.overall_readiness === 'READY' ? '#10b981' : (readinessData.overall_readiness === 'PARTIAL' ? '#f59e0b' : '#ef4444')}`,
                    borderRadius: '6px',
                    padding: '1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.4rem',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{
                        fontWeight: 700,
                        fontSize: '0.85rem',
                        color: readinessData.overall_readiness === 'READY' ? '#34d399' : (readinessData.overall_readiness === 'PARTIAL' ? '#fbbf24' : '#f87171'),
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                      }}>
                        {readinessData.overall_readiness === 'READY' ? <CheckCircle2 size={18} /> : (readinessData.overall_readiness === 'PARTIAL' ? <AlertTriangle size={18} /> : <XCircle size={18} />)}
                        DATA READINESS: {readinessData.overall_readiness}
                      </span>
                      <div style={{ fontSize: '0.72rem', color: '#cbd5e1' }}>
                        Spatial Overlap: <strong>{readinessData.spatial_overlap_pct}%</strong> | Temporal Overlap: <strong>{readinessData.temporal_overlap_pct}%</strong>
                      </div>
                    </div>
                    <p style={{ fontSize: '0.78rem', color: '#e2e8f0', margin: 0 }}>
                      {readinessData.summary_explanation}
                    </p>
                  </div>

                  {/* Modality Cards */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    {Object.entries(readinessData.modalities).map(([key, info]: [string, any]) => {
                      const isReady = info.status === 'READY';
                      const isPartial = info.status === 'PARTIAL';
                      return (
                        <div
                          key={key}
                          style={{
                            backgroundColor: '#111827',
                            border: '1px solid #1e293b',
                            borderRadius: '6px',
                            padding: '0.85rem',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.4rem',
                            fontSize: '0.75rem',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <strong style={{ color: '#f8fafc', textTransform: 'uppercase' }}>{key.replace('_', ' ')}</strong>
                            <span style={{
                              padding: '0.15rem 0.45rem',
                              borderRadius: '3px',
                              fontSize: '0.65rem',
                              fontWeight: 700,
                              backgroundColor: isReady ? 'rgba(16, 185, 129, 0.15)' : (isPartial ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)'),
                              color: isReady ? '#34d399' : (isPartial ? '#fbbf24' : '#f87171'),
                            }}>
                              {info.status}
                            </span>
                          </div>
                          <div style={{ color: '#94a3b8', fontSize: '0.70rem' }}>
                            Provider: {info.provider_name}
                          </div>
                          <div style={{ color: '#cbd5e1', fontSize: '0.72rem' }}>
                            {info.reason}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Partial Data Override Toggle */}
                  {readinessData.overall_readiness === 'PARTIAL' && (
                    <label style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.6rem',
                      backgroundColor: 'rgba(245, 158, 11, 0.1)',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      borderRadius: '6px',
                      padding: '0.75rem 1rem',
                      fontSize: '0.75rem',
                      color: '#fbbf24',
                      cursor: 'pointer',
                    }}>
                      <input
                        type="checkbox"
                        checked={allowPartialData}
                        onChange={(e) => setAllowPartialData(e.target.checked)}
                      />
                      <span>
                        <strong>Explicit Override:</strong> Allow forensic execution with partial observational data (e.g. dark vessel hypothesis / single-modality drift).
                      </span>
                    </label>
                  )}
                </div>
              )}
            </>
          )}

          {/* Feedback Messages */}
          {evalError && (
            <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', padding: '0.65rem', borderRadius: '4px', color: '#f87171', fontSize: '0.75rem' }}>
              {evalError}
            </div>
          )}
          {submitError && (
            <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', padding: '0.65rem', borderRadius: '4px', color: '#f87171', fontSize: '0.75rem' }}>
              {submitError}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div style={{
          padding: '1rem 1.5rem',
          borderTop: '1px solid #1e293b',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#090d16',
        }}>
          {step === 2 ? (
            <button
              type="button"
              onClick={() => setStep(1)}
              style={{
                backgroundColor: 'transparent',
                border: '1px solid #334155',
                color: '#94a3b8',
                padding: '0.45rem 0.95rem',
                borderRadius: '4px',
                fontSize: '0.78rem',
                cursor: 'pointer',
              }}
            >
              ← Back to Parameters
            </button>
          ) : (
            <div />
          )}

          <div style={{ display: 'flex', gap: '0.6rem' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                backgroundColor: 'transparent',
                border: '1px solid #334155',
                color: '#cbd5e1',
                padding: '0.45rem 0.95rem',
                borderRadius: '4px',
                fontSize: '0.78rem',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>

            {step === 1 ? (
              <button
                type="button"
                onClick={handleQueryProvidersAndAssess}
                disabled={isEvaluating}
                style={{
                  backgroundColor: '#0284c7',
                  border: 'none',
                  color: '#ffffff',
                  padding: '0.45rem 1.15rem',
                  borderRadius: '4px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: isEvaluating ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}
              >
                <Search size={14} /> {isEvaluating ? 'Querying Catalogues...' : 'Discover & Assess Readiness →'}
              </button>
            ) : (
              <button
                type="button"
                onClick={handleCreateAndLaunch}
                disabled={
                  isSubmitting ||
                  (!readinessData?.can_run && !allowPartialData)
                }
                style={{
                  backgroundColor: (readinessData?.can_run || allowPartialData) ? '#10b981' : '#334155',
                  border: 'none',
                  color: '#ffffff',
                  padding: '0.45rem 1.15rem',
                  borderRadius: '4px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: (readinessData?.can_run || allowPartialData) ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}
              >
                <Plus size={14} /> {isSubmitting ? 'Initializing...' : 'Create & Open Workspace'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.68rem',
  fontWeight: 700,
  color: '#64748b',
  display: 'block',
  marginBottom: '0.25rem',
  letterSpacing: '0.03em',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  backgroundColor: '#131b2e',
  border: '1px solid #1e293b',
  color: '#f8fafc',
  padding: '0.45rem 0.65rem',
  borderRadius: '4px',
  fontSize: '0.78rem',
  outline: 'none',
  boxSizing: 'border-box',
};

const selectStyle: React.CSSProperties = {
  width: '100%',
  backgroundColor: '#131b2e',
  border: '1px solid #1e293b',
  color: '#f8fafc',
  padding: '0.35rem 0.5rem',
  borderRadius: '4px',
  fontSize: '0.72rem',
  outline: 'none',
  marginTop: '0.25rem',
};

const providerBoxStyle: React.CSSProperties = {
  backgroundColor: '#111827',
  border: '1px solid #1e293b',
  borderRadius: '6px',
  padding: '0.65rem 0.85rem',
};
