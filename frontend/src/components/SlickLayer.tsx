import React from 'react';
import { Polygon, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { SlickDetection, SARScene } from '../types';

interface Props {
  slick?: SlickDetection;
  sarScene?: SARScene;
  visible?: boolean;
  onSelectSlick?: (slick: SlickDetection) => void;
  isSelected?: boolean;
  opacity?: number;
}

const slickCentroidIcon = (isSelected: boolean) => L.divIcon({
  className: 'slick-centroid-marker',
  html: `
    <div style="position: relative; display: flex; align-items: center; justify-content: center;">
      <div style="position: absolute; width: ${isSelected ? '28px' : '22px'}; height: ${isSelected ? '28px' : '22px'}; border-radius: 50%; background: rgba(239, 68, 68, 0.4); animation: pulse 1.5s infinite;"></div>
      <div style="width: 12px; height: 12px; border-radius: 50%; background: #ef4444; border: 2px solid #ffffff; box-shadow: 0 0 ${isSelected ? '16px' : '10px'} #ef4444;"></div>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

export const SlickLayer: React.FC<Props> = ({
  slick,
  sarScene,
  visible = true,
  onSelectSlick,
  isSelected = false,
  opacity = 0.55,
}) => {
  if (!slick || !visible) return null;

  // Convert GeoJSON [lon, lat] coordinates to Leaflet [lat, lon]
  const ring = slick.slick_polygon.coordinates[0];
  const latLngs: [number, number][] = ring.map(([lon, lat]) => [lat, lon]);
  const centroidLatLng: [number, number] = [slick.centroid.coordinates[1], slick.centroid.coordinates[0]];
  const acquisitionTime = sarScene ? new Date(sarScene.acquisition_timestamp).toUTCString() : 'N/A';

  return (
    <>
      <Polygon
        positions={latLngs}
        pathOptions={{
          color: isSelected ? '#f87171' : '#ef4444',
          weight: isSelected ? 3.5 : 2.5,
          fillColor: '#b91c1c',
          fillOpacity: opacity,
          dashArray: isSelected ? '4, 4' : undefined,
        }}
        eventHandlers={{
          click: () => {
            if (onSelectSlick) onSelectSlick(slick);
          },
        }}
      >
        <Popup>
          <div style={{ fontSize: '0.82rem', lineHeight: 1.5 }}>
            <div style={{ color: '#ef4444', fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.2rem' }}>
              🔴 Detected Oil Slick Polygon
            </div>
            <strong>Detection Timestamp:</strong> {acquisitionTime}<br />
            <strong>Surface Area:</strong> {slick.area_sq_km.toFixed(2)} km²<br />
            <strong>Perimeter:</strong> {slick.perimeter_km.toFixed(2)} km<br />
            <strong>Major Axis Orientation:</strong> {slick.major_axis_orientation_deg}°<br />
            <strong>Confidence Score:</strong> {(slick.confidence_score * 100).toFixed(1)}%<br />
            <strong>Lookalike Probability:</strong> {((slick.lookalike_probability ?? 0) * 100).toFixed(1)}%
          </div>
        </Popup>
      </Polygon>

      <Marker
        position={centroidLatLng}
        icon={slickCentroidIcon(isSelected)}
        eventHandlers={{
          click: () => {
            if (onSelectSlick) onSelectSlick(slick);
          },
        }}
      >
        <Popup>
          <div style={{ fontSize: '0.8rem', lineHeight: 1.4 }}>
            <strong style={{ color: '#ef4444' }}>Observed Slick Centroid</strong><br />
            <strong>Coordinates:</strong> {slick.centroid.coordinates[0].toFixed(4)}°E, {slick.centroid.coordinates[1].toFixed(4)}°N<br />
            <strong>Observation Time:</strong> {acquisitionTime}
          </div>
        </Popup>
      </Marker>
    </>
  );
};
