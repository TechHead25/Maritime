import React from 'react';
import { Polygon, Popup } from 'react-leaflet';
import { SARScene } from '../types';

interface Props {
  sarScene?: SARScene;
  visible?: boolean;
}

export const SARFootprintLayer: React.FC<Props> = ({ sarScene, visible = true }) => {
  if (!sarScene || !sarScene.footprint_polygon || !visible) return null;

  const ring = sarScene.footprint_polygon.coordinates[0];
  const latLngs: [number, number][] = ring.map(([lon, lat]) => [lat, lon]);

  return (
    <Polygon
      positions={latLngs}
      pathOptions={{
        color: '#64748b',
        weight: 1.5,
        dashArray: '5, 5',
        fillColor: '#334155',
        fillOpacity: 0.08,
      }}
    >
      <Popup>
        <div style={{ fontSize: '0.8rem', lineHeight: 1.4 }}>
          <strong style={{ color: '#38bdf8' }}>SAR Satellite Swath Footprint</strong><br />
          <strong>Platform:</strong> {sarScene.satellite_platform}<br />
          <strong>Sensor Mode:</strong> {sarScene.sensor_mode}<br />
          <strong>Polarization:</strong> {sarScene.polarization}<br />
          <strong>Acquisition:</strong> {new Date(sarScene.acquisition_timestamp).toUTCString()}<br />
          <strong>Resolution:</strong> {sarScene.pixel_resolution_meters}m ground pixel
        </div>
      </Popup>
    </Polygon>
  );
};
