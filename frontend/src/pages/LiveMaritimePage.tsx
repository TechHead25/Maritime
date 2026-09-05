import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  Radar,
  Search,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Radio,
  FileText,
  Plus,
} from 'lucide-react';
import {
  fetchLiveVessels,
  fetchLiveVesselDetails,
  updateLiveSubscription,
  createInvestigationFromVessel,
  getLiveStreamUrl,
} from '../services/api';
import { VesselIntelligenceModal } from '../components/VesselIntelligenceModal';

interface LiveVessel {
  mmsi: string;
  vessel_name: string;
  vessel_type: string;
  imo?: string;
  flag_country?: string;
  callsign?: string;
  latitude: number;
  longitude: number;
  speed_over_ground_knots: number;
  course_over_ground_deg: number;
  heading_deg: number;
  last_update_utc: string;
  data_age_seconds: number;
  is_stale: boolean;
}

interface VesselDetailedInfo extends LiveVessel {
  trail?: Array<{
    timestamp_utc: string;
    latitude: number;
    longitude: number;
    speed_over_ground_knots: number;
    course_over_ground_deg: number;
  }>;
  has_ais_gaps?: boolean;
  gap_intervals?: Array<[string, string]>;
  waypoints_count?: number;
}

// Region center coordinates
const REGION_COORDINATES: Record<string, { center: [number, number]; zoom: number; label: string }> = {
  SRI_LANKA_SOUTH: {
    center: [6.5, 81.5],
    zoom: 8,
    label: 'Sri Lanka (Southern Shipping Corridor)',
  },
  STRAIT_OF_MALACCA: {
    center: [3.0, 101.5],
    zoom: 8,
    label: 'Strait of Malacca (Chokepoint)',
  },
  BAY_OF_BENGAL: {
    center: [14.5, 87.0],
    zoom: 6,
    label: 'Bay of Bengal (Regional)',
  },
  ARABIAN_SEA: {
    center: [19.0, 71.5],
    zoom: 6,
    label: 'Arabian Sea (West Coast & Gulf)',
  },
  GLOBAL: {
    center: [10.0, 80.0],
    zoom: 4,
    label: 'Global Maritime (High Seas)',
  },
};

// Map controller component to smoothly pan/zoom when center or selected vessel changes
const MapViewController: React.FC<{ center: [number, number]; zoom: number; targetVesselCoords?: [number, number] }> = ({
  center,
  zoom,
  targetVesselCoords,
}) => {
  const map = useMap();
  useEffect(() => {
    if (targetVesselCoords) {
      map.setView(targetVesselCoords, Math.max(zoom, 10), { animate: true });
    } else {
      map.setView(center, zoom, { animate: true });
    }
  }, [center, zoom, targetVesselCoords, map]);
  return null;
};

