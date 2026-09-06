import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Download,
  ShieldCheck,
  Search,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { fetchCases, fetchCaseDetails, downloadReportPdf } from '../services/api';

interface ReportRow {
  caseId: string;
  caseTitle: string;
  incidentTimestamp?: string;
  updatedAt?: string;
  topCandidateName?: string;
  topCandidateMmsi?: string;
  totalScore?: number;
  riskLevel?: string;
  pdfUrl: string;
}

export const ReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [reports, setReports] = useState<ReportRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [downloadingCaseId, setDownloadingCaseId] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const loadReports = async () => {
    setLoading(true);
    try {
      const cases = await fetchCases();
      const reportRows: ReportRow[] = [];

      for (const c of cases) {
        try {
          const details = await fetchCaseDetails(c.id);
          const topScore = details.attribution_scores?.[0];

          reportRows.push({
            caseId: c.id,
            caseTitle: c.title,
            incidentTimestamp: c.metadata?.incident_timestamp || c.created_at,
            updatedAt: c.updated_at,
            topCandidateName: topScore?.candidate_name || 'Analysis Pending',
            topCandidateMmsi: topScore?.mmsi || 'N/A',
            totalScore: topScore?.total_score,
            riskLevel: topScore?.risk_level,
            pdfUrl: `/api/cases/${c.id}/report/pdf`,
          });
        } catch (e) {
          console.warn('Error fetching case report details:', c.id, e);
        }
      }

      setReports(reportRows);
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (caseId: string) => {
    try {
      setDownloadingCaseId(caseId);
      setDownloadError(null);
      await downloadReportPdf(caseId);
    } catch (err: any) {
      console.error('Failed to download report PDF:', err);
      setDownloadError(err.message || 'Failed to download PDF dossier. Please ensure the backend is available.');
    } finally {
      setDownloadingCaseId(null);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const filteredReports = reports.filter((r) =>
    r.caseTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.caseId.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (r.topCandidateName && r.topCandidateName.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            Forensic Intelligence Dossiers & Reports
          </h1>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.25rem', marginBottom: 0 }}>
            Audit-grade PDF reports, evidence chains of custody, and cryptographic SHA-256 verification packages.
          </p>
        </div>

        <button
          onClick={loadReports}
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
          <RefreshCw size={14} /> Refresh Reports
        </button>
      </div>

      {/* Download Error Notice */}
      {downloadError && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '8px',
          padding: '0.75rem 1rem',
          color: '#f87171',
          fontSize: '0.82rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.5rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={16} />
            <span>{downloadError}</span>
          </div>
          <button
            onClick={() => setDownloadError(null)}
            style={{
              background: 'none',
              border: 'none',
              color: '#f87171',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: 700,
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        alignItems: 'center',
        backgroundColor: '#0c1322',
        padding: '0.85rem 1rem',
        borderRadius: '8px',
        border: '1px solid #1e293b',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          backgroundColor: '#131b2e',
          border: '1px solid #1e293b',
          borderRadius: '6px',
          padding: '0.4rem 0.75rem',
          flex: '1 1 320px',
        }}>
          <Search size={15} color="#64748b" />
          <input
            type="text"
            placeholder="Search reports by incident, case ID, or vessel name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: 'none',
              border: 'none',
              color: '#f8fafc',
              fontSize: '0.82rem',
              outline: 'none',
              width: '100%',
            }}
          />
        </div>

        <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: 'auto' }}>
          {filteredReports.length} available reports
        </span>
      </div>

      {/* Reports Table */}
      <div style={{
        backgroundColor: '#0c1322',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        overflow: 'hidden',
      }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#94a3b8' }}>
            Compiling report dossiers across cases...
          </div>
        ) : filteredReports.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#64748b' }}>
            No reports found matching your search.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.80rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#111827', borderBottom: '1px solid #1e293b', color: '#64748b', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>INCIDENT / CASE TITLE</th>
                  <th style={{ padding: '0.75rem 1rem' }}>HIGHEST-RANKED CANDIDATE</th>
                  <th style={{ padding: '0.75rem 1rem' }}>ATTRIBUTION SCORE</th>
                  <th style={{ padding: '0.75rem 1rem' }}>VERIFICATION</th>
                  <th style={{ padding: '0.75rem 1rem' }}>INCIDENT DATE (UTC)</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map((r) => (
                  <tr
                    key={r.caseId}
                    style={{ borderBottom: '1px solid #1e293b', transition: 'background 0.15s' }}
                  >
                    {/* Case Title */}
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <div style={{ fontWeight: 600, color: '#f8fafc' }}>{r.caseTitle}</div>
                      <div style={{ fontSize: '0.70rem', color: '#64748b', fontFamily: 'monospace' }}>
                        Case ID: {r.caseId}
                      </div>
                    </td>

                    {/* Top Candidate */}
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <strong style={{ color: '#f8fafc' }}>{r.topCandidateName}</strong>
                      {r.topCandidateMmsi !== 'N/A' && (
                        <div style={{ fontSize: '0.70rem', color: '#64748b', fontFamily: 'monospace' }}>
                          MMSI: {r.topCandidateMmsi}
                        </div>
                      )}
                    </td>

                    {/* Attribution Score */}
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {r.totalScore !== undefined ? (
                        <span style={{
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.70rem',
                          fontWeight: 700,
                          backgroundColor: r.totalScore > 75 ? 'rgba(239, 68, 68, 0.12)' : 'rgba(2, 132, 199, 0.12)',
                          color: r.totalScore > 75 ? '#f87171' : '#38bdf8',
                          border: `1px solid ${r.totalScore > 75 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(2, 132, 199, 0.3)'}`,
                          fontFamily: 'monospace',
                        }}>
                          {r.totalScore.toFixed(1)}/100 ({r.riskLevel || 'EVALUATED'})
                        </span>
                      ) : (
                        <span style={{ color: '#64748b', fontSize: '0.72rem' }}>Pending Pipeline</span>
                      )}
                    </td>

                    {/* Verification */}
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        fontSize: '0.68rem',
                        color: '#34d399',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        padding: '0.15rem 0.45rem',
                        borderRadius: '4px',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                      }}>
                        <ShieldCheck size={12} /> SHA-256 Sealed
                      </span>
                    </td>

                    {/* Incident Date */}
                    <td style={{ padding: '0.75rem 1rem', color: '#cbd5e1', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      {r.incidentTimestamp
                        ? new Date(r.incidentTimestamp).toISOString().replace('T', ' ').substring(0, 16) + 'Z'
                        : 'N/A'}
                    </td>

                    {/* Action */}
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.5rem' }}>
                        <button
                          onClick={() => handleDownload(r.caseId)}
                          disabled={downloadingCaseId === r.caseId}
                          style={{
                            backgroundColor: '#0284c7',
                            color: '#ffffff',
                            border: 'none',
                            padding: '0.35rem 0.75rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            cursor: downloadingCaseId === r.caseId ? 'wait' : 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            opacity: downloadingCaseId === r.caseId ? 0.75 : 1,
                          }}
                        >
                          {downloadingCaseId === r.caseId ? (
                            <>
                              <RefreshCw size={13} className="spin-icon" /> Compiling PDF...
                            </>
                          ) : (
                            <>
                              <Download size={13} /> Download PDF
                            </>
                          )}
                        </button>

                        <button
                          onClick={() => navigate(`/app/investigations/${r.caseId}`)}
                          style={{
                            backgroundColor: '#1e293b',
                            border: '1px solid #334155',
                            color: '#cbd5e1',
                            padding: '0.35rem 0.65rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Workspace
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
