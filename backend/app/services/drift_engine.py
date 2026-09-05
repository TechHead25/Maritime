"""Backward Particle Drift Simulation Engine.

Simulates reverse-time oceanographic and meteorological Lagrangian advection of oil particles
from SAR observation time (T_obs) backward to locate probable discharge origins and release windows.

Model equation:
  v_effective = (current_factor * ocean_current) + (wind_factor * surface_wind) + turbulent_diffusion
  x(t - dt) = x(t) - v_effective * dt
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid

import numpy as np

from backend.app.models.schemas import (
    DriftSimulation,
    GeoPoint,
    Particle,
    ParticleStatus,
    ProbabilityCloud,
    ReleaseWindow,
    SlickDetection,
    SlickPolygon,
)
from backend.app.utils.geo_utils import bbox_polygon, haversine_distance_km


@dataclass
class DriftEngineConfig:
    """Configuration parameters for Lagrangian drift simulation."""
    time_step_minutes: int = 30
    max_hours_backward: float = 48.0
    particle_count: int = 1000
    wind_leeway_factor: float = 0.03
    current_advection_factor: float = 1.00
    horizontal_diffusivity_m2_s: float = 2.5
    random_seed: int = 42
    sample_points_count: int = 50


@dataclass
class DriftSimulationResult:
    """Output bundle containing the simulation record, release window, and time-sliced clouds."""
    simulation: DriftSimulation
    release_window: ReleaseWindow
    probability_clouds: List[ProbabilityCloud]
    origin_centroid: GeoPoint
    origin_uncertainty_radius_km: float


class DriftEngine:
    """Lagrangian particle tracking engine for backward drift advection."""

    def __init__(self, config: Optional[DriftEngineConfig] = None):
        self.config = config or DriftEngineConfig()

    def run_backward_drift(
        self,
        slick_detection: SlickDetection,
        observation_timestamp: datetime,
        ocean_current_data: Optional[Dict[str, Any]] = None,
        wind_data: Optional[Dict[str, Any]] = None,
        estimated_release_hours_ago: float = 14.0,
        release_window_half_width_hours: float = 2.0,
    ) -> DriftSimulationResult:
        """Executes backward drift simulation and returns probability clouds and release window.
        
        Args:
            slick_detection: Detected slick with boundary polygon and centroid.
            observation_timestamp: Satellite pass time (T_obs).
            ocean_current_data: Current grid/vector dictionary (u, v in m/s).
            wind_data: Wind grid/vector dictionary (u, v in m/s).
            estimated_release_hours_ago: Estimated historical age of slick for release peak.
            release_window_half_width_hours: Half-window width around release peak.
            
        Returns:
            DriftSimulationResult containing simulation models, release window, and probability clouds.
        """
        rng = np.random.default_rng(self.config.random_seed)
        
        # 1. Parse environmental vectors (m/s)
        u_curr, v_curr = self._extract_current_vector(ocean_current_data)
        u_wind, v_wind = self._extract_wind_vector(wind_data)

        # Apply scaling factors
        u_advect = (self.config.current_advection_factor * u_curr) + (self.config.wind_leeway_factor * u_wind)
        v_advect = (self.config.current_advection_factor * v_curr) + (self.config.wind_leeway_factor * v_wind)

        # 2. Seed initial particles inside the slick polygon at T_obs
        initial_particles = self._seed_particles(
            slick_detection=slick_detection,
            count=self.config.particle_count,
            rng=rng
        )

        dt_seconds = self.config.time_step_minutes * 60
        total_steps = int((self.config.max_hours_backward * 60) / self.config.time_step_minutes)
        diffusivity = self.config.horizontal_diffusivity_m2_s

        sim_id = str(uuid.uuid4())
        sim_start_time = observation_timestamp
        sim_end_time = observation_timestamp - timedelta(hours=self.config.max_hours_backward)

        simulation_model = DriftSimulation(
            id=sim_id,
            slick_detection_id=slick_detection.id,
            simulation_mode="BACKWARD_LAGRANGIAN",
            simulation_start_time=sim_start_time,
            simulation_end_time=sim_end_time,
            time_step_minutes=self.config.time_step_minutes,
            particle_count=self.config.particle_count,
            wind_leeway_factor=self.config.wind_leeway_factor,
            current_advection_factor=self.config.current_advection_factor,
            created_at=datetime.now(timezone.utc)
        )

        # State arrays: shape (N, 2) -> [lon, lat]
        particles = np.copy(initial_particles)
        probability_clouds: List[ProbabilityCloud] = []

        # 3. Step backward in time
        current_time = sim_start_time
        for step in range(total_steps + 1):
            hours_ago = (step * self.config.time_step_minutes) / 60.0
            slice_time = sim_start_time - timedelta(hours=hours_ago)

            # Calculate cloud envelope and stats
            cloud = self._compute_probability_cloud(
                sim_id=sim_id,
                particles=particles,
                timestamp=slice_time,
                hours_before_sar=hours_ago,
                sample_count=self.config.sample_points_count
            )
            probability_clouds.append(cloud)

            # Advect backward for next step: x(t - dt) = x(t) - v * dt + noise
            if step < total_steps:
                # Stochastic turbulent diffusion perturbation (meters)
                sigma_diffusion = math.sqrt(2.0 * diffusivity * dt_seconds)
                noise_x = rng.normal(0.0, sigma_diffusion, size=self.config.particle_count)
                noise_y = rng.normal(0.0, sigma_diffusion, size=self.config.particle_count)

                # Total displacement in meters
                dx_meters = (-u_advect * dt_seconds) + noise_x
                dy_meters = (-v_advect * dt_seconds) + noise_y

                # Convert meter displacement to latitude/longitude degrees
                mean_lat = np.mean(particles[:, 1])
                lat_rad = math.radians(mean_lat)
                meters_per_deg_lon = 111320.0 * max(0.01, math.cos(lat_rad))
                meters_per_deg_lat = 110574.0

                d_lon = dx_meters / meters_per_deg_lon
                d_lat = dy_meters / meters_per_deg_lat

                particles[:, 0] += d_lon
                particles[:, 1] += d_lat

        # 4. Calculate Release Window and Origin Centroid
        peak_time = sim_start_time - timedelta(hours=estimated_release_hours_ago)
        start_time = peak_time - timedelta(hours=release_window_half_width_hours)
        end_time = peak_time + timedelta(hours=release_window_half_width_hours)

        release_window = ReleaseWindow(
            id=str(uuid.uuid4()),
            drift_simulation_id=sim_id,
            estimated_start_time=start_time,
            estimated_end_time=end_time,
            peak_probability_time=peak_time,
            confidence_interval=0.90
        )

        # Find closest probability cloud to peak release time
        origin_cloud = min(
            probability_clouds,
            key=lambda c: abs((c.timestamp - peak_time).total_seconds())
        )

        return DriftSimulationResult(
            simulation=simulation_model,
            release_window=release_window,
            probability_clouds=probability_clouds,
            origin_centroid=origin_cloud.center_point,
            origin_uncertainty_radius_km=origin_cloud.dispersion_radius_km
        )

    def _seed_particles(
        self,
        slick_detection: SlickDetection,
        count: int,
        rng: np.random.Generator
    ) -> np.ndarray:
        """Generates initial particle coordinates distributed inside the slick polygon."""
        ring = slick_detection.slick_polygon.coordinates[0]
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        particles = []
        max_attempts = count * 20
        attempts = 0

        # Uniform rejection sampling inside polygon
        while len(particles) < count and attempts < max_attempts:
            cand_lon = rng.uniform(min_lon, max_lon)
            cand_lat = rng.uniform(min_lat, max_lat)
            if self._point_in_polygon(cand_lon, cand_lat, ring):
                particles.append([cand_lon, cand_lat])
            attempts += 1

        # Fallback: if complex polygon leaves remaining slots, distribute around centroid
        while len(particles) < count:
            c_lon = slick_detection.centroid.longitude
            c_lat = slick_detection.centroid.latitude
            scale_deg = 0.005
            particles.append([
                c_lon + rng.normal(0, scale_deg),
                c_lat + rng.normal(0, scale_deg)
            ])

        return np.array(particles, dtype=np.float64)

    def _compute_probability_cloud(
        self,
        sim_id: str,
        particles: np.ndarray,
        timestamp: datetime,
        hours_before_sar: float,
        sample_count: int
    ) -> ProbabilityCloud:
        """Calculates centroid, standard deviation dispersion radius, and bounding envelope."""
        lons = particles[:, 0]
        lats = particles[:, 1]

        center_lon = float(np.mean(lons))
        center_lat = float(np.mean(lats))
        center_pt = GeoPoint(coordinates=[round(center_lon, 5), round(center_lat, 5)])

        # Calculate dispersion standard deviation in km
        distances_km = [
            haversine_distance_km(center_lon, center_lat, float(p[0]), float(p[1]))
            for p in particles
        ]
        dispersion_km = float(np.std(distances_km)) if len(distances_km) > 1 else 0.5
        # Ensure a minimum uncertainty floor of 0.5 km
        dispersion_km = max(0.5, round(dispersion_km, 3))

        # Build 95% confidence bounding envelope polygon (approx 2 sigma)
        sigma_lon = float(np.std(lons)) * 2.0
        sigma_lat = float(np.std(lats)) * 2.0
        sigma_lon = max(0.005, sigma_lon)
        sigma_lat = max(0.005, sigma_lat)

        envelope_poly = bbox_polygon(
            min_lon=round(center_lon - sigma_lon, 5),
            min_lat=round(center_lat - sigma_lat, 5),
            max_lon=round(center_lon + sigma_lon, 5),
            max_lat=round(center_lat + sigma_lat, 5),
        )

        # Sample particle coordinates for frontend visualization
        step = max(1, len(particles) // sample_count)
        samples = [
            [round(float(p[0]), 5), round(float(p[1]), 5)]
            for p in particles[::step][:sample_count]
        ]

        return ProbabilityCloud(
            id=str(uuid.uuid4()),
            drift_simulation_id=sim_id,
            timestamp=timestamp,
            hours_before_sar=hours_before_sar,
            envelope_polygon=SlickPolygon(coordinates=envelope_poly),
            center_point=center_pt,
            dispersion_radius_km=dispersion_km,
            particle_sample_points=samples
        )

    def _point_in_polygon(self, x: float, y: float, poly: List[List[float]]) -> bool:
        """Ray-casting algorithm for point-in-polygon containment."""
        n = len(poly)
        inside = False
        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def _extract_current_vector(self, current_data: Optional[Dict[str, Any]]) -> Tuple[float, float]:
        """Extracts eastward (u) and northward (v) surface current velocities in m/s."""
        if not current_data:
            return (0.0, 0.0)
        mean_vec = current_data.get("mean_current_vectors", {})
        u = float(mean_vec.get("u_eastward_m_per_s") or mean_vec.get("u_eastward_m_s", 0.0))
        v = float(mean_vec.get("v_northward_m_per_s") or mean_vec.get("v_northward_m_s", 0.0))
        return (u, v)

    def _extract_wind_vector(self, wind_data: Optional[Dict[str, Any]]) -> Tuple[float, float]:
        """Extracts eastward (u) and northward (v) surface wind velocities in m/s."""
        if not wind_data:
            return (0.0, 0.0)
        mean_vec = wind_data.get("mean_wind_vectors", {})
        u = float(mean_vec.get("u_eastward_m_per_s") or mean_vec.get("u_eastward_m_s", 0.0))
        v = float(mean_vec.get("v_northward_m_per_s") or mean_vec.get("v_northward_m_s", 0.0))
        return (u, v)