// High-performance directional vessel marker
const createDirectionalVesselIcon = (type: string, courseDeg: number, isSelected: boolean) => {
  const color =
    type === 'TANKER'
      ? '#f59e0b'
      : type === 'CARGO'
      ? '#38bdf8'
      : type === 'TUG'
      ? '#10b981'
      : type === 'PASSENGER'
      ? '#c084fc'
      : '#94a3b8';

  const size = isSelected ? 18 : 12;

  return L.divIcon({
    className: 'custom-directional-vessel-marker',
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        transform: rotate(${courseDeg}deg);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
      ">
        <svg viewBox="0 0 24 24" width="${size}" height="${size}">
          <polygon points="12,2 22,22 12,17 2,22" fill="${color}" stroke="${isSelected ? '#ffffff' : '#0f172a'}" stroke-width="${isSelected ? 2.5 : 1}" />
        </svg>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

export const LiveMaritimePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryMmsi = searchParams.get('mmsi');

  const [vessels, setVessels] = useState<LiveVessel[]>([]);
  const [selectedMmsi, setSelectedMmsi] = useState<string | null>(queryMmsi);
  const [selectedVessel, setSelectedVessel] = useState<VesselDetailedInfo | null>(null);
  const [region, setRegion] = useState<string>('SRI_LANKA_SOUTH');
  const [vesselTypeFilter, setVesselTypeFilter] = useState<string>('ALL');
  const [minSpeedKnots, setMinSpeedKnots] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [status, setStatus] = useState<string>('DISCONNECTED');
  const [isConfigured, setIsConfigured] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(true);
  const [isChangingRegion, setIsChangingRegion] = useState<boolean>(false);
  const [isCreatingInvestigation, setIsCreatingInvestigation] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Unified Vessel Intelligence Profile Modal state
  const [profileModalMmsi, setProfileModalMmsi] = useState<string | null>(null);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState<boolean>(false);

  const eventSourceRef = useRef<EventSource | null>(null);
  const pollIntervalRef = useRef<any>(null);

  // Synchronize URL query parameter on mount/change
  useEffect(() => {
    if (queryMmsi && queryMmsi !== selectedMmsi) {
      setSelectedMmsi(queryMmsi);
    }
  }, [queryMmsi]);

  // Initial load and periodic polling fallback
  const fetchVesselSnapshot = async () => {
    try {
      const data = await fetchLiveVessels({
        vessel_type: vesselTypeFilter !== 'ALL' ? vesselTypeFilter : undefined,
        min_speed: minSpeedKnots > 0 ? minSpeedKnots : undefined,
      });
      setVessels(data.vessels || []);
      setStatus(data.status || 'DISCONNECTED');
      if (typeof data.configured === 'boolean') {
        setIsConfigured(data.configured);
      }
    } catch (err) {
      console.warn('Live vessels fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVesselSnapshot();
    pollIntervalRef.current = setInterval(fetchVesselSnapshot, 4000);
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [vesselTypeFilter, minSpeedKnots]);

  // Connect to backend Server-Sent Events (SSE) stream
  useEffect(() => {
    const sseUrl = getLiveStreamUrl();
    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'INITIAL_STATUS' || payload.type === 'HEARTBEAT') {
          setStatus(payload.status || 'LIVE');
        } else if (payload.type === 'VESSEL_POSITION' || payload.type === 'VESSEL_UPDATE') {
          const vData = payload.data;
          setVessels((prev) => {
            const idx = prev.findIndex((v) => v.mmsi === vData.mmsi);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = { ...updated[idx], ...vData };
              return updated;
            }
            return [...prev, vData];
          });
        }
      } catch (e) {
        console.warn('Error parsing SSE event payload:', e);
      }
    };

    es.onerror = () => {
      setStatus('DISCONNECTED');
    };

    return () => {
      es.close();
    };
  }, []);

  // Fetch detailed track trail when a vessel is selected
  useEffect(() => {
    if (!selectedMmsi) {
      setSelectedVessel(null);
      return;
    }

    const loadDetails = async () => {
      try {
        const details = await fetchLiveVesselDetails(selectedMmsi);
        setSelectedVessel(details);
      } catch {
        const existing = vessels.find((v) => v.mmsi === selectedMmsi);
        if (existing) {
          setSelectedVessel(existing as VesselDetailedInfo);
        }
      }
    };

    loadDetails();
  }, [selectedMmsi, vessels]);

  const handleSelectVessel = (mmsi: string) => {
    setSelectedMmsi(mmsi);
  };

  const handleOpenProfileModal = (mmsi: string) => {
    setProfileModalMmsi(mmsi);
    setIsProfileModalOpen(true);
  };

  // Handle region subscription change
  const handleRegionChange = async (newRegion: string) => {
    setIsChangingRegion(true);
    setRegion(newRegion);
    try {
      await updateLiveSubscription({ region_name: newRegion });
      await fetchVesselSnapshot();
    } catch (err: any) {
      console.warn('Region update error:', err);
    } finally {
      setIsChangingRegion(false);
    }
  };

  // Create an investigation centered on selected vessel
  const handleCreateInvestigationFromVessel = async () => {
    if (!selectedVessel) return;
    try {
      setIsCreatingInvestigation(true);
      const res = await createInvestigationFromVessel({
        mmsi: selectedVessel.mmsi,
        buffer_degrees: 0.8,
      });
      const caseId = res.case?.id;
      if (caseId) {
        setToastMessage(`Investigation established for ${selectedVessel.vessel_name}. Navigating to workspace...`);
        setTimeout(() => {
          navigate(`/app/investigations/${caseId}`);
        }, 1200);
      }
    } catch (err: any) {
      alert(`Could not create investigation: ${err.message}`);
    } finally {
      setIsCreatingInvestigation(false);
    }
  };

  const mapConfig = REGION_COORDINATES[region] || REGION_COORDINATES.SRI_LANKA_SOUTH;

  // Filter vessels based on local search query
  const filteredVessels = vessels.filter((v) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      v.vessel_name.toLowerCase().includes(q) ||
      v.mmsi.includes(q) ||
      (v.imo && v.imo.includes(q))
    );
  });

  const selectedVesselCoords: [number, number] | undefined = selectedVessel
    ? [selectedVessel.latitude, selectedVessel.longitude]
    : undefined;

  // Real-time status styling
  const getStatusIndicator = () => {
    switch (status) {
      case 'LIVE':
      case 'STREAMING':
        return { label: 'LIVE AIS STREAMING', color: '#10b981', dotColor: '#34d399' };
      case 'CONNECTING':
        return { label: 'CONNECTING...', color: '#f59e0b', dotColor: '#fbbf24' };
      case 'STALE':
        return { label: 'IDLE (CONNECTED)', color: '#38bdf8', dotColor: '#60a5fa' };
      default:
        return {
          label: isConfigured ? 'CONNECTING...' : 'UNCONFIGURED',
          color: isConfigured ? '#f59e0b' : '#94a3b8',
          dotColor: isConfigured ? '#fbbf24' : '#64748b',
        };
    }
  };

  const statusIndicator = getStatusIndicator();

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      maxWidth: '1800px',
      margin: '0 auto',
      minHeight: 'calc(100vh - 120px)',
    }}>
      {/* Toast Notice */}
      {toastMessage && (
        <div style={{
          backgroundColor: 'rgba(16, 185, 129, 0.2)',
          border: '1px solid #10b981',
          color: '#34d399',
          padding: '0.65rem 1rem',
          borderRadius: '6px',
          fontSize: '0.80rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <CheckCircle2 size={16} /> {toastMessage}
        </div>
      )}

      {/* Top Filter Bar */}
      <div style={{
        backgroundColor: '#0c1322',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        padding: '0.75rem 1.25rem',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '1rem',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Radar size={20} color="#38bdf8" />
            <h1 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
              Live Maritime Tracking
            </h1>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Region:</span>
            <select
              value={region}
              onChange={(e) => handleRegionChange(e.target.value)}
              disabled={isChangingRegion}
              style={selectStyle}
            >
              {Object.entries(REGION_COORDINATES).map(([key, cfg]) => (
                <option key={key} value={key}>
                  {cfg.label}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Type:</span>
            <select
              value={vesselTypeFilter}
              onChange={(e) => setVesselTypeFilter(e.target.value)}
              style={selectStyle}
            >
              <option value="ALL">All Vessel Types</option>
              <option value="TANKER">Tankers</option>
              <option value="CARGO">Cargo Vessels</option>
              <option value="TUG">Tugs & Towing</option>
              <option value="PASSENGER">Passenger</option>
              <option value="OTHER">Other / Unspecified</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Min Speed:</span>
            <input
              type="number"
              min="0"
              max="50"
              value={minSpeedKnots}
              onChange={(e) => setMinSpeedKnots(Number(e.target.value))}
              style={{ ...selectStyle, width: '60px' }}
            />
            <span style={{ fontSize: '0.72rem', color: '#64748b' }}>kn</span>
          </div>

          <div style={{ position: 'relative' }}>
            <Search size={14} color="#64748b" style={{ position: 'absolute', left: 8, top: 9 }} />
            <input
              type="text"
              placeholder="Search Name or MMSI..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                ...selectStyle,
                paddingLeft: '1.75rem',
                width: '180px',
              }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            backgroundColor: 'rgba(15, 23, 42, 0.8)',
            border: `1px solid ${statusIndicator.color}`,
            borderRadius: '4px',
            padding: '0.25rem 0.65rem',
            fontSize: '0.70rem',
            fontWeight: 700,
            color: statusIndicator.color,
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: statusIndicator.dotColor,
              display: 'inline-block',
              animation: (status === 'STREAMING' || status === 'LIVE') ? 'pulse 2s infinite' : 'none',
            }} />
            {statusIndicator.label}
          </div>

          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Active: <strong style={{ color: '#f8fafc' }}>{filteredVessels.length}</strong> vessels
          </div>

          <button
            onClick={fetchVesselSnapshot}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              color: '#94a3b8',
              borderRadius: '4px',
              padding: '0.35rem 0.65rem',
              fontSize: '0.75rem',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={12} className={loading ? 'spin-icon' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Dynamic Map Area */}
      <div style={{
        position: 'relative',
        height: selectedVessel ? 'calc(100vh - 460px)' : 'calc(100vh - 260px)',
        minHeight: '400px',
        borderRadius: '8px',
        overflow: 'hidden',
        border: '1px solid #1e293b',
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
      }}>
        <MapContainer
          center={mapConfig.center}
          zoom={mapConfig.zoom}
          style={{ height: '100%', width: '100%', backgroundColor: '#060d17' }}
        >
          <MapViewController
            center={mapConfig.center}
            zoom={mapConfig.zoom}
            targetVesselCoords={selectedVesselCoords}
          />

          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {/* Vessel Markers */}
          {filteredVessels.map((v) => {
            const isSelected = selectedMmsi === v.mmsi;
            const icon = createDirectionalVesselIcon(v.vessel_type, v.course_over_ground_deg, isSelected);

            return (
              <Marker
                key={v.mmsi}
                position={[v.latitude, v.longitude]}
                icon={icon}
                eventHandlers={{
                  click: () => handleSelectVessel(v.mmsi),
                }}
              >
                <Popup>
                  <div style={{ color: '#0f172a', fontSize: '0.75rem', lineHeight: 1.4 }}>
                    <strong style={{ fontSize: '0.85rem' }}>{v.vessel_name}</strong>
                    <div>Type: <strong>{v.vessel_type}</strong></div>
                    <div>MMSI: {v.mmsi}</div>
                    {v.imo && <div>IMO: {v.imo}</div>}
                    <div>Speed: {v.speed_over_ground_knots} kn</div>
                    <div>Course: {v.course_over_ground_deg}°</div>
                    <div style={{ fontSize: '0.70rem', color: '#64748b', marginTop: '0.25rem' }}>
                      Data Age: {v.data_age_seconds}s ({v.data_age_seconds < 300 ? 'LIVE POSITION' : 'RECENT POSITION'})
                    </div>
                    <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => handleSelectVessel(v.mmsi)}
                        style={{
                          backgroundColor: '#0284c7',
                          color: '#fff',
                          border: 'none',
                          borderRadius: '4px',
                          padding: '0.25rem 0.5rem',
                          cursor: 'pointer',
                          fontSize: '0.70rem',
                        }}
                      >
                        View Track
                      </button>
                      <button
                        onClick={() => handleOpenProfileModal(v.mmsi)}
                        style={{
                          backgroundColor: '#334155',
                          color: '#f8fafc',
                          border: 'none',
                          borderRadius: '4px',
                          padding: '0.25rem 0.5rem',
                          cursor: 'pointer',
                          fontSize: '0.70rem',
                        }}
                      >
                        Profile
                      </button>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {/* Detailed Waypoint Trail for Selected Vessel */}
          {selectedVessel?.trail && selectedVessel.trail.length > 1 && (
            <Polyline
              positions={selectedVessel.trail.map((wp) => [wp.latitude, wp.longitude])}
              pathOptions={{
                color: selectedVessel.vessel_type === 'TANKER' ? '#f59e0b' : '#38bdf8',
                weight: 3,
                dashArray: selectedVessel.has_ais_gaps ? '6, 6' : undefined,
                opacity: 0.85,
              }}
            />
          )}
        </MapContainer>

        {/* Empty Overlay */}
        {filteredVessels.length === 0 && !loading && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            border: '1px solid #334155',
            borderRadius: '8px',
            padding: '1.5rem 2rem',
            textAlign: 'center',
            maxWidth: '480px',
            zIndex: 1000,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
          }}>
            <Radio size={28} color="#94a3b8" style={{ margin: '0 auto 0.75rem' }} />
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', margin: '0 0 0.4rem' }}>
              {!isConfigured
                ? 'Live AIS Stream Unconfigured'
                : status === 'DISCONNECTED'
                ? 'Connecting to Live AIS Stream...'
                : 'Awaiting Transponder Signals'}
            </h3>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: 0, lineHeight: 1.4 }}>
              {!isConfigured
                ? 'Server-side AIS streaming credentials (AISSTREAM_API_KEY) are not configured. The platform strictly enforces zero synthetic data generation; no simulated vessels are shown.'
                : status === 'DISCONNECTED'
                ? 'Connecting to the live satellite AIS telemetry feed. Vessels will appear in real time once transponders broadcast.'
                : `Live stream is connected. Awaiting position reports for ${mapConfig.label}. Vessels will appear in real time as transponders broadcast.`}
            </p>
          </div>
        )}
      </div>

      {/* Selected Vessel Telemetry & Identity Drawer */}
      {selectedVessel && (
        <div style={{
          backgroundColor: '#0c1322',
          border: '1px solid #1e293b',
          borderRadius: '8px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          overflowY: 'auto',
        }}>
            {/* Drawer Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    color: selectedVessel.vessel_type === 'TANKER' ? '#f59e0b' : '#38bdf8',
                    letterSpacing: '0.04em',
                  }}>
                    {selectedVessel.vessel_type}
                  </span>

                  {/* Distinct Real-Time Status Tag */}
                  <span style={{
                    fontSize: '0.62rem',
                    fontWeight: 700,
                    padding: '0.1rem 0.4rem',
                    borderRadius: '3px',
                    backgroundColor: selectedVessel.data_age_seconds < 300 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                    color: selectedVessel.data_age_seconds < 300 ? '#34d399' : '#fbbf24',
                    border: `1px solid ${selectedVessel.data_age_seconds < 300 ? '#10b981' : '#f59e0b'}`,
                  }}>
                    {selectedVessel.data_age_seconds < 300 ? 'LIVE POSITION' : 'RECENT POSITION'}
                  </span>
                </div>

                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', margin: '0.2rem 0' }}>
                  {selectedVessel.vessel_name}
                </h2>
                <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'monospace' }}>
                  MMSI: {selectedVessel.mmsi} {selectedVessel.imo ? `• IMO: ${selectedVessel.imo}` : ''}
                </div>
              </div>

              <button
                onClick={() => setSelectedMmsi(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#64748b',
                  cursor: 'pointer',
                  fontSize: '1.1rem',
                  padding: '0.2rem 0.4rem',
                }}
              >
                ✕
              </button>
            </div>

            {/* Bridge Actions: Live -> Investigation */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <button
                onClick={() => {
                  setProfileModalMmsi(selectedVessel.mmsi);
                  setIsProfileModalOpen(true);
                }}
                style={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  color: '#38bdf8',
                  padding: '0.5rem',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.4rem',
                  transition: 'all 0.15s ease',
                }}
              >
                <FileText size={14} /> Open Vessel Intelligence Profile
              </button>

              <button
                onClick={handleCreateInvestigationFromVessel}
                disabled={isCreatingInvestigation}
                style={{
                  backgroundColor: '#0284c7',
                  border: 'none',
                  color: '#ffffff',
                  padding: '0.5rem',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: isCreatingInvestigation ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.4rem',
                  boxShadow: '0 2px 10px rgba(2, 132, 199, 0.4)',
                  transition: 'all 0.15s ease',
                }}
              >
                {isCreatingInvestigation ? <RefreshCw size={14} className="spin-icon" /> : <Plus size={14} />}
                {isCreatingInvestigation ? 'Creating Investigation...' : 'Create Investigation Around Vessel'}
              </button>
            </div>

            {/* Live Kinematics Matrix */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '0.65rem',
              backgroundColor: '#111827',
              padding: '0.85rem',
              borderRadius: '6px',
              border: '1px solid #1e293b',
              fontSize: '0.78rem',
            }}>
              <div>
                <span style={labelStyle}>SPEED OVER GROUND</span>
                <span style={{ color: '#f8fafc', fontFamily: 'monospace', fontWeight: 600, fontSize: '0.90rem' }}>
                  {selectedVessel.speed_over_ground_knots} kn
                </span>
              </div>

              <div>
                <span style={labelStyle}>COURSE OVER GROUND</span>
                <span style={{ color: '#f8fafc', fontFamily: 'monospace', fontWeight: 600, fontSize: '0.90rem' }}>
                  {selectedVessel.course_over_ground_deg}°
                </span>
              </div>

              <div>
                <span style={labelStyle}>TRUE HEADING</span>
                <span style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>
                  {selectedVessel.heading_deg}°
                </span>
              </div>

              <div>
                <span style={labelStyle}>DATA AGE & PROVENANCE</span>
                <span style={{ color: selectedVessel.data_age_seconds < 30 ? '#34d399' : '#fbbf24', fontWeight: 600 }}>
                  {selectedVessel.data_age_seconds < 60
                    ? `${Math.round(selectedVessel.data_age_seconds)}s ago`
                    : `${(selectedVessel.data_age_seconds / 60).toFixed(1)}m ago`}
                </span>
              </div>

              <div style={{ gridColumn: '1 / -1' }}>
                <span style={labelStyle}>CURRENT WGS84 COORDINATES</span>
                <span style={{ color: '#38bdf8', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {selectedVessel.latitude.toFixed(5)}°N, {selectedVessel.longitude.toFixed(5)}°E
                </span>
              </div>
            </div>

            {/* AIS Data Quality & Transponder Continuity */}
            <div style={{
              backgroundColor: '#111827',
              border: '1px solid #1e293b',
              borderRadius: '6px',
              padding: '0.85rem',
              fontSize: '0.78rem',
            }}>
              <span style={labelStyle}>AIS TRANSPONDER INTEGRITY</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.35rem' }}>
                {selectedVessel.has_ais_gaps ? (
                  <span style={{ color: '#f87171', display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 600 }}>
                    <AlertTriangle size={14} /> Transponder Dark Gaps Detected (&gt;1h)
                  </span>
                ) : (
                  <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 600 }}>
                    <CheckCircle2 size={14} /> Continuous Transmission Verified
                  </span>
                )}
              </div>
              <div style={{ fontSize: '0.70rem', color: '#64748b', marginTop: '0.35rem' }}>
                Historical Track Store: {selectedVessel.waypoints_count || 1} buffered waypoints
              </div>
            </div>

            {/* Vessel Particulars */}
            <div style={{
              backgroundColor: '#111827',
              border: '1px solid #1e293b',
              borderRadius: '6px',
              padding: '0.85rem',
              fontSize: '0.78rem',
            }}>
              <span style={labelStyle}>VESSEL IDENTITY & REGISTRY</span>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.4rem' }}>
                <div>
                  <span style={{ color: '#64748b', fontSize: '0.68rem', display: 'block' }}>FLAG STATE</span>
                  <strong style={{ color: '#f8fafc' }}>{selectedVessel.flag_country || 'Unknown'}</strong>
                </div>
                <div>
                  <span style={{ color: '#64748b', fontSize: '0.68rem', display: 'block' }}>CALL SIGN</span>
                  <strong style={{ color: '#f8fafc' }}>{selectedVessel.callsign || 'N/A'}</strong>
                </div>
              </div>
            </div>
          </div>
        )}

      {/* Unified Vessel Profile Modal */}
      <VesselIntelligenceModal
        mmsi={profileModalMmsi}
        isOpen={isProfileModalOpen}
        onClose={() => {
          setIsProfileModalOpen(false);
          setProfileModalMmsi(null);
        }}
      />
    </div>
  );
};

const selectStyle: React.CSSProperties = {
  backgroundColor: '#131b2e',
  border: '1px solid #1e293b',
  color: '#f8fafc',
  padding: '0.30rem 0.65rem',
  borderRadius: '4px',
  fontSize: '0.75rem',
  outline: 'none',
  cursor: 'pointer',
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.65rem',
  fontWeight: 700,
  color: '#64748b',
  display: 'block',
  marginBottom: '0.15rem',
  letterSpacing: '0.03em',
};
