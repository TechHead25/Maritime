import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  Plus,
  ArrowRight,
  RefreshCw,
  Satellite,
  Radio,
  Waves,
  Activity,
} from 'lucide-react';
import { fetchCases } from '../services/api';
import { InvestigationCase } from '../types';
import { NewInvestigationModal } from '../components/NewInvestigationModal';

export const InvestigationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState<InvestigationCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCases();
      setCases(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load investigations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.id.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || c.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const getGeoAreaString = (c: InvestigationCase) => {
    if (c.region_of_interest?.coordinates?.[0]) {
      const coords = c.region_of_interest.coordinates[0];
      const lons = coords.map((pt) => pt[0]);
      const lats = coords.map((pt) => pt[1]);
      const minLon = Math.min(...lons).toFixed(1);
      const maxLon = Math.max(...lons).toFixed(1);
      const minLat = Math.min(...lats).toFixed(1);
      const maxLat = Math.max(...lats).toFixed(1);
      return `${minLat}°N–${maxLat}°N, ${minLon}°E–${maxLon}°E`;
    }
    return 'Regional Bounding Box';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header and Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            Investigation Case Management
          </h1>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.25rem', marginBottom: 0 }}>
            Historical and active oil spill incidents, sensor data status, and forensic reconstruction cases.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          style={{
            backgroundColor: '#0284c7',
            border: 'none',
            color: '#ffffff',
            padding: '0.55rem 1.15rem',
            borderRadius: '6px',
            fontSize: '0.82rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            boxShadow: '0 2px 10px rgba(2, 132, 199, 0.3)',
          }}
        >
          <Plus size={16} /> New Investigation
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        alignItems: 'center',
        backgroundColor: '#0c1322',
        padding: '0.85rem 1rem',
        borderRadius: '8px',
        border: '1px solid #1e293b',
        flexWrap: 'wrap',
      }}>
        {/* Search */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          backgroundColor: '#131b2e',
          border: '1px solid #1e293b',
          borderRadius: '6px',
          padding: '0.4rem 0.75rem',
          flex: '1 1 260px',
        }}>
          <Search size={15} color="#64748b" />
          <input
            type="text"
            placeholder="Search by case title or ID..."
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

        {/* Status Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={15} color="#64748b" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              backgroundColor: '#131b2e',
              border: '1px solid #1e293b',
              color: '#f8fafc',
              fontSize: '0.80rem',
              borderRadius: '6px',
              padding: '0.4rem 0.75rem',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="ALL">All Statuses ({cases.length})</option>
            <option value="CREATED">CREATED</option>
            <option value="SAR_PROCESSED">SAR_PROCESSED</option>
            <option value="DRIFT_COMPLETED">DRIFT_COMPLETED</option>
            <option value="ATTRIBUTION_COMPLETED">ATTRIBUTION_COMPLETED</option>
          </select>
        </div>

        <button
          onClick={loadCases}
          style={{
            background: 'none',
            border: '1px solid #1e293b',
            color: '#94a3b8',
            padding: '0.4rem 0.75rem',
            borderRadius: '6px',
            fontSize: '0.80rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
          }}
        >
          <RefreshCw size={13} /> Refresh
        </button>
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
          <strong>System Error:</strong> {error}
        </div>
      )}

      {/* Investigations Table */}
      <div style={{
        backgroundColor: '#0c1322',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        overflow: 'hidden',
      }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#94a3b8' }}>
            Loading investigations registry...
          </div>
        ) : filteredCases.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#64748b' }}>
            No investigations match your query. Clear filters or create a new investigation.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.80rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#111827', borderBottom: '1px solid #1e293b', color: '#64748b', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>CASE TITLE & ID</th>
                  <th style={{ padding: '0.75rem 1rem' }}>STATUS</th>
                  <th style={{ padding: '0.75rem 1rem' }}>INCIDENT DATE (UTC)</th>
                  <th style={{ padding: '0.75rem 1rem' }}>GEOGRAPHIC AREA</th>
                  <th style={{ padding: '0.75rem 1rem' }}>DATA COMPLETENESS</th>
                  <th style={{ padding: '0.75rem 1rem' }}>LAST UPDATED</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {filteredCases.map((c) => {
                  const isCompleted = c.status === 'ATTRIBUTION_COMPLETED';
                  const incidentTime = c.metadata?.incident_timestamp || c.created_at;

                  return (
                    <tr
                      key={c.id}
                      style={{
                        borderBottom: '1px solid #1e293b',
                        transition: 'background-color 0.15s',
                      }}
                    >
                      {/* Title & ID */}
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <div style={{ fontWeight: 600, color: '#f8fafc' }}>{c.title}</div>
                        <div style={{ fontSize: '0.70rem', color: '#64748b', fontFamily: 'monospace' }}>{c.id}</div>
                      </td>

                      {/* Status */}
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{
                          padding: '0.2rem 0.55rem',
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

                      {/* Incident Date */}
                      <td style={{ padding: '0.75rem 1rem', color: '#cbd5e1', fontFamily: 'monospace' }}>
                        {incidentTime ? new Date(incidentTime).toISOString().replace('T', ' ').substring(0, 16) + 'Z' : 'N/A'}
                      </td>

                      {/* Geographic Area */}
                      <td style={{ padding: '0.75rem 1rem', color: '#94a3b8', fontSize: '0.75rem' }}>
                        {getGeoAreaString(c)}
                      </td>

                      {/* Data Completeness */}
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <div style={{ display: 'flex', gap: '0.35rem' }}>
                          <span title="SAR Scene" style={badgeStyle('#0284c7')}>
                            <Satellite size={10} /> SAR
                          </span>
                          <span title="AIS Telemetry" style={badgeStyle('#10b981')}>
                            <Radio size={10} /> AIS
                          </span>
                          <span title="Hydrodynamics" style={badgeStyle('#38bdf8')}>
                            <Waves size={10} /> CMEMS
                          </span>
                          <span title="Meteorology" style={badgeStyle('#f59e0b')}>
                            <Activity size={10} /> ERA5
                          </span>
                        </div>
                      </td>

                      {/* Last Updated */}
                      <td style={{ padding: '0.75rem 1rem', color: '#64748b', fontSize: '0.72rem', fontFamily: 'monospace' }}>
                        {c.updated_at ? new Date(c.updated_at).toISOString().replace('T', ' ').substring(0, 16) + 'Z' : 'N/A'}
                      </td>

                      {/* Action */}
                      <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '0.5rem' }}>
                          <button
                            onClick={() => navigate(`/app/investigations/${c.id}`)}
                            style={{
                              backgroundColor: '#0284c7',
                              border: 'none',
                              color: '#ffffff',
                              padding: '0.35rem 0.75rem',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.3rem',
                            }}
                          >
                            Open Workspace <ArrowRight size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* New Investigation Modal */}
      <NewInvestigationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCaseCreated={(createdCase) => {
          setIsModalOpen(false);
          setCases((prev) => [createdCase, ...prev]);
          navigate(`/app/investigations/${createdCase.id}`);
        }}
      />
    </div>
  );
};

const badgeStyle = (color: string): React.CSSProperties => ({
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.25rem',
  padding: '0.15rem 0.4rem',
  borderRadius: '3px',
  fontSize: '0.65rem',
  fontWeight: 700,
  backgroundColor: `${color}18`,
  color: color,
  border: `1px solid ${color}35`,
});
