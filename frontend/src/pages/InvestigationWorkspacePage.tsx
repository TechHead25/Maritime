import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  CaseDetails,
  InvestigationCase,
  AttributionScore,
  SlickDetection,
  VesselTrack,
} from '../types';
import {
  fetchCases,
  fetchCaseDetails,
  executeInvestigationJob,
  pollInvestigationProgress,
  fetchCaseRuns,
  compareCaseRuns,
  downloadReportPdf,
  fetchSurveillanceAlerts,
  triggerSurveillanceScan,
} from '../services/api';
import { ConsoleHeader } from '../components/ConsoleHeader';
import { ConsoleNavPanel, ConsoleNavSection } from '../components/ConsoleNavPanel';
import { RightIntelligencePanel } from '../components/RightIntelligencePanel';
import { InvestigationMap } from '../components/InvestigationMap';
import { SynchronizedTimeline } from '../components/SynchronizedTimeline';
import { NewInvestigationModal } from '../components/NewInvestigationModal';
import { SARAnalysisModal } from '../components/SARAnalysisModal';
import {
  Plus,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

interface CaseRunSummary {
  run_id: string;
  run_number: number;
  created_at_utc: string;
  top_candidate?: string;
  top_score?: number;
}

export const InvestigationWorkspacePage: React.FC = () => {
  const { caseId: routeCaseId } = useParams<{ caseId?: string }>();
  const navigate = useNavigate();

  // Investigation state
  const [cases, setCases] = useState<InvestigationCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(routeCaseId || null);
  const [details, setDetails] = useState<CaseDetails | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Left Nav Section
  const [activeSection, setActiveSection] = useState<ConsoleNavSection>('overview');

  // Interactive Selection State
  const [selectedSlick, setSelectedSlick] = useState<SlickDetection | null>(null);
  const [selectedVessel, setSelectedVessel] = useState<VesselTrack | null>(null);
  const [selectedCandidateScore, setSelectedCandidateScore] = useState<AttributionScore | null>(null);
  const [followMmsi, setFollowMmsi] = useState<string | undefined>(undefined);

  // Modals
  const [isNewModalOpen, setIsNewModalOpen] = useState<boolean>(false);
  const [isSarModalOpen, setIsSarModalOpen] = useState<boolean>(false);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState<boolean>(false);
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [compareRunA, setCompareRunA] = useState<string>('');
  const [compareRunB, setCompareRunB] = useState<string>('');

  // Runs Versioning
  const [runs, setRuns] = useState<CaseRunSummary[]>([]);

  // Pipeline Job Execution & Live Progress
  const [isRunningJob, setIsRunningJob] = useState<boolean>(false);
  const [jobProgress, setJobProgress] = useState<{
    pct: number;
    stage: string;
    msg: string;
  } | null>(null);
  const pollingRef = useRef<any>(null);

  // Report Export
  const [isDownloadingReport, setIsDownloadingReport] = useState<boolean>(false);

  // Timeline playback state
  const [currentTimelineTime, setCurrentTimelineTime] = useState<Date>(new Date());
  const [isTimelinePlaying, setIsTimelinePlaying] = useState<boolean>(false);
  const [timelineSpeed, setTimelineSpeed] = useState<number>(5);

  // Satellite Surveillance State
  const [isSurveillanceScanning, setIsSurveillanceScanning] = useState<boolean>(false);
  const [surveillanceAlerts, setSurveillanceAlerts] = useState<any[]>([]);

  const loadSurveillanceAlerts = async () => {
    try {
      const alerts = await fetchSurveillanceAlerts(50);
      setSurveillanceAlerts(alerts);
    } catch (e) {
      console.warn('Failed to fetch surveillance alerts:', e);
    }
  };

  const handleTriggerSurveillanceScan = async () => {
    try {
      setIsSurveillanceScanning(true);
      setToastMessage('Initiating automated satellite radar surveillance pass across high-risk sectors...');
      const sweep = await triggerSurveillanceScan();
      await loadCasesList();
      await loadSurveillanceAlerts();
      setToastMessage(
        `Surveillance sweep completed: ${sweep.sectors_scanned} sectors scanned, ${sweep.spills_detected} oil slicks detected & analyzed.`
      );
    } catch (err: any) {
      setError(`Surveillance sweep failed: ${err.message}`);
    } finally {
      setIsSurveillanceScanning(false);
    }
  };

  // Synchronize route parameter
  useEffect(() => {
    if (routeCaseId && routeCaseId !== selectedCaseId) {
      setSelectedCaseId(routeCaseId);
    }
  }, [routeCaseId]);

  // Load cases list
  const loadCasesList = async () => {
    try {
      const casesData = await fetchCases();
      setCases(casesData);
      if (!selectedCaseId && casesData.length > 0) {
        setSelectedCaseId(casesData[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load cases:', err);
    }
  };

  useEffect(() => {
    loadCasesList();
    loadSurveillanceAlerts();
  }, []);

  // Load Case Details & Historical Runs
  const loadCaseData = async (caseId: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchCaseDetails(caseId);
      setDetails(data);

      // Default selection
      if (data.attribution_scores && data.attribution_scores.length > 0) {
        setSelectedCandidateScore(data.attribution_scores[0]);
      } else {
        setSelectedCandidateScore(null);
      }

      if (data.slicks && data.slicks.length > 0) {
        setSelectedSlick(data.slicks[0]);
      } else {
        setSelectedSlick(null);
      }

      if (data.release_windows && data.release_windows.length > 0) {
        setCurrentTimelineTime(new Date(data.release_windows[0].peak_probability_time));
      } else if (data.sar_scenes && data.sar_scenes.length > 0) {
        setCurrentTimelineTime(new Date(data.sar_scenes[0].acquisition_timestamp));
      }

      // Load runs
      try {
        const runData = await fetchCaseRuns(caseId);
        setRuns(runData.runs || []);
      } catch {
        setRuns([]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCaseId) {
      loadCaseData(selectedCaseId);
    } else {
      setLoading(false);
    }
  }, [selectedCaseId]);

  // Handle Left Navigation clicks to orchestrate sub-views
  const handleSelectSection = (sec: ConsoleNavSection) => {
    setActiveSection(sec);
    if (sec === 'overview' || sec === 'environmental' || sec === 'drift' || sec === 'origin' || sec === 'provenance') {
      setSelectedSlick(null);
      setSelectedVessel(null);
      setSelectedCandidateScore(null);
    } else if (sec === 'slick') {
      if (details?.slicks && details.slicks.length > 0) {
        setSelectedSlick(details.slicks[0]);
        setSelectedVessel(null);
        setSelectedCandidateScore(null);
      }
    } else if (sec === 'vessels' || sec === 'attribution' || sec === 'evidence' || sec === 'uncertainty') {
      if (details?.attribution_scores && details.attribution_scores.length > 0) {
        setSelectedCandidateScore(details.attribution_scores[0]);
        setSelectedSlick(null);
        setSelectedVessel(null);
      }
    } else if (sec === 'sar') {
      setIsSarModalOpen(true);
    } else if (sec === 'reports') {
      handleExportReport();
    }
  };

  // Selection interactions
  const handleSelectCandidateByMmsi = (mmsi: string) => {
    const cand = details?.attribution_scores?.find((s) => s.mmsi === mmsi);
    if (cand) {
      setSelectedCandidateScore(cand);
      setSelectedVessel(null);
      setSelectedSlick(null);
      setFollowMmsi(mmsi);
    } else {
      const v = details?.vessel_tracks?.find((t) => t.mmsi === mmsi);
      if (v) {
        setSelectedVessel(v);
        setSelectedCandidateScore(null);
        setSelectedSlick(null);
        setFollowMmsi(mmsi);
      }
    }
  };

  const handleSelectSlick = (slick: SlickDetection) => {
    setSelectedSlick(slick);
    setSelectedVessel(null);
    setSelectedCandidateScore(null);
  };

  const handleClearSelection = () => {
    setSelectedSlick(null);
    setSelectedVessel(null);
    setSelectedCandidateScore(null);
    setFollowMmsi(undefined);
    setActiveSection('overview');
  };

  // Dynamic Asynchronous Investigation Execution
  const handleRunAnalysis = async () => {
    if (!selectedCaseId || !details) return;

    try {
      setIsRunningJob(true);
      setError(null);
      setJobProgress({ pct: 5, stage: 'INITIALIZING', msg: 'Queueing forensic pipeline task in backend...' });

      const metaRelHours = Number((details.case.metadata as any)?.estimated_release_hours_ago);
      const relHours = !isNaN(metaRelHours) && metaRelHours > 0 ? metaRelHours : 14.0;

      const launch = await executeInvestigationJob(selectedCaseId, {
        particle_count: 500,
        random_seed: 42,
        estimated_release_hours_ago: relHours,
      });

      const jobId = launch.job_id;

      pollingRef.current = setInterval(async () => {
        try {
          const poll = await pollInvestigationProgress(selectedCaseId, jobId);
          setJobProgress({
            pct: poll.progress_pct || 10,
            stage: poll.stage || 'PROCESSING',
            msg: poll.message || 'Executing pipeline...',
          });

          if (poll.status === 'COMPLETED') {
            clearInterval(pollingRef.current);
            setIsRunningJob(false);
            setJobProgress(null);
            setToastMessage('Forensic analysis completed. Results and immutable versioned run persisted.');
            setTimeout(() => setToastMessage(null), 8000);
            loadCaseData(selectedCaseId);
          } else if (poll.status === 'FAILED') {
            clearInterval(pollingRef.current);
            setIsRunningJob(false);
            setJobProgress(null);
            setError(poll.error || 'Pipeline execution failed.');
          }
        } catch (pollErr: any) {
          console.warn('Progress poll error:', pollErr);
        }
      }, 450);
    } catch (err: any) {
      setIsRunningJob(false);
      setJobProgress(null);
      setError(err.message || 'Failed to start investigation job.');
    }
  };

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  // Export PDF Dossier
  const handleExportReport = async () => {
    if (!selectedCaseId) return;
    try {
      setIsDownloadingReport(true);
      await downloadReportPdf(selectedCaseId);
      setToastMessage('Forensic dossier compiled & downloaded successfully.');
      setTimeout(() => setToastMessage(null), 6000);
    } catch (e: any) {
      setError(`Failed to export report: ${e.message}`);
    } finally {
      setIsDownloadingReport(false);
    }
  };

  // Run Comparison
  const handleOpenCompare = () => {
    if (runs.length >= 2) {
      setCompareRunA(runs[runs.length - 2].run_id);
      setCompareRunB(runs[runs.length - 1].run_id);
      runComparison(runs[runs.length - 2].run_id, runs[runs.length - 1].run_id);
    }
    setIsCompareModalOpen(true);
  };

  const runComparison = async (a: string, b: string) => {
    if (!selectedCaseId || !a || !b) return;
    try {
      const res = await compareCaseRuns(selectedCaseId, a, b);
      setComparisonResult(res);
    } catch (e: any) {
      console.warn('Comparison error:', e);
    }
  };

  // Clean Empty State when no investigations exist
  if (!selectedCaseId && !loading && cases.length === 0) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '70vh',
        gap: '1.5rem',
        textAlign: 'center',
        maxWidth: '560px',
        margin: '0 auto',
      }}>
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
          border: '1px solid var(--glass-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#38bdf8',
        }}>
          <Plus size={28} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f8fafc', margin: '0 0 0.5rem' }}>
            No Active Investigations
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>
            Create an investigation from scratch by defining the area of interest, incident timestamp, and discovering real-world observations. No preloaded cases are required.
          </p>
        </div>
        <button
          onClick={() => setIsNewModalOpen(true)}
          style={{
            backgroundColor: '#0284c7',
            border: 'none',
            color: '#ffffff',
            padding: '0.65rem 1.4rem',
            borderRadius: '6px',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            boxShadow: '0 4px 15px rgba(2, 132, 199, 0.35)',
          }}
        >
          <Plus size={16} /> Create New Investigation
        </button>

        <NewInvestigationModal
          isOpen={isNewModalOpen}
          onClose={() => setIsNewModalOpen(false)}
          onCaseCreated={(newCase) => {
            loadCasesList();
            setSelectedCaseId(newCase.id);
            navigate(`/app/investigations/${newCase.id}`);
          }}
        />
      </div>
    );
  }

  const primarySar = details?.sar_scenes?.[0];
  const primarySlick = details?.slicks?.[0];
  const primaryReleaseWindow = details?.release_windows?.[0];
  const originCloud = (details?.probability_clouds && details.probability_clouds.length > 0)
    ? details.probability_clouds[details.probability_clouds.length - 1]
    : undefined;

  const defaultObsTime = primarySar?.acquisition_timestamp
    ? new Date(primarySar.acquisition_timestamp)
    : new Date();
  const defaultStartTime = new Date(defaultObsTime.getTime() - 24 * 3600 * 1000);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '0.85rem',
      maxWidth: '1800px',
      margin: '0 auto',
      minHeight: 'calc(100vh - 120px)',
    }}>
      {/* 1. ENTERPRISE CONSOLE HEADER */}
      {details && (
        <ConsoleHeader
          caseItem={details.case}
          cases={cases}
          onSelectCase={(id) => {
            setSelectedCaseId(id);
            navigate(`/app/investigations/${id}`);
          }}
          onOpenNewModal={() => setIsNewModalOpen(true)}
          readinessStatus="READY"
          lastAnalysisTime={details.case.updated_at}
          isRunningPipeline={isRunningJob}
          onRunAnalysis={handleRunAnalysis}
          onExportReport={handleExportReport}
          isDownloadingReport={isDownloadingReport}
          canCompare={runs.length >= 2}
          onOpenCompare={handleOpenCompare}
          isSurveillanceScanning={isSurveillanceScanning}
          onTriggerSurveillanceScan={handleTriggerSurveillanceScan}
          surveillanceAlertsCount={surveillanceAlerts.length}
        />
      )}

      {/* Dynamic Job Progress Bar */}
      {isRunningJob && jobProgress && (
        <div style={{
          backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
          border: '1px solid var(--glass-border)',
          borderRadius: '8px',
          padding: '0.85rem 1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#38bdf8' }}>
              PIPELINE STAGE: {jobProgress.stage} ({jobProgress.pct}%)
            </span>
            <span style={{ fontSize: '0.70rem', color: '#94a3b8' }}>
              Deterministic numerical calculation active...
            </span>
          </div>

          <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{
              width: `${jobProgress.pct}%`,
              height: '100%',
              backgroundColor: '#0284c7',
              transition: 'width 0.3s ease',
            }} />
          </div>

          <div style={{ fontSize: '0.72rem', color: '#cbd5e1' }}>
            {jobProgress.msg}
          </div>
        </div>
      )}

      {/* Toast Feedback */}
      {toastMessage && (
        <div style={{
          backgroundColor: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid var(--glass-border)',
          color: '#34d399',
          padding: '0.65rem 1rem',
          borderRadius: '6px',
          fontSize: '0.78rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <CheckCircle2 size={16} /> {toastMessage}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid var(--glass-border)',
          color: '#f87171',
          padding: '0.65rem 1rem',
          borderRadius: '6px',
          fontSize: '0.78rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* 2. THREE-COLUMN ENTERPRISE CONSOLE BODY */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '220px minmax(0, 1fr) 440px',
        gap: '0.85rem',
        flex: 1,
        minHeight: '680px',
      }}>
        {/* Left Column: 12-Item Forensic Navigation */}
        <ConsoleNavPanel
          activeSection={activeSection}
          onSelectSection={handleSelectSection}
          candidateCount={details?.attribution_scores?.length || 0}
          slickDetected={Boolean(details?.slicks && details.slicks.length > 0)}
        />

        {/* Center Column: Central Map Workspace + Synchronized Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', minWidth: 0 }}>
          {/* Main Map */}
          <div style={{ flex: 1, minHeight: '520px' }}>
            <InvestigationMap
              sarScene={primarySar}
              slick={primarySlick}
              clouds={details?.probability_clouds}
              releaseWindow={primaryReleaseWindow}
              originCentroid={originCloud?.center_point}
              originUncertaintyKm={originCloud?.dispersion_radius_km || 1.0}
              vesselTracks={details?.vessel_tracks}
              candidates={details?.candidates}
              attributionScores={details?.attribution_scores}
              selectedCandidateMmsi={selectedCandidateScore?.mmsi}
              selectedSlickId={selectedSlick?.id}
              onSelectCandidate={handleSelectCandidateByMmsi}
              onSelectSlick={handleSelectSlick}
              currentTime={currentTimelineTime}
            />
          </div>

          {/* Synchronized Timeline along bottom of central workspace */}
          {details && (
            <SynchronizedTimeline
              currentTime={currentTimelineTime}
              onTimeChange={setCurrentTimelineTime}
              startTime={defaultStartTime}
              endTime={defaultObsTime}
              releaseWindow={primaryReleaseWindow}
              clouds={details?.probability_clouds}
              vesselTracks={details?.vessel_tracks}
              selectedCandidateMmsi={selectedCandidateScore?.mmsi}
              onSelectCandidate={handleSelectCandidateByMmsi}
              isPlaying={isTimelinePlaying}
              onTogglePlay={() => setIsTimelinePlaying(!isTimelinePlaying)}
              playbackSpeed={timelineSpeed}
              onSpeedChange={setTimelineSpeed}
              followMmsi={followMmsi}
              onToggleFollow={setFollowMmsi}
              onReset={() => setCurrentTimelineTime(defaultStartTime)}
            />
          )}
        </div>

        {/* Right Column: Dynamic Intelligence Panel */}
        <RightIntelligencePanel
          details={details}
          activeSection={activeSection}
          selectedSlick={selectedSlick}
          selectedVessel={selectedVessel}
          selectedCandidateScore={selectedCandidateScore}
          onClearSelection={handleClearSelection}
          onSelectCandidateByMmsi={handleSelectCandidateByMmsi}
          onFollowVesselToggle={(mmsi) => setFollowMmsi(followMmsi === mmsi ? undefined : mmsi)}
          isFollowingVessel={Boolean(followMmsi && selectedCandidateScore && followMmsi === selectedCandidateScore.mmsi)}
          onOpenSarModal={() => setIsSarModalOpen(true)}
        />
      </div>

      {/* Comparison Modal */}
      {isCompareModalOpen && (
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
            backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
            border: '1px solid var(--glass-border)',
            borderRadius: '10px',
            width: '100%',
            maxWidth: '680px',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                Historical Run Comparison
              </h3>
              <button
                onClick={() => setIsCompareModalOpen(false)}
                style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={labelStyle}>BASELINE RUN</label>
                <select
                  value={compareRunA}
                  onChange={(e) => {
                    setCompareRunA(e.target.value);
                    runComparison(e.target.value, compareRunB);
                  }}
                  style={selectStyle}
                >
                  {runs.map((r) => (
                    <option key={r.run_id} value={r.run_id}>
                      Run #{r.run_number} ({r.top_candidate})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={labelStyle}>TARGET COMPARISON RUN</label>
                <select
                  value={compareRunB}
                  onChange={(e) => {
                    setCompareRunB(e.target.value);
                    runComparison(compareRunA, e.target.value);
                  }}
                  style={selectStyle}
                >
                  {runs.map((r) => (
                    <option key={r.run_id} value={r.run_id}>
                      Run #{r.run_number} ({r.top_candidate})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {comparisonResult && (
              <div style={{
                backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                border: '1px solid var(--glass-border)',
                borderRadius: '6px',
                padding: '1rem',
                fontSize: '0.78rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.65rem',
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                  <div>
                    <span style={{ color: '#64748b', fontSize: '0.68rem', display: 'block' }}>RUN A TOP CANDIDATE</span>
                    <strong style={{ color: '#f8fafc' }}>
                      {comparisonResult.run_a.top_candidate} ({comparisonResult.run_a.top_score} pts)
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', fontSize: '0.68rem', display: 'block' }}>RUN B TOP CANDIDATE</span>
                    <strong style={{ color: '#f8fafc' }}>
                      {comparisonResult.run_b.top_candidate} ({comparisonResult.run_b.top_score} pts)
                    </strong>
                  </div>
                </div>

                <div>
                  <span style={{ color: '#64748b', fontSize: '0.68rem', display: 'block' }}>RANKING SHIFT DETECTED</span>
                  <strong style={{ color: comparisonResult.candidate_ranking_changed ? '#f59e0b' : '#34d399' }}>
                    {comparisonResult.candidate_ranking_changed ? 'Yes - Different Primary Candidate' : 'No - Primary Candidate Unchanged'}
                  </strong>
                </div>

                <div>
                  <span style={{ color: '#64748b', fontSize: '0.68rem', display: 'block' }}>PARAMETER DELTAS</span>
                  {Object.keys(comparisonResult.parameter_changes || {}).length > 0 ? (
                    <div style={{ marginTop: '0.25rem', fontFamily: 'monospace', fontSize: '0.72rem', color: '#cbd5e1' }}>
                      {Object.entries(comparisonResult.parameter_changes).map(([k, v]: [string, any]) => (
                        <div key={k}>• {k}: {String(v.run_a)} → {String(v.run_b)}</div>
                      ))}
                    </div>
                  ) : (
                    <span style={{ color: '#94a3b8' }}>No configuration differences recorded.</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* New Investigation Modal */}
      <NewInvestigationModal
        isOpen={isNewModalOpen}
        onClose={() => setIsNewModalOpen(false)}
        onCaseCreated={(newCase) => {
          loadCasesList();
          setSelectedCaseId(newCase.id);
          navigate(`/app/investigations/${newCase.id}`);
        }}
      />

      {/* Sentinel-1 SAR Radar Imagery & Diagnostics Modal */}
      <SARAnalysisModal
        isOpen={isSarModalOpen}
        onClose={() => setIsSarModalOpen(false)}
        caseId={selectedCaseId || details?.case?.id || 'case_new_diamond_2020'}
        sarScene={primarySar}
        slick={primarySlick}
      />
    </div>
  );
};

const selectStyle: React.CSSProperties = {
  backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
  border: '1px solid var(--glass-border)',
  color: '#f8fafc',
  padding: '0.35rem 0.65rem',
  borderRadius: '4px',
  fontSize: '0.75rem',
  outline: 'none',
  cursor: 'pointer',
  width: '100%',
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.65rem',
  fontWeight: 700,
  color: '#64748b',
  display: 'block',
  marginBottom: '0.25rem',
  letterSpacing: '0.03em',
};
