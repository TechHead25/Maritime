"""Multi-Factor Explainable Attribution Scoring & Forensic Evidence Engine.

Computes transparent, auditable attribution liability scores for candidate vessels
based on 5 deterministic forensic evidence factors:
1. Spatiotemporal Proximity: 40% (Max 40.0 pts)
2. Timing Alignment: 25% (Max 25.0 pts)
3. Navigational Behaviour: 15% (Max 15.0 pts)
4. AIS Continuity / Anomaly: 10% (Max 10.0 pts)
5. Vessel Relevance: 10% (Max 10.0 pts)

Also generates structured forensic evidence categorized as:
- SUPPORTING_EVIDENCE (Incriminating / correlating signals)
- CONTRADICTING_EVIDENCE (Signals reducing likelihood)
- EXCULPATORY_EVIDENCE (Signals strongly exonerating candidate)
- DATA_QUALITY (Telemetry confidence and density)
- UNCERTAINTY (Dispersion and temporal bounds)

Guiding Rule (from GEMINI.md):
Never state that a vessel 'definitely caused a spill' or is 'guilty'.
Always use calibrated phrasing:
"This vessel is the highest-ranked candidate based on the available spatial, temporal, and navigational evidence."
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from backend.app.models.schemas import (
    AttributionScore,
    AttributionScoreSubScores,
    CandidateVessel,
    EvidenceCategory,
    EvidenceItem,
    FactorCategory,
    GeoPoint,
    ProbabilityCloud,
    ReleaseWindow,
    RiskLevel,
    SlickDetection,
    VesselTrack,
    VesselType,
)
from backend.app.utils.geo_utils import haversine_distance_km


@dataclass
class ScoringWeights:
    """Weights for the 5 attribution factors summing to 100%."""
    proximity_weight: float = 40.0
    timing_weight: float = 25.0
    behavior_weight: float = 15.0
    ais_weight: float = 10.0
    vessel_weight: float = 10.0


class ScoringEngine:
    """Explainable Multi-Factor Attribution Scoring & Evidence Engine."""

    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()

    def score_candidates(
        self,
        candidates: List[CandidateVessel],
        vessel_tracks: List[VesselTrack],
        slick_detection: SlickDetection,
        release_window: ReleaseWindow,
        probability_clouds: List[ProbabilityCloud],
    ) -> List[AttributionScore]:
        """Calculates multi-factor attribution scores and evidence chains for all candidates.
        
        Args:
            candidates: Intercepted candidate vessel entities.
            vessel_tracks: Raw/interpolated track waypoints for each vessel.
            slick_detection: Oil slick polygon, centroid, and orientation.
            release_window: Estimated release window [T_start, T_end].
            probability_clouds: Particle dispersion probability clouds.
            
        Returns:
            List of AttributionScore objects sorted in descending order by total score.
        """
        if not candidates:
            return []

        # Find origin cloud at peak release time
        origin_cloud = min(
            probability_clouds,
            key=lambda c: abs((c.timestamp - release_window.peak_probability_time).total_seconds())
        )
        dispersion_sigma = max(0.5, origin_cloud.dispersion_radius_km)
        slick_orientation = slick_detection.major_axis_orientation_deg

        track_map = {t.mmsi: t for t in vessel_tracks}
        scored_list: List[AttributionScore] = []

        for cand in candidates:
            track = track_map.get(cand.mmsi)
            score_obj = self._evaluate_candidate(
                candidate=cand,
                track=track,
                slick_orientation=slick_orientation,
                release_window=release_window,
                probability_clouds=probability_clouds,
                dispersion_sigma=dispersion_sigma
            )
            scored_list.append(score_obj)

        # Sort descending by total score
        scored_list.sort(key=lambda s: s.total_score, reverse=True)

        # Assign ordinal ranks (1 = highest candidate)
        for rank_idx, s in enumerate(scored_list, start=1):
            s.rank = rank_idx

        return scored_list

    def _evaluate_candidate(
        self,
        candidate: CandidateVessel,
        track: Optional[VesselTrack],
        slick_orientation: float,
        release_window: ReleaseWindow,
        probability_clouds: List[ProbabilityCloud],
        dispersion_sigma: float
    ) -> AttributionScore:
        """Evaluates all 5 evidence factors and generates structured forensic evidence."""
        score_id = str(uuid.uuid4())
        cand_name = candidate.vessel_name

        supporting: List[EvidenceItem] = []
        contradicting: List[EvidenceItem] = []
        exculpatory: List[EvidenceItem] = []
        data_quality: List[EvidenceItem] = []
        uncertainty: List[EvidenceItem] = []

        # 1. Spatiotemporal Proximity Score (Max 40.0 pts)
        s_prox, ev_prox = self._score_proximity(
            score_id=score_id,
            candidate=candidate,
            track=track,
            probability_clouds=probability_clouds,
            release_window=release_window,
            dispersion_sigma=dispersion_sigma
        )
        self._dispatch_evidence(ev_prox, supporting, contradicting, exculpatory)

        # 2. Timing Alignment Score (Max 25.0 pts)
        s_timing, ev_timing = self._score_timing(
            score_id=score_id,
            candidate=candidate,
            release_window=release_window
        )
        self._dispatch_evidence(ev_timing, supporting, contradicting, exculpatory)

        # 3. Navigational Behaviour Score (Max 15.0 pts)
        s_behavior, ev_behaviors = self._score_behavior(
            score_id=score_id,
            candidate=candidate,
            track=track,
            slick_orientation=slick_orientation
        )
        for ev in ev_behaviors:
            self._dispatch_evidence(ev, supporting, contradicting, exculpatory)

        # 4. AIS Continuity / Anomaly Score (Max 10.0 pts)
        s_ais, ev_ais = self._score_ais_continuity(
            score_id=score_id,
            candidate=candidate,
            track=track,
            release_window=release_window
        )
        self._dispatch_evidence(ev_ais, supporting, contradicting, exculpatory)

        # 5. Vessel Relevance Score (Max 10.0 pts)
        s_vessel, ev_vessel = self._score_vessel_relevance(
            score_id=score_id,
            candidate=candidate
        )
        self._dispatch_evidence(ev_vessel, supporting, contradicting, exculpatory)

        # 6. Data Quality & Scientific Uncertainty Items
        dq_items, unc_items = self._generate_data_quality_and_uncertainty(
            score_id=score_id,
            candidate=candidate,
            track=track,
            release_window=release_window,
            dispersion_sigma=dispersion_sigma
        )
        data_quality.extend(dq_items)
        uncertainty.extend(unc_items)

        # Composite total score
        total = round(s_prox + s_timing + s_behavior + s_ais + s_vessel, 1)
        total = max(0.0, min(100.0, total))

        # Risk categorization
        if total >= 75.0:
            risk = RiskLevel.VERY_HIGH
        elif total >= 50.0:
            risk = RiskLevel.HIGH
        elif total >= 30.0:
            risk = RiskLevel.MEDIUM
        elif total >= 15.0:
            risk = RiskLevel.LOW
        else:
            risk = RiskLevel.NEGLIGIBLE

        sub_scores = AttributionScoreSubScores(
            proximity_score=round(s_prox, 1),
            trajectory_alignment_score=round(s_timing, 1),
            vessel_type_risk_score=round(s_vessel, 1),
            navigational_anomaly_score=round(s_behavior, 1),
            ais_integrity_penalty=round(s_ais, 1)
        )

        all_evidence = supporting + contradicting + exculpatory + data_quality + uncertainty

        return AttributionScore(
            id=score_id,
            candidate_vessel_id=candidate.id,
            candidate_name=cand_name,
            mmsi=candidate.mmsi,
            vessel_type=candidate.vessel_type,
            rank=1,
            total_score=total,
            risk_level=risk,
            sub_scores=sub_scores,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            exculpatory_evidence=exculpatory,
            data_quality_items=data_quality,
            uncertainty_items=uncertainty,
            evidence_items=all_evidence
        )

    def _dispatch_evidence(
        self,
        ev: EvidenceItem,
        supporting: List[EvidenceItem],
        contradicting: List[EvidenceItem],
        exculpatory: List[EvidenceItem]
    ):
        if ev.category == EvidenceCategory.SUPPORTING_EVIDENCE:
            supporting.append(ev)
        elif ev.category == EvidenceCategory.CONTRADICTING_EVIDENCE:
            contradicting.append(ev)
        elif ev.category == EvidenceCategory.EXCULPATORY_EVIDENCE:
            exculpatory.append(ev)

    # -----------------------------------------------------------------------
    # Factor 1: Spatiotemporal Proximity (40%)
    # -----------------------------------------------------------------------
    def _score_proximity(
        self,
        score_id: str,
        candidate: Optional[CandidateVessel] = None,
        track: Optional[VesselTrack] = None,
        probability_clouds: Optional[List[ProbabilityCloud]] = None,
        release_window: Optional[ReleaseWindow] = None,
        dispersion_sigma: float = 1.0,
        cpa_km: Optional[float] = None,
    ) -> Tuple[float, EvidenceItem]:
        """Calculates proximity score and generates supporting/contradicting/exculpatory items."""
        cand_name = candidate.vessel_name if candidate else "Candidate Vessel"
        min_4d_dist = float("inf")

        if cpa_km is not None:
            min_4d_dist = cpa_km
        elif candidate and (
            candidate.is_in_release_envelope or (
                release_window and release_window.estimated_start_time <= candidate.time_of_closest_approach <= release_window.estimated_end_time
            )
        ):
            min_4d_dist = candidate.closest_point_of_approach_km
        elif track and track.waypoints and probability_clouds:
            for wp in track.waypoints:
                nearest_cloud = min(
                    probability_clouds,
                    key=lambda c: abs((c.timestamp - wp.timestamp).total_seconds())
                )
                time_diff_hours = abs((nearest_cloud.timestamp - wp.timestamp).total_seconds()) / 3600.0
                if time_diff_hours <= 1.0:
                    d = haversine_distance_km(
                        wp.longitude,
                        wp.latitude,
                        nearest_cloud.center_point.longitude,
                        nearest_cloud.center_point.latitude
                    )
                    if d < min_4d_dist:
                        min_4d_dist = d

        if min_4d_dist == float("inf"):
            if candidate and release_window:
                delta_h = abs((candidate.time_of_closest_approach - release_window.peak_probability_time).total_seconds()) / 3600.0
                min_4d_dist = candidate.closest_point_of_approach_km + (delta_h * 3.0)
            elif candidate:
                min_4d_dist = candidate.closest_point_of_approach_km
            else:
                min_4d_dist = 10.0

        # Exponential Gaussian decay based on dispersion spread
        decay = math.exp(-(min_4d_dist ** 2) / (2.0 * (dispersion_sigma ** 2)))
        score = round(self.weights.proximity_weight * decay, 1)

        if min_4d_dist <= 1.0:
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.SUPPORTING_EVIDENCE,
                factor_category=FactorCategory.PROXIMITY,
                title=f"Direct Origin Intersection ({min_4d_dist * 1000:.0f} m)",
                description=(
                    f"Vessel trajectory intersected the reconstructed origin centroid within "
                    f"{min_4d_dist * 1000:.0f} meters during the active release window."
                ),
                severity="HIGH",
                source="Lagrangian Advection Intercept",
                calculated_value=f"{min_4d_dist * 1000:.0f} m",
                threshold_used="< 1.0 km",
                calculation_reference="Geodesic Haversine Distance to Origin Centroid",
                confidence=0.95,
                uncertainty=f"+/- {dispersion_sigma:.2f} km dispersion radius",
                score_impact=score,
                verifiable_data={"min_distance_km": round(min_4d_dist, 3)}
            )
        elif min_4d_dist <= 12.0:
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.SUPPORTING_EVIDENCE,
                factor_category=FactorCategory.PROXIMITY,
                title=f"Close Transit of Origin Zone ({min_4d_dist:.1f} km)",
                description=f"Vessel passed within {min_4d_dist:.1f} km of the reconstructed origin centroid during release window.",
                severity="MEDIUM",
                source="Lagrangian Advection Intercept",
                calculated_value=f"{min_4d_dist:.1f} km",
                threshold_used="< 12.0 km",
                calculation_reference="Geodesic Haversine Distance to Origin Centroid",
                confidence=0.90,
                uncertainty=f"+/- {dispersion_sigma:.2f} km dispersion radius",
                score_impact=score,
                verifiable_data={"min_distance_km": round(min_4d_dist, 3)}
            )
        elif min_4d_dist <= 25.0:
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.CONTRADICTING_EVIDENCE,
                factor_category=FactorCategory.PROXIMITY,
                title=f"Divergent Spatial Clearance ({min_4d_dist:.1f} km)",
                description=(
                    f"Vessel trajectory maintained a {min_4d_dist:.1f} km spatial separation "
                    f"from the primary backward drift dispersion envelope."
                ),
                severity="LOW",
                source="Lagrangian Advection Intercept",
                calculated_value=f"{min_4d_dist:.1f} km",
                threshold_used="> 12.0 km",
                calculation_reference="Geodesic Haversine Distance to Origin Centroid",
                confidence=0.88,
                score_impact=score,
                verifiable_data={"min_distance_km": round(min_4d_dist, 3)}
            )
        else:
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.EXCULPATORY_EVIDENCE,
                factor_category=FactorCategory.PROXIMITY,
                title=f"Significant Distance from Spill Origin ({min_4d_dist:.1f} km)",
                description=(
                    f"Vessel remained {min_4d_dist:.1f} km away from the estimated origin region, "
                    f"exceeding reasonable oil drift dispersion boundaries."
                ),
                severity="HIGH",
                source="Lagrangian Advection Intercept",
                calculated_value=f"{min_4d_dist:.1f} km",
                threshold_used="> 25.0 km",
                calculation_reference="Geodesic Haversine Distance to Origin Centroid",
                confidence=0.95,
                score_impact=score,
                verifiable_data={"min_distance_km": round(min_4d_dist, 3)}
            )

        return score, ev

    # -----------------------------------------------------------------------
    # Factor 2: Timing Alignment (25%)
    # -----------------------------------------------------------------------
    def _score_timing(
        self,
        score_id: str,
        candidate: Optional[CandidateVessel] = None,
        cpa_time: Optional[datetime] = None,
        release_window: Optional[ReleaseWindow] = None
    ) -> Tuple[float, EvidenceItem]:
        """Calculates timing alignment score and temporal evidence."""
        cand_name = candidate.vessel_name if candidate else "Candidate Vessel"
        transit_time = cpa_time or (candidate.time_of_closest_approach if candidate else None)
        if not transit_time or not release_window:
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.DATA_QUALITY,
                factor_category=FactorCategory.ALIGNMENT,
                title="Timing Data Unavailable",
                description="Unable to compute timing alignment due to missing transit or release window timestamps.",
                score_impact=0.0
            )
            return 0.0, ev

        peak_time = release_window.peak_probability_time
        start_time = release_window.estimated_start_time
        end_time = release_window.estimated_end_time

        delta_hours = abs((transit_time - peak_time).total_seconds()) / 3600.0
        window_half_width = max(0.5, (end_time - start_time).total_seconds() / 7200.0)

        if start_time <= transit_time <= end_time:
            fraction_of_half = min(1.0, delta_hours / window_half_width)
            score = round(self.weights.timing_weight * (1.0 - fraction_of_half * 0.25), 1)

            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.SUPPORTING_EVIDENCE,
                factor_category=FactorCategory.ALIGNMENT,
                title="Temporal Coincidence with Release Window",
                description=(
                    f"Vessel transit ({transit_time.strftime('%H:%M')} UTC) occurred directly "
                    f"within the estimated release window (delta: {delta_hours * 60:.0f} min from peak probability)."
                ),
                severity="HIGH",
                source="Historical AIS Ingestion",
                source_timestamp_start=start_time,
                source_timestamp_end=end_time,
                calculated_value=f"{delta_hours * 60:.0f} min delta",
                threshold_used=f"Within [{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')} UTC]",
                calculation_reference="Peak Release Temporal Difference",
                confidence=0.92,
                score_impact=score,
                verifiable_data={"time_of_cpa": transit_time.isoformat(), "peak_time": peak_time.isoformat()}
            )
        elif delta_hours <= 4.0:
            hours_outside = delta_hours - window_half_width
            decay = math.exp(-(hours_outside ** 2) / (2.0 * (3.0 ** 2)))
            score = round(self.weights.timing_weight * decay, 1)

            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.CONTRADICTING_EVIDENCE,
                factor_category=FactorCategory.ALIGNMENT,
                title=f"Slight Temporal Offset ({delta_hours:.1f}h from Peak)",
                description=(
                    f"Vessel transit ({transit_time.strftime('%H:%M')} UTC) was offset by "
                    f"{delta_hours:.1f} hours from the peak discharge probability time."
                ),
                severity="LOW",
                source="Historical AIS Ingestion",
                calculated_value=f"{delta_hours:.1f}h offset",
                threshold_used="Outside release window",
                confidence=0.85,
                score_impact=score,
                verifiable_data={"delta_hours": round(delta_hours, 2)}
            )
        else:
            score = 1.0
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.EXCULPATORY_EVIDENCE,
                factor_category=FactorCategory.ALIGNMENT,
                title=f"Significant Temporal Non-Overlap ({delta_hours:.1f}h Outside Window)",
                description=(
                    f"Vessel transit occurred {delta_hours:.1f} hours away from the release window, "
                    f"indicating the vessel was not present during the discharge event."
                ),
                severity="HIGH",
                source="Historical AIS Ingestion",
                calculated_value=f"{delta_hours:.1f}h",
                threshold_used="> 4.0h from release window",
                confidence=0.96,
                score_impact=score,
                verifiable_data={"delta_hours": round(delta_hours, 2)}
            )

        return score, ev

    # -----------------------------------------------------------------------
    # Factor 3: Navigational Behaviour (15%)
    # -----------------------------------------------------------------------
    def _score_behavior(
        self,
        score_id: str,
        candidate: Optional[CandidateVessel] = None,
        track: Optional[VesselTrack] = None,
        slick_orientation: float = 0.0
    ) -> Tuple[float, List[EvidenceItem]]:
        """Calculates behavioral heading and speed reduction anomalies."""
        items: List[EvidenceItem] = []
        cand_name = candidate.vessel_name if candidate else "Candidate Vessel"

        if not track or not track.waypoints:
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.DATA_QUALITY,
                factor_category=FactorCategory.BEHAVIOR,
                title="Nominal Navigation Profile",
                description="Insufficient waypoint density to assess heading or speed anomalies.",
                severity="INFORMATIONAL",
                score_impact=2.0
            )
            return 2.0, [ev]

        # 1. Course alignment with slick elongation axis
        courses = [wp.course_over_ground_deg for wp in track.waypoints if wp.speed_over_ground_knots > 2.0]
        mean_course = float(sum(courses) / len(courses)) if courses else slick_orientation
        delta_angle = abs(mean_course - slick_orientation) % 360.0
        acute_delta = min(delta_angle, 360.0 - delta_angle)
        acute_delta = min(acute_delta, abs(acute_delta - 180.0))

        cos_align = max(0.0, math.cos(math.radians(acute_delta)))
        align_score = round(10.0 * cos_align, 1)

        if acute_delta <= 25.0:
            ev_align = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.SUPPORTING_EVIDENCE,
                factor_category=FactorCategory.ALIGNMENT,
                title=f"Trajectory Heading Aligned with Slick Axis ({mean_course:.0f}° vs {slick_orientation:.0f}°)",
                description=(
                    f"Vessel course ({mean_course:.1f}°) exhibits {cos_align * 100:.0f}% angular alignment "
                    f"with the major elongation axis of the oil slick ({slick_orientation:.1f}°)."
                ),
                severity="HIGH",
                source="Historical AIS Ingestion",
                calculated_value=f"Delta: {acute_delta:.1f}°",
                threshold_used="Delta <= 25.0°",
                calculation_reference="Cosine Vector Alignment with Slick Major Axis",
                confidence=0.90,
                score_impact=align_score,
                verifiable_data={"mean_course_deg": mean_course, "slick_orientation_deg": slick_orientation}
            )
            items.append(ev_align)
        elif acute_delta >= 50.0:
            ev_align = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.CONTRADICTING_EVIDENCE,
                factor_category=FactorCategory.ALIGNMENT,
                title=f"Course Divergent from Slick Orientation ({acute_delta:.0f}° Delta)",
                description=(
                    f"Vessel track heading ({mean_course:.1f}°) diverged from the slick dispersion "
                    f"elongation orientation ({slick_orientation:.1f}°)."
                ),
                severity="LOW",
                source="Historical AIS Ingestion",
                calculated_value=f"Delta: {acute_delta:.1f}°",
                threshold_used="Delta >= 50.0°",
                confidence=0.85,
                score_impact=align_score,
                verifiable_data={"mean_course_deg": mean_course, "slick_orientation_deg": slick_orientation}
            )
            items.append(ev_align)

        # 2. Speed drop and loitering analysis
        speeds = [wp.speed_over_ground_knots for wp in track.waypoints if wp.speed_over_ground_knots >= 0]
        speed_score = 0.0
        if speeds:
            min_spd, max_spd = min(speeds), max(speeds)
            if (max_spd - min_spd) >= 3.5 and min_spd < 9.0:
                speed_score = 5.0
                ev_speed = EvidenceItem(
                    id=str(uuid.uuid4()),
                    attribution_score_id=score_id,
                    candidate_vessel=cand_name,
                    category=EvidenceCategory.SUPPORTING_EVIDENCE,
                    factor_category=FactorCategory.BEHAVIOR,
                    title="Open-Sea Deceleration / Loitering Anomaly",
                    description=(
                        f"Vessel exhibited an abnormal open-ocean deceleration from {max_spd:.1f} knots down to "
                        f"{min_spd:.1f} knots during passage through the spill area."
                    ),
                    severity="HIGH",
                    source="Historical AIS Telemetry",
                    calculated_value=f"{max_spd:.1f} -> {min_spd:.1f} kts",
                    threshold_used="Speed Drop >= 3.5 kts AND Min Speed < 9.0 kts",
                    calculation_reference="Waypoint Speed Over Ground Analysis",
                    confidence=0.94,
                    score_impact=speed_score,
                    verifiable_data={"min_speed_knots": min_spd, "max_speed_knots": max_spd}
                )
                items.append(ev_speed)
            elif (max_spd - min_spd) < 2.0 and min_spd >= 10.0:
                ev_speed = EvidenceItem(
                    id=str(uuid.uuid4()),
                    attribution_score_id=score_id,
                    candidate_vessel=cand_name,
                    category=EvidenceCategory.EXCULPATORY_EVIDENCE,
                    factor_category=FactorCategory.BEHAVIOR,
                    title="Nominal Constant Cruising Speed Profile",
                    description=(
                        f"Vessel maintained uniform cruising speed ({min_spd:.1f} - {max_spd:.1f} kts) "
                        f"with zero loitering, stopping, or sudden speed drop anomalies."
                    ),
                    severity="MEDIUM",
                    source="Historical AIS Telemetry",
                    calculated_value=f"{min_spd:.1f} - {max_spd:.1f} kts (Stable)",
                    threshold_used="Speed variation < 2.0 kts",
                    calculation_reference="SOG Stability Evaluation",
                    confidence=0.92,
                    score_impact=0.0,
                    verifiable_data={"min_speed_knots": min_spd, "max_speed_knots": max_spd}
                )
                items.append(ev_speed)

        total_behavior = min(self.weights.behavior_weight, align_score + speed_score)
        return total_behavior, items

    # -----------------------------------------------------------------------
    # Factor 4: AIS Continuity (10%)
    # -----------------------------------------------------------------------
    def _score_ais_continuity(
        self,
        score_id: str,
        candidate: Optional[CandidateVessel] = None,
        track: Optional[VesselTrack] = None,
        release_window: Optional[ReleaseWindow] = None
    ) -> Tuple[float, EvidenceItem]:
        """Calculates AIS transponder blackout score and exculpatory continuity."""
        cand_name = candidate.vessel_name if candidate else "Candidate Vessel"
        has_gaps = (candidate.has_ais_gaps if candidate else False) or (track.has_ais_gaps if track else False)
        gaps = (candidate.gap_intervals if candidate else []) or (track.gap_intervals if track else [])

        if has_gaps and gaps:
            window_start = release_window.estimated_start_time if release_window else datetime.min.replace(tzinfo=timezone.utc)
            window_end = release_window.estimated_end_time if release_window else datetime.max.replace(tzinfo=timezone.utc)

            near_window = any(
                (g[0] <= window_end and g[1] >= window_start) for g in gaps
            )
            duration_hrs = sum((g[1] - g[0]).total_seconds() / 3600.0 for g in gaps)

            if near_window:
                score = self.weights.ais_weight  # 10.0 pts
                ev = EvidenceItem(
                    id=str(uuid.uuid4()),
                    attribution_score_id=score_id,
                    candidate_vessel=cand_name,
                    category=EvidenceCategory.SUPPORTING_EVIDENCE,
                    factor_category=FactorCategory.AIS_INTEGRITY,
                    title=f"AIS Transponder Blackout During Release Window ({duration_hrs:.1f}h)",
                    description=(
                        f"AIS transponder was deactivated for {duration_hrs:.1f} hours during transit "
                        f"directly across the estimated spill release envelope."
                    ),
                    severity="HIGH",
                    source="Historical AIS Ingestion",
                    source_timestamp_start=gaps[0][0] if gaps else None,
                    source_timestamp_end=gaps[0][1] if gaps else None,
                    calculated_value=f"{duration_hrs:.1f} hours gap",
                    threshold_used="Outage > 60 min during release window",
                    calculation_reference="Consecutive AIS Message Gap Interval",
                    confidence=0.95,
                    score_impact=score,
                    verifiable_data={"gap_duration_hours": round(duration_hrs, 2), "gap_count": len(gaps)}
                )
            else:
                score = 4.0
                ev = EvidenceItem(
                    id=str(uuid.uuid4()),
                    attribution_score_id=score_id,
                    candidate_vessel=cand_name,
                    category=EvidenceCategory.SUPPORTING_EVIDENCE,
                    factor_category=FactorCategory.AIS_INTEGRITY,
                    title=f"Regional AIS Transmission Outage ({duration_hrs:.1f}h)",
                    description=f"Vessel exhibited a {duration_hrs:.1f}-hour transponder transmission outage in the regional area.",
                    severity="MEDIUM",
                    source="Historical AIS Ingestion",
                    calculated_value=f"{duration_hrs:.1f} hours gap",
                    threshold_used="Outage > 60 min",
                    confidence=0.88,
                    score_impact=score,
                    verifiable_data={"gap_duration_hours": round(duration_hrs, 2)}
                )
        else:
            score = 0.0
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.EXCULPATORY_EVIDENCE,
                factor_category=FactorCategory.AIS_INTEGRITY,
                title="Continuous 100% AIS Transponder Broadcast",
                description=(
                    "Vessel maintained continuous, uninterrupted AIS broadcast across the entire "
                    "investigation horizon with zero transponder deactivations."
                ),
                severity="MEDIUM",
                source="Historical AIS Ingestion",
                calculated_value="100% Broadcast Continuity (0 Outages)",
                threshold_used="No gaps > 60 min",
                confidence=0.95,
                score_impact=0.0,
                verifiable_data={"has_gaps": False, "gap_count": 0}
            )

        return score, ev

    # -----------------------------------------------------------------------
    # Factor 5: Vessel Relevance (10%)
    # -----------------------------------------------------------------------
    def _score_vessel_relevance(
        self,
        score_id: str,
        candidate: Optional[Union[CandidateVessel, VesselType]] = None,
        vessel_type: Optional[VesselType] = None
    ) -> Tuple[float, EvidenceItem]:
        """Calculates vessel type risk profile and corresponding evidence."""
        if isinstance(candidate, VesselType):
            v_type = candidate
            cand_name = "Candidate Vessel"
        elif candidate and isinstance(candidate, CandidateVessel):
            v_type = candidate.vessel_type
            cand_name = candidate.vessel_name
        elif vessel_type is not None:
            v_type = vessel_type
            cand_name = "Candidate Vessel"
        else:
            v_type = VesselType.CARGO
            cand_name = "Candidate Vessel"

        if v_type == VesselType.TANKER:
            score = 10.0
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.SUPPORTING_EVIDENCE,
                factor_category=FactorCategory.VESSEL_TYPE,
                title="High-Risk Laden Crude / Product Tanker Profile",
                description="Vessel is an oil/chemical tanker carrying high-volume liquid hydrocarbon cargo and oily ballast.",
                severity="HIGH",
                source="ITU-R M.1371 AIS Static Metadata",
                calculated_value=f"Ship Type: {v_type.value}",
                threshold_used="Tanker / Liquid Petroleum Cargo",
                confidence=0.98,
                score_impact=score,
                verifiable_data={"vessel_type": v_type.value}
            )
        elif v_type == VesselType.BUNKER:
            score = 8.5
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.SUPPORTING_EVIDENCE,
                factor_category=FactorCategory.VESSEL_TYPE,
                title="Moderate-High Risk: Bunkering Tanker",
                description="Vessel conducts offshore marine fuel transfers with dedicated heavy fuel oil storage.",
                severity="MEDIUM",
                source="ITU-R M.1371 AIS Static Metadata",
                calculated_value=f"Ship Type: {v_type.value}",
                score_impact=score,
                verifiable_data={"vessel_type": v_type.value}
            )
        elif v_type == VesselType.CARGO:
            score = 6.0
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.SUPPORTING_EVIDENCE,
                factor_category=FactorCategory.VESSEL_TYPE,
                title="Moderate Risk: Commercial Cargo Vessel",
                description="Commercial container/bulk cargo vessel operating with heavy fuel oil bunker storage.",
                severity="LOW",
                source="ITU-R M.1371 AIS Static Metadata",
                calculated_value=f"Ship Type: {v_type.value}",
                score_impact=score,
                verifiable_data={"vessel_type": v_type.value}
            )
        else:
            score = 1.0
            ev = EvidenceItem(
                id=str(uuid.uuid4()),
                attribution_score_id=score_id,
                candidate_vessel=cand_name,
                category=EvidenceCategory.EXCULPATORY_EVIDENCE,
                factor_category=FactorCategory.VESSEL_TYPE,
                title="Low-Risk Non-Tanker Vessel Classification",
                description=f"Vessel is classified as {v_type.value} with low operational hydrocarbon discharge potential.",
                severity="HIGH",
                source="ITU-R M.1371 AIS Static Metadata",
                calculated_value=f"Ship Type: {v_type.value}",
                threshold_used="Non-petroleum carrier",
                confidence=0.95,
                score_impact=score,
                verifiable_data={"vessel_type": v_type.value}
            )

        return score, ev

    # -----------------------------------------------------------------------
    # Data Quality & Uncertainty Generators
    # -----------------------------------------------------------------------
    def _generate_data_quality_and_uncertainty(
        self,
        score_id: str,
        candidate: CandidateVessel,
        track: Optional[VesselTrack],
        release_window: ReleaseWindow,
        dispersion_sigma: float
    ) -> Tuple[List[EvidenceItem], List[EvidenceItem]]:
        dq_items: List[EvidenceItem] = []
        unc_items: List[EvidenceItem] = []

        # Data quality: Ping count & temporal resolution
        wp_count = len(track.waypoints) if track and track.waypoints else 0
        dq = EvidenceItem(
            id=str(uuid.uuid4()),
            attribution_score_id=score_id,
            candidate_vessel=candidate.vessel_name,
            category=EvidenceCategory.DATA_QUALITY,
            factor_category=FactorCategory.DATA_QUALITY,
            title="AIS Trajectory Telemetry Density",
            description=(
                f"Trajectory reconstructed from {wp_count} georeferenced AIS positions with "
                f"geodesic waypoint interpolation at 15-minute resolution."
            ),
            severity="INFORMATIONAL",
            source="Historical AIS CSV Ingestion",
            calculated_value=f"{wp_count} pings",
            confidence=0.95,
            score_impact=0.0,
            verifiable_data={"waypoint_count": wp_count}
        )
        dq_items.append(dq)

        # Uncertainty: Spatial dispersion radius
        unc_spatial = EvidenceItem(
            id=str(uuid.uuid4()),
            attribution_score_id=score_id,
            candidate_vessel=candidate.vessel_name,
            category=EvidenceCategory.UNCERTAINTY,
            factor_category=FactorCategory.UNCERTAINTY,
            title="Origin Spatial Dispersion Uncertainty (1-Sigma)",
            description=(
                f"Turbulent diffusion and hydrodynamic divergence define an origin uncertainty radius "
                f"of +/- {dispersion_sigma:.2f} km around the reconstructed centroid."
            ),
            severity="INFORMATIONAL",
            source="CMEMS Hydrodynamic Lagrangian Diffusion",
            calculated_value=f"+/- {dispersion_sigma:.2f} km",
            confidence=0.90,
            uncertainty=f"1-sigma radius: {dispersion_sigma:.2f} km",
            score_impact=0.0,
            verifiable_data={"dispersion_sigma_km": dispersion_sigma}
        )
        unc_items.append(unc_spatial)

        # Uncertainty: Temporal release window width
        delta_window_hrs = (release_window.estimated_end_time - release_window.estimated_start_time).total_seconds() / 3600.0
        unc_temporal = EvidenceItem(
            id=str(uuid.uuid4()),
            attribution_score_id=score_id,
            candidate_vessel=candidate.vessel_name,
            category=EvidenceCategory.UNCERTAINTY,
            factor_category=FactorCategory.UNCERTAINTY,
            title="Release Time Uncertainty Window",
            description=(
                f"Estimated discharge time window is bounded within {delta_window_hrs:.1f} hours "
                f"with a {release_window.confidence_interval * 100:.0f}% confidence interval."
            ),
            severity="INFORMATIONAL",
            source="Lagrangian Reverse Advection Statistics",
            source_timestamp_start=release_window.estimated_start_time,
            source_timestamp_end=release_window.estimated_end_time,
            calculated_value=f"{delta_window_hrs:.1f} hours span",
            confidence=release_window.confidence_interval,
            uncertainty=f"{release_window.confidence_interval * 100:.0f}% CI",
            score_impact=0.0,
            verifiable_data={"window_duration_hours": round(delta_window_hrs, 2)}
        )
        unc_items.append(unc_temporal)

        return dq_items, unc_items
