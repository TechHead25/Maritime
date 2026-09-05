"""AIS Candidate Identification and Spatiotemporal Interception Engine.

Correlates historical vessel trajectories (AIS) with backward drift probability clouds
and estimated release windows to identify candidate vessels based on:
1. Spatiotemporal proximity and Closest Point of Approach (CPA)
2. Intersection with the dynamic particle dispersion envelopes
3. Navigational anomalies (transponder dark gaps, speed drops, abrupt course changes)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid

from backend.app.models.schemas import (
    CandidateVessel,
    GeoPoint,
    ProbabilityCloud,
    ReleaseWindow,
    VesselPosition,
    VesselTrack,
    VesselType,
)
from backend.app.utils.geo_utils import haversine_distance_km


@dataclass
class AISEngineConfig:
    """Configuration settings for AIS trajectory interception."""
    max_cpa_distance_km: float = 50.0
    interpolation_step_minutes: float = 5.0
    gap_threshold_minutes: float = 60.0
    speed_drop_threshold_knots: float = 3.5
    course_change_threshold_deg: float = 35.0


@dataclass
class VesselNavigationalProfile:
    """Calculated metrics summarizing a vessel's behavior near the spill zone."""
    cpa_km: float
    time_of_cpa: datetime
    cpa_position: GeoPoint
    is_in_release_envelope: bool
    is_in_release_window: bool
    has_gaps: bool
    gap_intervals: List[List[datetime]]
    speed_drop_detected: bool
    min_speed_knots: float
    max_speed_knots: float
    course_deviation_deg: float
    anomalies_summary: List[str] = field(default_factory=list)


