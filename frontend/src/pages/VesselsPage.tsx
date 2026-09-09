import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  RefreshCw,
} from 'lucide-react';
import { fetchCases, fetchCaseDetails } from '../services/api';
import { VesselTrack } from '../types';

interface VesselWithCaseMeta extends VesselTrack {
  associatedCaseTitles: string[];
}

export const VesselsPage: React.FC = () => {
  const navigate = useNavigate();
  const [vessels, setVessels] = useState<VesselWithCaseMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [gapsOnly, setGapsOnly] = useState(false);

  const loadVessels = async () => {
    setLoading(true);
    try {
      const cases = await fetchCases();
      const map = new Map<string, VesselWithCaseMeta>();

      for (const c of cases.slice(0, 10)) {
        try {
          const details = await fetchCaseDetails(c.id);
          if (details.vessel_tracks) {
            details.vessel_tracks.forEach((t) => {
              if (map.has(t.mmsi)) {
                const existing = map.get(t.mmsi)!;
                if (!existing.associatedCaseTitles.includes(c.title)) {
                  existing.associatedCaseTitles.push(c.title);
                }
              } else {
                map.set(t.mmsi, {
                  ...t,
                  associatedCaseTitles: [c.title],
                });
              }
            });
          }
        } catch (e) {
          console.warn('Error loading vessels for case:', c.id, e);
        }
      }

      setVessels(Array.from(map.values()));
    } catch (err) {
      console.error('Failed to load vessel registry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVessels();
  }, []);

  const filteredVessels = vessels.filter((v) => {
    const matchesSearch =
      v.vessel_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.mmsi.includes(searchTerm) ||
      (v.flag_country && v.flag_country.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesType = typeFilter === 'ALL' || v.vessel_type === typeFilter;
    const matchesGap = gapsOnly ? v.has_ais_gaps : true;

    return matchesSearch && matchesType && matchesGap;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            Vessel Intelligence Registry
          </h1>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.25rem', marginBottom: 0 }}>
            Catalog of all vessels intercepted in operational areas, historical trajectory records, and transponder anomalies.
          </p>
        </div>

        <button
          onClick={loadVessels}
          style={{
            backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
            border: '1px solid var(--glass-border)',
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
          <RefreshCw size={14} /> Refresh Registry
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        alignItems: 'center',
        backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
        padding: '0.85rem 1rem',
        borderRadius: '8px',
        border: '1px solid var(--glass-border)',
        flexWrap: 'wrap',
      }}>
        {/* Search */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
          border: '1px solid var(--glass-border)',
          borderRadius: '6px',
          padding: '0.4rem 0.75rem',
          flex: '1 1 260px',
        }}>
          <Search size={15} color="#64748b" />
          <input
            type="text"
            placeholder="Search by vessel name, MMSI, or flag..."
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

        {/* Type Filter */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          style={{
            backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
            border: '1px solid var(--glass-border)',
            color: '#f8fafc',
            fontSize: '0.80rem',
            borderRadius: '6px',
            padding: '0.4rem 0.75rem',
            outline: 'none',
          }}
        >
          <option value="ALL">All Vessel Types</option>
          <option value="TANKER">Tankers</option>
          <option value="CARGO">Cargo</option>
          <option value="TUG">Tugs</option>
          <option value="OTHER">Other</option>
        </select>

        {/* Gaps Toggle */}
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.80rem', color: '#cbd5e1', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={gapsOnly}
            onChange={(e) => setGapsOnly(e.target.checked)}
            style={{ accentColor: '#0284c7' }}
          />
          <span>Only Anomaly / Gaps</span>
        </label>

        <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: 'auto' }}>
          Showing {filteredVessels.length} of {vessels.length} vessels
        </span>
      </div>

      {/* Vessels Data Table */}
      <div style={{
        backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
        border: '1px solid var(--glass-border)',
        borderRadius: '8px',
        overflow: 'hidden',
      }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#94a3b8' }}>
            Compiling vessel telemetry across cases...
          </div>
        ) : filteredVessels.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#64748b' }}>
            No vessel records match your search criteria.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.80rem' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)', borderBottom: '1px solid var(--glass-border)', color: '#64748b', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>VESSEL NAME & MMSI</th>
                  <th style={{ padding: '0.75rem 1rem' }}>TYPE</th>
                  <th style={{ padding: '0.75rem 1rem' }}>FLAG</th>
                  <th style={{ padding: '0.75rem 1rem' }}>WAYPOINTS</th>
                  <th style={{ padding: '0.75rem 1rem' }}>AIS CONTINUITY</th>
                  <th style={{ padding: '0.75rem 1rem' }}>LAST KNOWN POSITION</th>
                  <th style={{ padding: '0.75rem 1rem' }}>ASSOCIATED INCIDENTS</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {filteredVessels.map((v) => {
                  const latestWp = v.waypoints?.[v.waypoints.length - 1];

                  return (
                    <tr
                      key={v.mmsi}
                      style={{ borderBottom: '1px solid var(--glass-border)', transition: 'background 0.15s' }}
                    >
                      {/* Name & MMSI */}
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <div style={{ fontWeight: 600, color: '#f8fafc' }}>{v.vessel_name}</div>
                        <div style={{ fontSize: '0.70rem', color: '#64748b', fontFamily: 'monospace' }}>
                          MMSI: {v.mmsi}
                        </div>
                      </td>

                      {/* Type */}
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{
                          fontSize: '0.70rem',
                          fontWeight: 700,
                          color: v.vessel_type === 'TANKER' ? '#f59e0b' : '#38bdf8',
                        }}>
                          {v.vessel_type}
                        </span>
                      </td>

                      {/* Flag */}
                      <td style={{ padding: '0.75rem 1rem', color: '#cbd5e1' }}>
                        {v.flag_country || 'Unknown'}
                      </td>

                      {/* Waypoints */}
                      <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace', color: '#94a3b8' }}>
                        {v.waypoints.length} pings
                      </td>

                      {/* Continuity */}
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{
                          padding: '0.15rem 0.45rem',
                          borderRadius: '4px',
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          backgroundColor: v.has_ais_gaps ? 'rgba(239, 68, 68, 0.12)' : 'rgba(16, 185, 129, 0.12)',
                          color: v.has_ais_gaps ? '#f87171' : '#34d399',
                          border: `1px solid ${v.has_ais_gaps ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                        }}>
                          {v.has_ais_gaps ? 'GAP DETECTED' : 'CONTINUOUS'}
                        </span>
                      </td>

                      {/* Position */}
                      <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace', color: '#cbd5e1', fontSize: '0.75rem' }}>
                        {latestWp
                          ? `${latestWp.latitude.toFixed(3)}°N, ${latestWp.longitude.toFixed(3)}°E`
                          : 'N/A'}
                      </td>

                      {/* Incidents */}
                      <td style={{ padding: '0.75rem 1rem', color: '#94a3b8', fontSize: '0.75rem' }}>
                        {v.associatedCaseTitles.join(', ')}
                      </td>

                      {/* Action */}
                      <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                        <button
                          onClick={() => navigate('/app/live')}
                          style={{
                            backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                            border: '1px solid var(--glass-border)',
                            color: '#38bdf8',
                            padding: '0.3rem 0.65rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          View on Map
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
    </div>
  );
};
