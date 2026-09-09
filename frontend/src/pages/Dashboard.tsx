import React, { useEffect, useState } from 'react';
import {
  CaseDetails,
  HealthStatus,
  InvestigationCase,
  AttributionScore,
  FullInvestigationResponse,
} from '../types';
import {
  fetchCases,
  fetchCaseDetails,
  fetchHealth,
  runInvestigation,
} from '../services/api';
import { AppShell } from '../components/AppShell';
import { CaseSelector } from '../components/CaseSelector';
import { CaseHeader } from '../components/CaseHeader';
import { WorkflowStepper } from '../components/WorkflowStepper';
import { InvestigationMap } from '../components/InvestigationMap';
import { OriginPanel } from '../components/OriginPanel';
import { ReleaseWindowPanel } from '../components/ReleaseWindowPanel';
import { CandidateRanking } from '../components/CandidateRanking';
import { ScoreBreakdown } from '../components/ScoreBreakdown';
import { EvidencePanel } from '../components/EvidencePanel';
import { DataSourcesPanel } from '../components/DataSourcesPanel';
import { UncertaintyPanel } from '../components/UncertaintyPanel';
import { SynchronizedTimeline } from '../components/SynchronizedTimeline';
import { NewInvestigationModal } from '../components/NewInvestigationModal';