class AISEngine:
    """Spatiotemporal candidate vessel interceptor."""

    def __init__(self, config: Optional[AISEngineConfig] = None):
        self.config = config or AISEngineConfig()

    def identify_candidates(
        self,
        case_id: str,
        vessel_tracks: List[VesselTrack],
        release_window: ReleaseWindow,
        probability_clouds: List[ProbabilityCloud],
    ) -> List[CandidateVessel]:
        """Evaluates vessel tracks against probability clouds and release window.
        
        Args:
            case_id: Target InvestigationCase UUID.
            vessel_tracks: List of raw/interpolated vessel trajectories.
            release_window: Estimated release window [T_start, T_end].
            probability_clouds: Time-series of dispersion probability clouds.
            
        Returns:
            List of strongly-typed CandidateVessel models.
        """
        candidates: List[CandidateVessel] = []

        # Find origin center at peak release time
        origin_cloud = min(
            probability_clouds,
            key=lambda c: abs((c.timestamp - release_window.peak_probability_time).total_seconds())
        )
        origin_center = origin_cloud.center_point

        for track in vessel_tracks:
            profile = self._analyze_vessel_track(
                track=track,
                release_window=release_window,
                probability_clouds=probability_clouds,
                origin_center=origin_center
            )

            # Filter candidates within maximum search horizon
            if profile.cpa_km <= self.config.max_cpa_distance_km:
                cand = CandidateVessel(
                    id=str(uuid.uuid4()),
                    case_id=case_id,
                    vessel_track_id=track.id,
                    mmsi=track.mmsi,
                    vessel_name=track.vessel_name,
                    vessel_type=track.vessel_type,
                    flag_country=track.flag_country,
                    closest_point_of_approach_km=round(profile.cpa_km, 3),
                    time_of_closest_approach=profile.time_of_cpa,
                    interpolated_position_at_cpa=profile.cpa_position,
                    is_in_release_envelope=profile.is_in_release_envelope,
                    has_ais_gaps=profile.has_gaps,
                    gap_intervals=profile.gap_intervals
                )
                candidates.append(cand)

        return candidates

    def _analyze_vessel_track(
        self,
        track: VesselTrack,
        release_window: ReleaseWindow,
        probability_clouds: List[ProbabilityCloud],
        origin_center: GeoPoint,
    ) -> VesselNavigationalProfile:
        """Computes CPA, cloud intersection, dark gaps, and behavioral metrics for a single track."""
        dense_positions = self._interpolate_waypoints(track.waypoints, self.config.interpolation_step_minutes)

        if not dense_positions:
            # Fallback if no waypoints
            now = release_window.peak_probability_time
            return VesselNavigationalProfile(
                cpa_km=999.0,
                time_of_cpa=now,
                cpa_position=origin_center,
                is_in_release_envelope=False,
                is_in_release_window=False,
                has_gaps=False,
                gap_intervals=[],
                speed_drop_detected=False,
                min_speed_knots=0.0,
                max_speed_knots=0.0,
                course_deviation_deg=0.0
            )

        # 1. Find Closest Point of Approach (CPA) to origin center
        min_dist = float("inf")
        cpa_time = dense_positions[0].timestamp
        cpa_pt = GeoPoint(coordinates=[dense_positions[0].longitude, dense_positions[0].latitude])

        for pos in dense_positions:
            d = haversine_distance_km(
                pos.longitude,
                pos.latitude,
                origin_center.longitude,
                origin_center.latitude
            )
            if d < min_dist:
                min_dist = d
                cpa_time = pos.timestamp
                cpa_pt = GeoPoint(coordinates=[round(pos.longitude, 5), round(pos.latitude, 5)])

        # 2. Check temporal overlap and spatial cloud intersection
        is_in_window = (release_window.estimated_start_time <= cpa_time <= release_window.estimated_end_time)
        is_in_envelope = False

        cloud_map = {c.timestamp: c for c in probability_clouds}

        for pos in dense_positions:
            # Check if this position is within release window
            if release_window.estimated_start_time <= pos.timestamp <= release_window.estimated_end_time:
                # Find matching or nearest probability cloud
                nearest_cloud = min(
                    probability_clouds,
                    key=lambda c: abs((c.timestamp - pos.timestamp).total_seconds())
                )
                time_diff_min = abs((nearest_cloud.timestamp - pos.timestamp).total_seconds()) / 60.0
                if time_diff_min <= 60.0:
                    dist_to_cloud = haversine_distance_km(
                        pos.longitude,
                        pos.latitude,
                        nearest_cloud.center_point.longitude,
                        nearest_cloud.center_point.latitude
                    )
                    # Within 2x dispersion radius (approx 95% envelope)
                    if dist_to_cloud <= max(1.5, nearest_cloud.dispersion_radius_km * 2.0):
                        is_in_envelope = True
                        break

        # 3. Detect AIS gaps
        has_gaps, gap_intervals = self._detect_ais_gaps(track)

        # 4. Detect speed drops and course anomalies
        speeds = [p.speed_over_ground_knots for p in track.waypoints if p.speed_over_ground_knots > 0]
        min_spd = min(speeds) if speeds else 0.0
        max_spd = max(speeds) if speeds else 0.0
        speed_drop = (max_spd - min_spd) >= self.config.speed_drop_threshold_knots

        courses = [p.course_over_ground_deg for p in track.waypoints]
        course_dev = 0.0
        if len(courses) >= 2:
            diffs = [abs(courses[i] - courses[i-1]) for i in range(1, len(courses))]
            # Account for 360 wrap-around
            diffs = [min(d, 360.0 - d) for d in diffs]
            course_dev = max(diffs)

        anomalies = []
        if has_gaps:
            anomalies.append(f"AIS transponder gap detected ({len(gap_intervals)} outages)")
        if speed_drop and min_spd < 9.0:
            anomalies.append(f"Significant speed reduction ({max_spd:.1f} kts down to {min_spd:.1f} kts)")
        if course_dev >= self.config.course_change_threshold_deg:
            anomalies.append(f"Course alteration observed ({course_dev:.1f} deg)")

        return VesselNavigationalProfile(
            cpa_km=min_dist,
            time_of_cpa=cpa_time,
            cpa_position=cpa_pt,
            is_in_release_envelope=is_in_envelope,
            is_in_release_window=is_in_window,
            has_gaps=has_gaps,
            gap_intervals=gap_intervals,
            speed_drop_detected=speed_drop,
            min_speed_knots=min_spd,
            max_speed_knots=max_spd,
            course_deviation_deg=course_dev,
            anomalies_summary=anomalies
        )

    def _interpolate_waypoints(
        self,
        waypoints: List[VesselPosition],
        step_minutes: float
    ) -> List[VesselPosition]:
        """Interpolates discrete GPS waypoints at fine temporal resolution."""
        if not waypoints:
            return []
        if len(waypoints) == 1:
            return [waypoints[0]]

        # Sort chronologically
        sorted_wp = sorted(waypoints, key=lambda w: w.timestamp)
        dense: List[VesselPosition] = []

        for i in range(len(sorted_wp) - 1):
            p1 = sorted_wp[i]
            p2 = sorted_wp[i + 1]

            dense.append(p1)

            t1 = p1.timestamp
            t2 = p2.timestamp
            dt_minutes = (t2 - t1).total_seconds() / 60.0

            if dt_minutes > step_minutes:
                num_steps = int(dt_minutes / step_minutes)
                for step_i in range(1, num_steps):
                    frac = (step_i * step_minutes) / dt_minutes
                    interp_time = t1 + timedelta(minutes=step_i * step_minutes)
                    interp_lon = p1.longitude + frac * (p2.longitude - p1.longitude)
                    interp_lat = p1.latitude + frac * (p2.latitude - p1.latitude)
                    interp_spd = p1.speed_over_ground_knots + frac * (p2.speed_over_ground_knots - p1.speed_over_ground_knots)
                    interp_course = p1.course_over_ground_deg

                    dense.append(
                        VesselPosition(
                            timestamp=interp_time,
                            longitude=round(interp_lon, 5),
                            latitude=round(interp_lat, 5),
                            speed_over_ground_knots=round(interp_spd, 1),
                            course_over_ground_deg=round(interp_course, 1),
                            navigational_status=p1.navigational_status
                        )
                    )

        dense.append(sorted_wp[-1])
        return dense

    def _detect_ais_gaps(self, track: VesselTrack) -> Tuple[bool, List[List[datetime]]]:
        """Identifies transponder transmission gaps exceeding the threshold."""
        # Use declared gap intervals if present
        if track.has_ais_gaps and track.gap_intervals:
            return True, track.gap_intervals

        # Compute gaps from waypoint intervals
        sorted_wp = sorted(track.waypoints, key=lambda w: w.timestamp)
        gaps: List[List[datetime]] = []

        for i in range(len(sorted_wp) - 1):
            t1 = sorted_wp[i].timestamp
            t2 = sorted_wp[i + 1].timestamp
            delta_min = (t2 - t1).total_seconds() / 60.0
            if delta_min >= self.config.gap_threshold_minutes:
                gaps.append([t1, t2])

        has_gap = len(gaps) > 0 or track.has_ais_gaps
        return has_gap, gaps
