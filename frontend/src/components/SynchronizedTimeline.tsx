import React, { useEffect, useRef } from 'react';
import { ProbabilityCloud, ReleaseWindow, VesselTrack } from '../types';
import {
  formatUTCTimestamp,
  calculateRelativeHours,
  isTimestampInReleaseWindow,
  findClosestProbabilityCloud,
} from '../utils/timelineUtils';

interface Props {
  startTime: Date;
  endTime: Date;
  currentTime: Date;
  onTimeChange: (newTime: Date) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  playbackSpeed: number;
  onSpeedChange: (speed: number) => void;
  releaseWindow?: ReleaseWindow;
  clouds?: ProbabilityCloud[];
  vesselTracks?: VesselTrack[];
  selectedCandidateMmsi?: string;
  onSelectCandidate?: (mmsi: string) => void;
  followMmsi?: string;
  onToggleFollow?: (mmsi: string | undefined) => void;
  onReset: () => void;
}

export const SynchronizedTimeline: React.FC<Props> = ({
  startTime,
  endTime,
  currentTime,
  onTimeChange,
  isPlaying,
  onTogglePlay,
  playbackSpeed,
  onSpeedChange,
  releaseWindow,
  clouds = [],
  vesselTracks = [],
  selectedCandidateMmsi,
  onSelectCandidate,
  followMmsi,
  onToggleFollow,
  onReset,
}) => {
  const timerRef = useRef<any>(null);

  const startMs = startTime.getTime();
  const endMs = endTime.getTime();
  const currentMs = currentTime.getTime();
  const totalDurationMs = Math.max(1, endMs - startMs);

  const progressPercent = Math.max(0, Math.min(100, ((currentMs - startMs) / totalDurationMs) * 100));

  // Release window interval percentage on slider
  let releaseStartPercent = 0;
  let releaseEndPercent = 0;
  if (releaseWindow) {
    const rwStartMs = new Date(releaseWindow.estimated_start_time).getTime();
    const rwEndMs = new Date(releaseWindow.estimated_end_time).getTime();
    releaseStartPercent = Math.max(0, Math.min(100, ((rwStartMs - startMs) / totalDurationMs) * 100));
    releaseEndPercent = Math.max(0, Math.min(100, ((rwEndMs - startMs) / totalDurationMs) * 100));
  }

  // Animation Loop
  useEffect(() => {
    if (isPlaying) {
      // 50ms tick: advances simulation time by (playbackSpeed * 1 minute)
      timerRef.current = setInterval(() => {
        const nextMs = currentMs + (playbackSpeed * 60 * 1000);
        if (nextMs >= endMs) {
          onTimeChange(new Date(endMs));
          onTogglePlay(); // pause at end
        } else {
          onTimeChange(new Date(nextMs));
        }
      }, 50);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playbackSpeed, endMs, currentMs, onTimeChange, onTogglePlay]);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const frac = parseFloat(e.target.value) / 100;
    const targetMs = startMs + frac * totalDurationMs;
    onTimeChange(new Date(targetMs));
  };

  const handleStep = (deltaMinutes: number) => {
    const targetMs = Math.max(startMs, Math.min(endMs, currentMs + deltaMinutes * 60 * 1000));
    onTimeChange(new Date(targetMs));
  };

  const handleJumpToReleasePeak = () => {
    if (releaseWindow) {
      onTimeChange(new Date(releaseWindow.peak_probability_time));
    }
  };

  const isInsideRelease = isTimestampInReleaseWindow(currentTime, releaseWindow);
  const isAtObs = Math.abs(currentMs - endMs) < 60 * 1000;
  const closestCloud = findClosestProbabilityCloud(clouds, currentTime);

  return (
    <div style={{
      backgroundColor: '#090d16',
      borderTop: '1px solid #1e293b',
      borderBottom: '1px solid #1e293b',
      borderRadius: '8px',
      padding: '0.9rem 1.25rem',
      marginBottom: '1rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.4)',
    }}>
      {/* Top Row: Clock, Relative Time & Status Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '1.15rem' }}>⏱</span>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontFamily: 'monospace', fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '0.04em' }}>
                {formatUTCTimestamp(currentTime)}
              </span>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#38bdf8', backgroundColor: '#0c4a6e40', padding: '0.15rem 0.45rem', borderRadius: '4px', border: '1px solid #0284c7' }}>
                {calculateRelativeHours(currentTime, endTime)}
              </span>
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '2px' }}>
              Simulation Horizon: {formatUTCTimestamp(startTime).slice(11, 16)} UTC ➔ {formatUTCTimestamp(endTime).slice(11, 16)} UTC
            </div>
          </div>
        </div>

        {/* Dynamic Status Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {isInsideRelease && (
            <span style={{
              fontSize: '0.70rem',
              fontWeight: 700,
              backgroundColor: '#78350f40',
              color: '#f59e0b',
              border: '1px solid #f59e0b',
              padding: '0.2rem 0.55rem',
              borderRadius: '4px',
              animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }}>
              🚨 ACTIVE RELEASE WINDOW
            </span>
          )}
          {isAtObs && (
            <span style={{
              fontSize: '0.70rem',
              fontWeight: 700,
              backgroundColor: '#ef444425',
              color: '#ef4444',
              border: '1px solid #ef4444',
              padding: '0.2rem 0.55rem',
              borderRadius: '4px',
            }}>
              🛰 SAR OBSERVATION PASS
            </span>
          )}
          {closestCloud && (
            <span style={{
              fontSize: '0.70rem',
              color: '#94a3b8',
              backgroundColor: '#1e293b',
              padding: '0.2rem 0.50rem',
              borderRadius: '4px',
              border: '1px solid #334155',
            }}>
              Drift Swarm: 1σ Spread ±{closestCloud.cloud.dispersion_radius_km.toFixed(2)} km
            </span>
          )}
        </div>
      </div>

      {/* Middle Row: Custom Range Slider with Release Window Band */}
      <div style={{ position: 'relative', width: '100%', paddingTop: '4px', paddingBottom: '4px' }}>
        {/* Release Window Track Highlight */}
        {releaseWindow && (
          <div
            title={`Release Window: ${new Date(releaseWindow.estimated_start_time).toUTCString().slice(17, 22)} - ${new Date(releaseWindow.estimated_end_time).toUTCString().slice(17, 22)} UTC`}
            style={{
              position: 'absolute',
              top: '8px',
              left: `${releaseStartPercent}%`,
              width: `${Math.max(1, releaseEndPercent - releaseStartPercent)}%`,
              height: '8px',
              backgroundColor: '#f59e0b55',
              border: '1px solid #f59e0b',
              borderRadius: '3px',
              pointerEvents: 'none',
              zIndex: 1,
            }}
          />
        )}

        <input
          type="range"
          min={0}
          max={100}
          step={0.1}
          value={progressPercent}
          onChange={handleSliderChange}
          style={{
            position: 'relative',
            zIndex: 2,
            width: '100%',
            height: '8px',
            borderRadius: '4px',
            accentColor: isInsideRelease ? '#f59e0b' : '#38bdf8',
            cursor: 'pointer',
            background: 'transparent',
          }}
        />

        {/* Timeline Ticks & Labels */}
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#64748b', marginTop: '3px' }}>
          <span>{formatUTCTimestamp(startTime).slice(11, 16)} UTC (T-14.5h)</span>
          {releaseWindow && (
            <span style={{ color: '#f59e0b', fontWeight: 600 }}>
              ★ Release Peak ({new Date(releaseWindow.peak_probability_time).toUTCString().slice(17, 22)} UTC)
            </span>
          )}
          <span>{formatUTCTimestamp(endTime).slice(11, 16)} UTC (T_obs)</span>
        </div>
      </div>

      {/* Bottom Row: Playback Controls, Speed, Follow Vessel */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
          {/* Jump to Start */}
          <button
            onClick={() => onTimeChange(new Date(startMs))}
            title="Jump to Horizon Start"
            style={{
              fontSize: '0.75rem',
              backgroundColor: '#1e293b',
              color: '#cbd5e1',
              border: '1px solid #334155',
              borderRadius: '4px',
              padding: '0.25rem 0.55rem',
              cursor: 'pointer',
            }}
          >
            ⏮ Start
          </button>

          {/* Step Back 15m */}
          <button
            onClick={() => handleStep(-15)}
            title="Step backward 15 minutes"
            style={{
              fontSize: '0.75rem',
              backgroundColor: '#1e293b',
              color: '#cbd5e1',
              border: '1px solid #334155',
              borderRadius: '4px',
              padding: '0.25rem 0.55rem',
              cursor: 'pointer',
            }}
          >
            ◀ -15m
          </button>

          {/* Play / Pause Toggle */}
          <button
            onClick={onTogglePlay}
            style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              backgroundColor: isPlaying ? '#ef444420' : '#10b98120',
              color: isPlaying ? '#ef4444' : '#10b981',
              border: `1px solid ${isPlaying ? '#ef4444' : '#10b981'}`,
              borderRadius: '4px',
              padding: '0.25rem 0.85rem',
              cursor: 'pointer',
            }}
          >
            {isPlaying ? '⏸ Pause' : '▶ Play Timeline'}
          </button>

          {/* Step Forward 15m */}
          <button
            onClick={() => handleStep(15)}
            title="Step forward 15 minutes"
            style={{
              fontSize: '0.75rem',
              backgroundColor: '#1e293b',
              color: '#cbd5e1',
              border: '1px solid #334155',
              borderRadius: '4px',
              padding: '0.25rem 0.55rem',
              cursor: 'pointer',
            }}
          >
            +15m ▶
          </button>

          {/* Jump to Peak */}
          {releaseWindow && (
            <button
              onClick={handleJumpToReleasePeak}
              title="Jump to Discharge Peak"
              style={{
                fontSize: '0.75rem',
                backgroundColor: '#78350f30',
                color: '#f59e0b',
                border: '1px solid #f59e0b',
                borderRadius: '4px',
                padding: '0.25rem 0.55rem',
                cursor: 'pointer',
              }}
            >
              🎯 Release Peak
            </button>
          )}

          {/* Jump to End */}
          <button
            onClick={() => onTimeChange(new Date(endMs))}
            title="Jump to Satellite Pass (T_obs)"
            style={{
              fontSize: '0.75rem',
              backgroundColor: '#1e293b',
              color: '#cbd5e1',
              border: '1px solid #334155',
              borderRadius: '4px',
              padding: '0.25rem 0.55rem',
              cursor: 'pointer',
            }}
          >
            ⏩ T_obs
          </button>

          {/* Reset */}
          <button
            onClick={onReset}
            title="Reset Timeline to Peak Window"
            style={{
              fontSize: '0.75rem',
              backgroundColor: '#0f172a',
              color: '#94a3b8',
              border: '1px solid #334155',
              borderRadius: '4px',
              padding: '0.25rem 0.55rem',
              cursor: 'pointer',
            }}
          >
            🔄 Reset
          </button>
        </div>

        {/* Speed Selection & Vessel Following Dropdown */}
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {/* Playback Speed Buttons */}
          <div style={{ display: 'flex', gap: '0.2rem', alignItems: 'center' }}>
            <span style={{ fontSize: '0.70rem', color: '#64748b' }}>Speed:</span>
            {[1, 5, 15, 60].map((spd) => (
              <button
                key={spd}
                onClick={() => onSpeedChange(spd)}
                style={{
                  fontSize: '0.68rem',
                  fontWeight: playbackSpeed === spd ? 700 : 500,
                  backgroundColor: playbackSpeed === spd ? '#0284c7' : '#1e293b',
                  color: playbackSpeed === spd ? '#f8fafc' : '#94a3b8',
                  border: '1px solid #334155',
                  borderRadius: '3px',
                  padding: '0.15rem 0.35rem',
                  cursor: 'pointer',
                }}
              >
                {spd}x
              </button>
            ))}
          </div>

          {/* Follow Vessel Dropdown */}
          {vesselTracks.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ fontSize: '0.70rem', color: '#64748b' }}>Focus:</span>
              <select
                value={followMmsi || selectedCandidateMmsi || ''}
                onChange={(e) => {
                  const mmsi = e.target.value || undefined;
                  if (onToggleFollow) onToggleFollow(mmsi);
                  if (onSelectCandidate && mmsi) onSelectCandidate(mmsi);
                }}
                style={{
                  fontSize: '0.72rem',
                  backgroundColor: '#1e293b',
                  color: '#f8fafc',
                  border: '1px solid #334155',
                  borderRadius: '4px',
                  padding: '0.2rem 0.4rem',
                  cursor: 'pointer',
                }}
              >
                <option value="">-- All Regional Ships --</option>
                {vesselTracks.map((t) => (
                  <option key={t.mmsi} value={t.mmsi}>
                    🚢 {t.vessel_name} ({t.vessel_type})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