export const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [cases, setCases] = useState<InvestigationCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('case_new_diamond_2020');
  const [isNewCaseModalOpen, setIsNewCaseModalOpen] = useState<boolean>(false);
  const [details, setDetails] = useState<CaseDetails | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedCandidateScore, setSelectedCandidateScore] = useState<AttributionScore | null>(null);
  const [isRunningPipeline, setIsRunningPipeline] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Synchronized Continuous Timeline State
  const defaultObsTime = details?.sar_scenes?.[0]?.acquisition_timestamp
    ? new Date(details.sar_scenes[0].acquisition_timestamp)
    : new Date();
  const defaultStartTime = new Date(defaultObsTime.getTime() - 14.5 * 3600 * 1000);

  const [currentTimelineTime, setCurrentTimelineTime] = useState<Date>(defaultStartTime);
  const [isTimelinePlaying, setIsTimelinePlaying] = useState<boolean>(false);
  const [timelineSpeed, setTimelineSpeed] = useState<number>(5);
  const [followMmsi, setFollowMmsi] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (details?.release_windows && details.release_windows.length > 0) {
      setCurrentTimelineTime(new Date(details.release_windows[0].peak_probability_time));
    } else if (details?.sar_scenes && details.sar_scenes.length > 0) {
      setCurrentTimelineTime(new Date(details.sar_scenes[0].acquisition_timestamp));
    }
  }, [details]);

  useEffect(() => {
    loadWorkspace();
  }, []);

  useEffect(() => {
    if (selectedCaseId) {
      loadCaseData(selectedCaseId);
    }
  }, [selectedCaseId]);

  const loadWorkspace = async () => {
    try {
      const h = await fetchHealth();
      setHealth(h);
    } catch (err: any) {
      console.warn('Backend API unreachable, using development state:', err);
      setHealth(null);
    }

    try {
      const caseList = await fetchCases();
      setCases(caseList);
      if (caseList.length > 0) {
        // Select initial historical case or first available investigation
        const hist = caseList.find((c) => c.id === 'case_new_diamond_2020');
        setSelectedCaseId(hist ? hist.id : caseList[0].id);
      }
    } catch (err: any) {
      console.warn('Failed to load cases from API:', err);
    }
  };

  const loadCaseData = async (caseId: string) => {
    try {
      setLoading(true);
      const d = await fetchCaseDetails(caseId);
      setDetails(d);
      setError(null);

      // Auto-select rank 1 candidate if scores exist
      if (d.attribution_scores && d.attribution_scores.length > 0) {
        setSelectedCandidateScore(d.attribution_scores[0]);
      } else {
        setSelectedCandidateScore(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load case data');
    } finally {
      setLoading(false);
    }
  };

  const handleRunPipeline = async () => {
    if (!details) return;
    try {
      setIsRunningPipeline(true);
      const metaRelHours = Number((details.case.metadata as any)?.estimated_release_hours_ago);
      const relHours = !isNaN(metaRelHours) && metaRelHours > 0
        ? metaRelHours
        : (details.case.id === 'case_new_diamond_2020' ? 9.25 : (details.case.id === 'case_ennore_2017' ? 20.75 : 12.0));

      const res: FullInvestigationResponse = await runInvestigation(details.case.id, {
        particle_count: 500,
        random_seed: 42,
        estimated_release_hours_ago: relHours,
      });

      // Update state with complete pipeline response
      setDetails((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          case: res.case,
          drift_simulations: res.drift_simulations,
          probability_clouds: res.probability_clouds,
          release_windows: res.release_windows,
          candidates: res.candidate_vessels,
          attribution_scores: res.attribution_scores,
        };
      });

      if (res.attribution_scores.length > 0) {
        setSelectedCandidateScore(res.attribution_scores[0]);
      }

      setToastMessage(res.summary_verdict);
      setTimeout(() => setToastMessage(null), 10000);
    } catch (err: any) {
      alert(`Pipeline execution error: ${err.message}`);
    } finally {
      setIsRunningPipeline(false);
    }
  };

  const primarySlick = details?.slicks?.[0];
  const primarySar = details?.sar_scenes?.[0];
  const primaryReleaseWindow = details?.release_windows?.[0];
  const originCloud = (details?.probability_clouds && details.probability_clouds.length > 0)
    ? details.probability_clouds[details.probability_clouds.length - 1]
    : undefined;

  const displayClouds = details?.probability_clouds;
  const displayVesselTracks = details?.vessel_tracks;
  const displayCandidates = details?.candidates;
  const displayScores = details?.attribution_scores;

  return (
    <AppShell
      health={health}
      caseSelectorSlot={
        <CaseSelector
          cases={cases}
          selectedCaseId={selectedCaseId}
          onSelectCase={(id) => setSelectedCaseId(id)}
          isLoading={loading}
          onOpenNewCaseModal={() => setIsNewCaseModalOpen(true)}
        />
      }
    >
      <NewInvestigationModal
        isOpen={isNewCaseModalOpen}
        onClose={() => setIsNewCaseModalOpen(false)}
        onCaseCreated={(createdCase) => {
          setCases((prev) => [...prev, createdCase]);
          setSelectedCaseId(createdCase.id);
          setToastMessage(`Created new case '${createdCase.title}' successfully.`);
        }}
      />

      {/* Forensic Attribution Verdict Toast Banner */}
      {toastMessage && (
        <div style={{
          backgroundColor: '#04785715',
          border: '1px solid var(--glass-border)',
          color: '#10b981',
          padding: '0.90rem 1.25rem',
          borderRadius: '8px',
          marginBottom: '1rem',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.8rem',
          boxShadow: '0 4px 16px rgba(16, 185, 129, 0.15)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <span style={{ fontSize: '1.2rem', color: '#34d399' }}>✓</span>
            <div>
              <strong style={{ color: '#f8fafc' }}>Forensic Attribution Verdict:</strong> {toastMessage}
            </div>
          </div>
          <button
            onClick={() => setToastMessage(null)}
            style={{ background: 'none', border: 'none', color: '#10b981', cursor: 'pointer', fontSize: '1rem' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Connection / Backend Alert */}
      {error && (
        <div style={{
          backgroundColor: '#ef444415',
          border: '1px solid var(--glass-border)',
          color: '#f87171',
          padding: '1rem 1.25rem',
          borderRadius: '8px',
          marginBottom: '1rem',
          fontSize: '0.85rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <strong>Telemetry Alert:</strong> {error}. Ensure FastAPI backend is active on port 8000.
          </div>
          <button
            onClick={() => loadCaseData(selectedCaseId)}
            style={{
              backgroundColor: '#ef4444',
              color: '#ffffff',
              border: 'none',
              padding: '0.35rem 0.75rem',
              borderRadius: '4px',
              fontSize: '0.78rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div style={{
          textAlign: 'center',
          padding: '8rem 0',
          color: '#94a3b8',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '1rem',
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid #334155',
            borderTopColor: '#38bdf8',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }} />
          <span style={{ fontSize: '0.90rem', fontWeight: 600, color: '#f8fafc' }}>
            Loading Investigation Telemetry...
          </span>
        </div>
      ) : details ? (
        <>
          {/* Case Header Banner */}
          <CaseHeader
            caseItem={details.case}
            sarScene={primarySar}
            slick={primarySlick}
            onRunInvestigation={handleRunPipeline}
            isRunningPipeline={isRunningPipeline}
          />

          {/* Workflow Stepper Guide */}
          <WorkflowStepper
            status={details.case.status}
            isRunning={isRunningPipeline}
            onStartPipeline={handleRunPipeline}
          />

          {/* Main 2-Column Forensic Workspace Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.35fr 1fr', gap: '1.25rem', alignItems: 'start' }}>
            {/* Left Column: Geospatial Map & Origin Diagnostics */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Synchronized Continuous Timeline Scrubber & Dynamic Player */}
              <SynchronizedTimeline
                startTime={defaultStartTime}
                endTime={defaultObsTime}
                currentTime={currentTimelineTime}
                onTimeChange={(t) => setCurrentTimelineTime(t)}
                isPlaying={isTimelinePlaying}
                onTogglePlay={() => setIsTimelinePlaying((prev) => !prev)}
                playbackSpeed={timelineSpeed}
                onSpeedChange={(spd) => setTimelineSpeed(spd)}
                releaseWindow={primaryReleaseWindow}
                clouds={details.probability_clouds}
                vesselTracks={details.vessel_tracks}
                selectedCandidateMmsi={selectedCandidateScore?.mmsi}
                onSelectCandidate={(mmsi) => {
                  const s = details.attribution_scores.find((x) => x.mmsi === mmsi);
                  if (s) setSelectedCandidateScore(s);
                }}
                followMmsi={followMmsi}
                onToggleFollow={(mmsi) => setFollowMmsi(mmsi)}
                onReset={() => {
                  setIsTimelinePlaying(false);
                  if (details.release_windows && details.release_windows.length > 0) {
                    setCurrentTimelineTime(new Date(details.release_windows[0].peak_probability_time));
                  } else {
                    setCurrentTimelineTime(defaultStartTime);
                  }
                }}
              />

              <InvestigationMap
                sarScene={primarySar}
                slick={primarySlick}
                clouds={displayClouds}
                releaseWindow={primaryReleaseWindow}
                originCentroid={originCloud?.center_point}
                originUncertaintyKm={originCloud?.dispersion_radius_km}
                vesselTracks={displayVesselTracks}
                candidates={displayCandidates}
                attributionScores={displayScores}
                selectedCandidateMmsi={selectedCandidateScore?.mmsi}
                onSelectCandidate={(mmsi) => {
                  const s = details.attribution_scores.find((x) => x.mmsi === mmsi);
                  if (s) setSelectedCandidateScore(s);
                }}
                currentTime={currentTimelineTime}
              />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <OriginPanel
                  originCentroid={originCloud?.center_point}
                  originUncertaintyKm={originCloud?.dispersion_radius_km}
                  slickCentroid={primarySlick?.centroid}
                />

                <ReleaseWindowPanel releaseWindow={primaryReleaseWindow} />
              </div>

              {(() => {
                const isRealtime = Boolean(
                  details.case.metadata?.is_realtime ||
                  details.case.metadata?.operational_mode === 'REAL_TIME_SURVEILLANCE' ||
                  details.case.id.includes('autodetect') ||
                  details.case.id.includes('real_time') ||
                  details.case.title.includes('REAL-TIME')
                );
                const isSynthetic = !isRealtime && (details.case.metadata?.synthetic ?? false);

                return (
                  <DataSourcesPanel
                    dataSources={details.environment}
                    isSynthetic={isSynthetic}
                    isRealtime={isRealtime}
                  />
                );
              })()}
            </div>

            {/* Right Column: Candidate Leaderboard, Sub-Scores & Evidence Chain */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {details.attribution_scores && details.attribution_scores.length > 0 ? (
                <CandidateRanking
                  scores={details.attribution_scores}
                  selectedScoreId={selectedCandidateScore?.id}
                  onSelectScore={(s) => setSelectedCandidateScore(s)}
                />
              ) : (
                <div style={{
                  backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                  border: '1px dashed #334155',
                  borderRadius: '8px',
                  padding: '2rem 1.5rem',
                  textAlign: 'center',
                  color: '#94a3b8',
                  fontSize: '0.85rem',
                }}>
                  <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>⚖️</div>
                  <strong style={{ color: '#f8fafc' }}>Attribution Analysis Pending</strong>
                  <div style={{ fontSize: '0.75rem', marginTop: '0.35rem', color: '#64748b' }}>
                    Execute the forensic pipeline to evaluate candidate vessel tracks against the release envelope and compute attribution scores.
                  </div>
                </div>
              )}

              {selectedCandidateScore && (
                <>
                  <ScoreBreakdown score={selectedCandidateScore} />
                  <EvidencePanel score={selectedCandidateScore} />
                </>
              )}

              <UncertaintyPanel
                uncertaintyRadiusKm={originCloud?.dispersion_radius_km || 0.58}
                confidenceInterval={primaryReleaseWindow?.confidence_interval || 0.90}
              />
            </div>
          </div>
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '4rem 0', color: '#94a3b8' }}>
          No investigation case selected. Choose an incident from the case selector above.
        </div>
      )}
    </AppShell>
  );
};
