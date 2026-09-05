import React, { useState } from 'react';
import { MapContainer, TileLayer, Polygon, Popup } from 'react-leaflet';
import {
  SARScene,
  SlickDetection,
  ProbabilityCloud,
  ReleaseWindow,
  GeoPoint,
  VesselTrack,
  CandidateVessel,
  AttributionScore,
} from '../types';
import { SARFootprintLayer } from './SARFootprintLayer';
import { SlickLayer } from './SlickLayer';
import { DriftCloudLayer } from './DriftCloudLayer';
import { VesselTrackLayer } from './VesselTrackLayer';
import { Layers } from 'lucide-react';

interface Props {
  sarScene?: SARScene;
  slick?: SlickDetection;
  clouds?: ProbabilityCloud[];
  releaseWindow?: ReleaseWindow;
  originCentroid?: GeoPoint;
  originUncertaintyKm?: number;
  vesselTracks?: VesselTrack[];
  candidates?: CandidateVessel[];
  attributionScores?: AttributionScore[];
  selectedCandidateMmsi?: string;
  selectedSlickId?: string;
  onSelectCandidate?: (mmsi: string) => void;
  onSelectSlick?: (slick: SlickDetection) => void;
  currentTime?: Date;
}

export const InvestigationMap: React.FC<Props> = ({
  sarScene,
  slick,
  clouds = [],
  releaseWindow,
  originCentroid,
  originUncertaintyKm,
  vesselTracks = [],
  candidates = [],
  attributionScores = [],
  selectedCandidateMmsi,
  selectedSlickId,
  onSelectCandidate,
  onSelectSlick,
  currentTime,
}) => {
  // Layer Toggles
  const [showFootprint, setShowFootprint] = useState<boolean>(true);
  const [showSARImagery, setShowSARImagery] = useState<boolean>(true);
  const [showSlick, setShowSlick] = useState<boolean>(true);
  const [showLookalikes, setShowLookalikes] = useState<boolean>(true);
  const [showDrift, setShowDrift] = useState<boolean>(true);
  const [showParticles, setShowParticles] = useState<boolean>(true);
  const [showOrigin, setShowOrigin] = useState<boolean>(true);
  const [showReleaseRegion, setShowReleaseRegion] = useState<boolean>(true);
  const [showVessels, setShowVessels] = useState<boolean>(true);
  const [showTracks, setShowTracks] = useState<boolean>(true);

  // Opacity Controls
  const [slickOpacity, setSlickOpacity] = useState<number>(0.65);
  const [driftOpacity, setDriftOpacity] = useState<number>(0.25);
  const [sarOpacity, setSarOpacity] = useState<number>(0.15);

  // Controls & Legend State
  const [isControlsOpen, setIsControlsOpen] = useState<boolean>(false);
  const [showLegend, setShowLegend] = useState<boolean>(true);

  // Center coordinate: default around incident location
  const centerLat = slick ? slick.centroid.coordinates[1] : 7.85;
  const centerLon = slick ? slick.centroid.coordinates[0] : 82.90;

  // Release Region Envelope Polygon (from earliest cloud or convex hull)
  const releaseCloud = clouds.length > 0 ? clouds[clouds.length - 1] : undefined;
  const releasePoly = releaseCloud?.envelope_polygon || releaseCloud?.convex_hull_polygon;
  const releaseLatLngs: [number, number][] = releasePoly?.coordinates?.[0]
    ? releasePoly.coordinates[0].map((pt) => [pt[1], pt[0]])
    : [];

  return (
    <div style={{
      position: 'relative',
      backgroundColor: '#0c1322',
      border: '1px solid #1e293b',
      borderRadius: '8px',
      overflow: 'hidden',
      height: '100%',
      minHeight: '620px',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Top Map Toolbar: Quick Toggles & Controls Button */}
      <div style={{
        position: 'absolute',
        top: 12,
        right: 12,
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
      }}>
        <div style={{
          backgroundColor: 'rgba(15, 23, 42, 0.92)',
          border: '1px solid #334155',
          borderRadius: '6px',
          padding: '0.35rem 0.65rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.72rem',
          fontWeight: 600,
          backdropFilter: 'blur(8px)',
        }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer', color: '#ef4444' }}>
            <input
              type="checkbox"
              checked={showSlick}
              onChange={(e) => setShowSlick(e.target.checked)}
            />
            Slick
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer', color: '#38bdf8' }}>
            <input
              type="checkbox"
              checked={showDrift}
              onChange={(e) => setShowDrift(e.target.checked)}
            />
            Drift
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer', color: '#0284c7' }}>
            <input
              type="checkbox"
              checked={showParticles}
              onChange={(e) => setShowParticles(e.target.checked)}
            />
            Particles
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer', color: '#f59e0b' }}>
            <input
              type="checkbox"
              checked={showVessels}
              onChange={(e) => setShowVessels(e.target.checked)}
            />
            AIS Ships ({vesselTracks.length})
          </label>
        </div>

        {/* Detailed Layer Controls Button */}
        <button
          onClick={() => setIsControlsOpen(!isControlsOpen)}
          style={{
            backgroundColor: isControlsOpen ? '#0284c7' : 'rgba(15, 23, 42, 0.92)',
            border: '1px solid #334155',
            color: '#f8fafc',
            padding: '0.35rem 0.65rem',
            borderRadius: '6px',
            fontSize: '0.72rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            backdropFilter: 'blur(8px)',
          }}
          title="Toggle Layers & Opacity"
        >
          <Layers size={13} />
          <span>Layers & Opacity</span>
        </button>
      </div>

      {/* Slide-out Layer & Opacity Control Panel */}
      {isControlsOpen && (
        <div style={{
          position: 'absolute',
          top: 50,
          right: 12,
          zIndex: 1000,
          backgroundColor: 'rgba(12, 19, 34, 0.96)',
          border: '1px solid #334155',
          borderRadius: '8px',
          padding: '1rem',
          width: '280px',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.85rem',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.6)',
          backdropFilter: 'blur(10px)',
          fontSize: '0.75rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '0.4rem' }}>
            <strong style={{ color: '#f8fafc' }}>Map Layer Visibility</strong>
            <button
              onClick={() => setIsControlsOpen(false)}
              style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <label style={layerCheckboxStyle('#64748b')}>
              <input type="checkbox" checked={showFootprint} onChange={(e) => setShowFootprint(e.target.checked)} />
              SAR Swath Footprint
            </label>
            <label style={layerCheckboxStyle('#38bdf8')}>
              <input type="checkbox" checked={showSARImagery} onChange={(e) => setShowSARImagery(e.target.checked)} />
              SAR Calibrated Backscatter Overlay
            </label>
            <label style={layerCheckboxStyle('#ef4444')}>
              <input type="checkbox" checked={showSlick} onChange={(e) => setShowSlick(e.target.checked)} />
              Detected Oil Slick
            </label>
            <label style={layerCheckboxStyle('#fbbf24')}>
              <input type="checkbox" checked={showLookalikes} onChange={(e) => setShowLookalikes(e.target.checked)} />
              Lookalikes (Biogenic / Low Wind)
            </label>
            <label style={layerCheckboxStyle('#0284c7')}>
              <input type="checkbox" checked={showDrift} onChange={(e) => setShowDrift(e.target.checked)} />
              Drift Probability Cloud
            </label>
            <label style={layerCheckboxStyle('#38bdf8')}>
              <input type="checkbox" checked={showParticles} onChange={(e) => setShowParticles(e.target.checked)} />
              Particle Trajectories
            </label>
            <label style={layerCheckboxStyle('#10b981')}>
              <input type="checkbox" checked={showOrigin} onChange={(e) => setShowOrigin(e.target.checked)} />
              Estimated Origin Centroid
            </label>
            <label style={layerCheckboxStyle('#f59e0b')}>
              <input type="checkbox" checked={showReleaseRegion} onChange={(e) => setShowReleaseRegion(e.target.checked)} />
              Release Region Envelope
            </label>
            <label style={layerCheckboxStyle('#f87171')}>
              <input type="checkbox" checked={showVessels} onChange={(e) => setShowVessels(e.target.checked)} />
              AIS Vessels ({vesselTracks.length})
            </label>
            <label style={layerCheckboxStyle('#cbd5e1')}>
              <input type="checkbox" checked={showTracks} onChange={(e) => setShowTracks(e.target.checked)} />
              Vessel Historical Tracks
            </label>
          </div>

          <div style={{ borderTop: '1px solid #1e293b', paddingTop: '0.6rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <strong style={{ color: '#cbd5e1', fontSize: '0.70rem' }}>Layer Opacity Controls</strong>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#94a3b8' }}>
                <span>Slick Fill</span>
                <span>{(slickOpacity * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={slickOpacity}
                onChange={(e) => setSlickOpacity(Number(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#94a3b8' }}>
                <span>Drift Dispersion Cloud</span>
                <span>{(driftOpacity * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.8"
                step="0.05"
                value={driftOpacity}
                onChange={(e) => setDriftOpacity(Number(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#94a3b8' }}>
                <span>SAR Backscatter Swath</span>
                <span>{(sarOpacity * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.6"
                step="0.05"
                value={sarOpacity}
                onChange={(e) => setSarOpacity(Number(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Leaflet Map Container */}
      <div style={{ flex: 1, position: 'relative' }}>
        <MapContainer
          center={[centerLat, centerLon]}
          zoom={10}
          scrollWheelZoom={true}
          style={{ width: '100%', height: '100%' }}
        >
          {/* CartoDB Dark Matter tile layer */}
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {/* 1. SAR Swath Footprint */}
          <SARFootprintLayer sarScene={sarScene} visible={showFootprint} />

          {/* 2. SAR Calibrated Backscatter Overlay Simulation */}
          {showSARImagery && sarScene?.footprint_polygon?.coordinates?.[0] && (
            <Polygon
              positions={sarScene.footprint_polygon.coordinates[0].map((c) => [c[1], c[0]])}
              pathOptions={{
                color: '#38bdf8',
                weight: 1,
                fillColor: '#0369a1',
                fillOpacity: sarOpacity,
              }}
            >
              <Popup>
                <div style={{ fontSize: '0.78rem' }}>
                  <strong>SAR Backscatter Array</strong><br />
                  Resolution: {sarScene.pixel_resolution_meters}m<br />
                  Mode: {sarScene.sensor_mode} ({sarScene.polarization})
                </div>
              </Popup>
            </Polygon>
          )}

          {/* 3. Detected Slick Layer */}
          <SlickLayer
            slick={slick}
            sarScene={sarScene}
            visible={showSlick}
            onSelectSlick={onSelectSlick}
            isSelected={selectedSlickId === slick?.id}
            opacity={slickOpacity}
          />

          {/* 4. Release Region Envelope */}
          {showReleaseRegion && releaseLatLngs.length > 0 && (
            <Polygon
              positions={releaseLatLngs}
              pathOptions={{
                color: '#f59e0b',
                weight: 2,
                dashArray: '6, 6',
                fillColor: '#d97706',
                fillOpacity: 0.15,
              }}
            >
              <Popup>
                <div style={{ fontSize: '0.78rem' }}>
                  <strong style={{ color: '#f59e0b' }}>Estimated Release Region</strong><br />
                  Origin centroid dispersion envelope at estimated discharge time.
                </div>
              </Popup>
            </Polygon>
          )}

          {/* 5. Drift Probability Clouds & Particle Trajectories */}
          <DriftCloudLayer
            clouds={clouds}
            releaseWindow={releaseWindow}
            originCentroid={originCentroid}
            originUncertaintyKm={originUncertaintyKm}
            visible={showDrift}
            showParticles={showParticles}
            showUncertaintyBuffer={showOrigin}
            currentTime={currentTime}
          />

          {/* 6. AIS Vessels & Tracks */}
          <VesselTrackLayer
            tracks={vesselTracks}
            candidates={candidates}
            attributionScores={attributionScores}
            selectedCandidateMmsi={selectedCandidateMmsi}
            onSelectCandidate={onSelectCandidate}
            visible={showVessels}
            currentTime={currentTime}
          />
        </MapContainer>

        {/* Collapsible Forensic Map Legend */}
        <div style={{
          position: 'absolute',
          bottom: 12,
          left: 12,
          zIndex: 1000,
          backgroundColor: 'rgba(15, 23, 42, 0.92)',
          border: '1px solid #334155',
          borderRadius: '6px',
          padding: '0.6rem 0.85rem',
          fontSize: '0.72rem',
          backdropFilter: 'blur(8px)',
          maxWidth: '310px',
        }}>
          <div
            onClick={() => setShowLegend(!showLegend)}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', fontWeight: 700, color: '#f8fafc', marginBottom: showLegend ? '0.4rem' : 0 }}
          >
            <span>🗺 Console Map Legend</span>
            <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>{showLegend ? '▼' : '▲'}</span>
          </div>

          {showLegend && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', color: '#cbd5e1' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ width: '12px', height: '12px', backgroundColor: '#ef4444', borderRadius: '2px', display: 'inline-block' }} />
                <span>Detected Oil Slick (Sentinel-1 SAR)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ width: '12px', height: '12px', backgroundColor: '#38bdf8', borderRadius: '50%', display: 'inline-block', border: '1px solid #fff' }} />
                <span>Reconstructed Origin Centroid (T_peak)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ width: '12px', height: '12px', border: '1px dashed #0284c7', backgroundColor: 'rgba(56, 189, 248, 0.2)', display: 'inline-block' }} />
                <span>Lagrangian Particle Drift Cloud</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ width: '12px', height: '12px', border: '1px dashed #f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.15)', display: 'inline-block' }} />
                <span>Spill Release Region Envelope</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ width: '12px', height: '3px', backgroundColor: '#ef4444', display: 'inline-block' }} />
                <span>Priority Candidate Vessel Track</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ width: '12px', height: '3px', borderTop: '2px dashed #94a3b8', display: 'inline-block' }} />
                <span>Projected / Future Waypoint Track</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const layerCheckboxStyle = (color: string): React.CSSProperties => ({
  display: 'flex',
  alignItems: 'center',
  gap: '0.45rem',
  cursor: 'pointer',
  color: color,
  fontWeight: 500,
  fontSize: '0.72rem',
});
