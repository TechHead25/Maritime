import React from 'react';
import { Polygon, CircleMarker, Circle, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { ProbabilityCloud, ReleaseWindow, GeoPoint } from '../types';
import { findClosestProbabilityCloud } from '../utils/timelineUtils';

interface Props {
  clouds: ProbabilityCloud[];
  releaseWindow?: ReleaseWindow;
  originCentroid?: GeoPoint;
  originUncertaintyKm?: number;
  visible?: boolean;
  showParticles?: boolean;
  showUncertaintyBuffer?: boolean;
  selectedStepIndex?: number;
  currentTime?: Date;
}

const originCentroidIcon = L.divIcon({
  className: 'origin-centroid-marker',
  html: `
    <div style="position: relative; display: flex; align-items: center; justify-content: center;">
      <div style="position: absolute; width: 28px; height: 28px; border-radius: 50%; background: rgba(56, 189, 248, 0.25); border: 1px dashed #38bdf8;"></div>
      <div style="width: 14px; height: 14px; border-radius: 50%; background: #38bdf8; border: 2px solid #ffffff; box-shadow: 0 0 12px #38bdf8;"></div>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

export const DriftCloudLayer: React.FC<Props> = ({
  clouds,
  releaseWindow,
  originCentroid,
  originUncertaintyKm = 0.58,
  visible = true,
  showParticles = true,
  showUncertaintyBuffer = true,
  selectedStepIndex,
  currentTime,
}) => {
  if (!visible || !clouds || clouds.length === 0) return null;

  // Filter clouds: if currentTime is given, render the active simulation timestep cloud
  let cloudsToRender: ProbabilityCloud[] = [];
  if (currentTime) {
    const closest = findClosestProbabilityCloud(clouds, currentTime);
    cloudsToRender = closest ? [closest.cloud] : [clouds[0]];
  } else if (selectedStepIndex !== undefined && clouds[selectedStepIndex]) {
    cloudsToRender = [clouds[selectedStepIndex]];
  } else {
    // Default overview: subsampled envelopes
    cloudsToRender = clouds.filter((_, idx) => idx % 3 === 0 || idx === clouds.length - 1);
  }

  return (
    <>
      {cloudsToRender.map((cloud, idx) => {
        const poly = cloud.envelope_polygon || cloud.convex_hull_polygon;
        const ring = poly?.coordinates?.[0] || [];
        const latLngs: [number, number][] = ring.map((pt: number[]) => [pt[1], pt[0]]);

        return (
          <React.Fragment key={cloud.id || idx}>
            {/* Probability Dispersion Cloud Envelope */}
            {latLngs.length > 0 && (
              <Polygon
                positions={latLngs}
                pathOptions={{
                  color: '#0284c7',
                  weight: 1.5,
                  fillColor: '#38bdf8',
                  fillOpacity: 0.15,
                  dashArray: '4, 4',
                }}
              >
                <Popup>
                  <div style={{ fontSize: '0.8rem', lineHeight: 1.4 }}>
                    <strong style={{ color: '#38bdf8' }}>Lagrangian Drift Cloud (-{(cloud.hours_before_sar ?? cloud.hours_backward ?? 0).toFixed(1)}h)</strong><br />
                    <strong>Timestamp:</strong> {new Date(cloud.timestamp).toUTCString()}<br />
                    <strong>Centroid:</strong> {cloud.center_point.coordinates[0].toFixed(4)}°E, {cloud.center_point.coordinates[1].toFixed(4)}°N<br />
                    <strong>Dispersion Spread (1σ):</strong> {cloud.dispersion_radius_km.toFixed(2)} km<br />
                    <strong>95% Envelope Area:</strong> ~{(Math.PI * Math.pow(cloud.dispersion_radius_km * 2, 2)).toFixed(1)} km²
                  </div>
                </Popup>
              </Polygon>
            )}

            {/* Particle Swarm Samples */}
            {showParticles && cloud.particle_sample_points?.map((pt: number[], pIdx: number) => (
              <CircleMarker
                key={pIdx}
                center={[pt[1], pt[0]]}
                radius={1.5}
                pathOptions={{
                  color: '#38bdf8',
                  fillColor: '#38bdf8',
                  fillOpacity: 0.60,
                  weight: 0,
                }}
              />
            ))}
          </React.Fragment>
        );
      })}

      {/* Reconstructed Origin Centroid Marker & Uncertainty Circle */}
      {originCentroid && (
        <>
          <Marker
            position={[originCentroid.coordinates[1], originCentroid.coordinates[0]]}
            icon={originCentroidIcon}
          >
            <Popup>
              <div style={{ fontSize: '0.82rem', lineHeight: 1.45 }}>
                <strong style={{ color: '#38bdf8', fontSize: '0.9rem' }}>Reconstructed Spill Origin</strong><br />
                <strong>Coordinates:</strong> {originCentroid.coordinates[0].toFixed(4)}°E, {originCentroid.coordinates[1].toFixed(4)}°N<br />
                <strong>Estimated Release Peak:</strong> {releaseWindow ? new Date(releaseWindow.peak_probability_time).toUTCString() : 'N/A'}<br />
                <strong>Spatial Dispersion (1σ):</strong> ±{originUncertaintyKm.toFixed(2)} km<br />
                {releaseWindow && (
                  <span>
                    <strong>Release Window (90% CI):</strong> {new Date(releaseWindow.estimated_start_time).toUTCString().slice(17, 22)} - {new Date(releaseWindow.estimated_end_time).toUTCString().slice(17, 22)} UTC
                  </span>
                )}
              </div>
            </Popup>
          </Marker>

          {showUncertaintyBuffer && (
            <Circle
              center={[originCentroid.coordinates[1], originCentroid.coordinates[0]]}
              radius={originUncertaintyKm * 1000}
              pathOptions={{
                color: '#38bdf8',
                weight: 1.5,
                fillColor: '#38bdf8',
                fillOpacity: 0.08,
                dashArray: '6, 6',
              }}
            />
          )}
        </>
      )}
    </>
  );
};
