import React from 'react';
import { Polyline, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { VesselTrack, CandidateVessel, AttributionScore } from '../types';
import { interpolateVesselPosition } from '../utils/timelineUtils';

interface Props {
  tracks: VesselTrack[];
  candidates?: CandidateVessel[];
  attributionScores?: AttributionScore[];
  selectedCandidateMmsi?: string;
  onSelectCandidate?: (mmsi: string) => void;
  visible?: boolean;
  currentTime?: Date;
}

const RANK_COLORS: Record<number, string> = {
  1: '#ef4444', // Rank 1 (Red / Highest Candidate)
  2: '#f59e0b', // Rank 2 (Gold / High Risk)
  3: '#a855f7', // Rank 3 (Purple)
  4: '#06b6d4', // Rank 4 (Cyan)
  5: '#10b981', // Rank 5 (Emerald)
};

const vesselLiveMarkerIcon = (color: string, isSelected: boolean, courseDeg: number, isInGap: boolean) => L.divIcon({
  className: 'live-vessel-marker',
  html: `
    <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;">
      ${isSelected ? `<div style="position: absolute; width: 32px; height: 32px; border-radius: 50%; background: ${color}33; border: 1.5px solid ${color}; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>` : ''}
      <div style="
        width: 18px;
        height: 18px;
        background: ${isInGap ? '#334155' : color};
        border: 2px solid ${isInGap ? '#ef4444' : '#ffffff'};
        border-radius: 50% 50% 50% 0;
        transform: rotate(${courseDeg - 45}deg);
        box-shadow: 0 0 10px ${isInGap ? '#ef4444' : color};
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        ${isInGap ? '<div style="width: 4px; height: 4px; background: #ef4444; border-radius: 50%;"></div>' : ''}
      </div>
    </div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

export const VesselTrackLayer: React.FC<Props> = ({
  tracks,
  candidates = [],
  attributionScores = [],
  selectedCandidateMmsi,
  onSelectCandidate,
  visible = true,
  currentTime,
}) => {
  if (!visible || !tracks || tracks.length === 0) return null;

  const candidateMap = new Map(candidates.map((c) => [c.mmsi, c]));
  const scoreMap = new Map(attributionScores.map((s) => [s.mmsi, s]));

  return (
    <>
      {tracks.map((track, idx) => {
        const cand = candidateMap.get(track.mmsi);
        const score = scoreMap.get(track.mmsi);
        const isSelected = selectedCandidateMmsi === track.mmsi;
        const color = (score?.rank && RANK_COLORS[score.rank]) || RANK_COLORS[(idx % 5) + 1] || '#94a3b8';

        // Interpolate live position if currentTime is given
        const liveState = currentTime
          ? interpolateVesselPosition(track.waypoints, currentTime, track.gap_intervals)
          : null;

        const currentMs = currentTime ? currentTime.getTime() : Infinity;

        // Split trajectory into past (solid) and future (dimmed)
        const pastWaypoints = track.waypoints.filter(w => new Date(w.timestamp).getTime() <= currentMs);
        const futureWaypoints = track.waypoints.filter(w => new Date(w.timestamp).getTime() >= currentMs);

        const allLatLngs: [number, number][] = track.waypoints.map((w) => [w.latitude, w.longitude]);
        const pastLatLngs: [number, number][] = pastWaypoints.map((w) => [w.latitude, w.longitude]);
        if (liveState) {
          pastLatLngs.push([liveState.latitude, liveState.longitude]);
        }

        const futureLatLngs: [number, number][] = [];
        if (liveState) {
          futureLatLngs.push([liveState.latitude, liveState.longitude]);
        }
        futureWaypoints.forEach(w => futureLatLngs.push([w.latitude, w.longitude]));

        return (
          <React.Fragment key={track.id || track.mmsi}>
            {/* If no time given, render full track */}
            {!currentTime && (
              <Polyline
                positions={allLatLngs}
                pathOptions={{
                  color: color,
                  weight: isSelected ? 4.5 : 2.5,
                  opacity: isSelected ? 1.0 : 0.75,
                  dashArray: track.has_ais_gaps ? '6, 4' : undefined,
                }}
                eventHandlers={{
                  click: () => onSelectCandidate && onSelectCandidate(track.mmsi),
                }}
              />
            )}

            {/* Past Synchronized Breadcrumb Track */}
            {currentTime && pastLatLngs.length > 1 && (
              <Polyline
                positions={pastLatLngs}
                pathOptions={{
                  color: color,
                  weight: isSelected ? 4.0 : 2.2,
                  opacity: isSelected ? 1.0 : 0.85,
                }}
                eventHandlers={{
                  click: () => onSelectCandidate && onSelectCandidate(track.mmsi),
                }}
              />
            )}

            {/* Future Dimmed Track */}
            {currentTime && futureLatLngs.length > 1 && (
              <Polyline
                positions={futureLatLngs}
                pathOptions={{
                  color: color,
                  weight: 1.5,
                  opacity: 0.35,
                  dashArray: '4, 4',
                }}
              />
            )}

            {/* Live Synchronized Vessel Position Marker */}
            {liveState && liveState.is_visible && (
              <Marker
                position={[liveState.latitude, liveState.longitude]}
                icon={vesselLiveMarkerIcon(color, isSelected, liveState.course_deg, liveState.is_in_gap)}
                eventHandlers={{
                  click: () => onSelectCandidate && onSelectCandidate(track.mmsi),
                }}
              >
                <Popup>
                  <div style={{ fontSize: '0.82rem', lineHeight: 1.5, minWidth: '220px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
                      <strong style={{ color: color, fontSize: '0.9rem' }}>{track.vessel_name}</strong>
                      {score && (
                        <span style={{
                          backgroundColor: '#0f172a',
                          color: score.rank === 1 ? '#ef4444' : '#f8fafc',
                          padding: '0.15rem 0.45rem',
                          borderRadius: '4px',
                          fontWeight: 700,
                          fontSize: '0.75rem',
                          border: '1px solid #334155',
                        }}>
                          #{score.rank} • {score.total_score.toFixed(1)}/100
                        </span>
                      )}
                    </div>

                    <div><strong>MMSI:</strong> {track.mmsi}</div>
                    <div><strong>Type:</strong> {track.vessel_type} ({track.flag_country})</div>
                    <div><strong>Current Speed:</strong> {liveState.speed_knots.toFixed(1)} kts</div>
                    <div><strong>Heading (COG):</strong> {liveState.course_deg.toFixed(0)}°</div>
                    <div><strong>Position:</strong> {liveState.latitude.toFixed(4)}°N, {liveState.longitude.toFixed(4)}°E</div>

                    {liveState.is_in_gap ? (
                      <div style={{ marginTop: '0.4rem', color: '#ef4444', fontWeight: 700, backgroundColor: '#ef444420', padding: '0.2rem 0.4rem', borderRadius: '4px' }}>
                        ⚠️ AIS TRANSPONDER OUTAGE IN EFFECT
                      </div>
                    ) : (
                      <div style={{ marginTop: '0.4rem', color: '#10b981', fontSize: '0.75rem' }}>
                        ✓ AIS Broadcasting Active
                      </div>
                    )}

                    {cand && (
                      <div style={{ marginTop: '0.4rem', paddingTop: '0.4rem', borderTop: '1px solid #334155', fontSize: '0.75rem', color: '#cbd5e1' }}>
                        <strong>CPA Distance:</strong> {cand.closest_point_of_approach_km.toFixed(2)} km
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            )}
          </React.Fragment>
        );
      })}
    </>
  );
};
