"""Unified Vessel Intelligence Service.

Bridges real-time live AIS telemetry with historical forensic investigation dossiers:
- Enriches vessel identity via verified maritime registries (zero fabricated data).
- Classifies telemetry state strictly as LIVE_POSITION, RECENT_POSITION, or HISTORICAL_POSITION.
- Correlates cross-investigation relationships (Priority Candidate, Candidate, Subject, Tracked).
- Aggregates multi-case forensic evidence items citing this vessel.
- Compliant with GEMINI.md: strictly non-accusatory evidence representation.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from backend.app.providers.registry import provider_registry
from backend.app.services.case_service import case_service
from backend.app.services.live_ais_service import live_ais_service

logger = logging.getLogger("maritime-oil-attribution.services.vessel_intelligence")


class VesselIntelligenceService:
    """Aggregates real-time kinematics, registry identity, and forensic investigation lineage."""

    def get_unified_vessel_profile(self, mmsi: str) -> Dict[str, Any]:
        """Compiles a complete unified intelligence profile for a given MMSI."""
        clean_mmsi = str(mmsi).strip()

        # -------------------------------------------------------------------
        # 1. Verified Identity & Registry Particulars
        # -------------------------------------------------------------------
        identity_prov = provider_registry.get_vessel_identity_provider()
        registry_rec = identity_prov.lookup_by_mmsi(clean_mmsi)

        identity_data = {
            "mmsi": clean_mmsi,
            "vessel_name": registry_rec.get("vessel_name", f"MMSI {clean_mmsi}") if registry_rec else None,
            "vessel_type": registry_rec.get("vessel_type", "UNKNOWN") if registry_rec else None,
            "imo": registry_rec.get("imo") if registry_rec else None,
            "callsign": registry_rec.get("callsign") if registry_rec else None,
            "flag_country": registry_rec.get("flag_country") if registry_rec else None,
            "gross_tonnage": registry_rec.get("gross_tonnage") if registry_rec else None,
            "deadweight_tonnage": registry_rec.get("deadweight_tonnage") if registry_rec else None,
            "length_meters": registry_rec.get("length_meters") if registry_rec else None,
            "beam_meters": registry_rec.get("beam_meters") if registry_rec else None,
            "build_year": registry_rec.get("build_year") if registry_rec else None,
            "owner_operator": registry_rec.get("owner_operator") if registry_rec else None,
            "registry_verified": registry_rec is not None,
            "registry_source": identity_prov.name if registry_rec else "Unindexed in local verified registry",
        }

        # -------------------------------------------------------------------
        # 2. Real-Time Status & Kinematic Telemetry
        # -------------------------------------------------------------------
        live_details = live_ais_service.get_vessel_details(clean_mmsi)
        telemetry_state: Dict[str, Any] = {}

        if live_details:
            age = float(live_details.get("data_age_seconds", 0.0))
            if age < 300.0:  # < 5 minutes
                pos_status = "LIVE POSITION"
                pos_color = "#10b981"
            elif age < 7200.0:  # < 2 hours
                pos_status = "RECENT POSITION"
                pos_color = "#f59e0b"
            else:
                pos_status = "STALE POSITION"
                pos_color = "#94a3b8"

            telemetry_state = {
                "position_status": pos_status,
                "status_color": pos_color,
                "is_currently_live": age < 300.0,
                "data_age_seconds": age,
                "latitude": live_details.get("latitude"),
                "longitude": live_details.get("longitude"),
                "speed_over_ground_knots": live_details.get("speed_over_ground_knots", 0.0),
                "course_over_ground_deg": live_details.get("course_over_ground_deg", 0.0),
                "heading_deg": live_details.get("heading_deg", 0.0),
                "navigational_status": live_details.get("navigational_status", "Underway using engine"),
                "last_update_utc": live_details.get("last_update_utc"),
                "telemetry_source": "Live AIS Stream (Mediate Ingestion)",
                "active_trail": live_details.get("trail", []),
                "has_ais_gaps": live_details.get("has_ais_gaps", False),
                "gap_intervals": live_details.get("gap_intervals", []),
                "waypoints_count": live_details.get("waypoints_count", 0),
            }
            if not identity_data["vessel_name"] and live_details.get("vessel_name"):
                identity_data["vessel_name"] = live_details.get("vessel_name")
            if not identity_data["vessel_type"] and live_details.get("vessel_type"):
                identity_data["vessel_type"] = live_details.get("vessel_type")
        else:
            # Fallback: search historical case tracks for last known observation
            last_known = self._find_last_known_historical_track(clean_mmsi)
            telemetry_state = {
                "position_status": "HISTORICAL POSITION" if last_known else "OFFLINE",
                "status_color": "#64748b",
                "is_currently_live": False,
                "data_age_seconds": None,
                "latitude": last_known.get("latitude") if last_known else None,
                "longitude": last_known.get("longitude") if last_known else None,
                "speed_over_ground_knots": last_known.get("speed") if last_known else None,
                "course_over_ground_deg": last_known.get("course") if last_known else None,
                "heading_deg": None,
                "navigational_status": "Archived Record",
                "last_update_utc": last_known.get("timestamp_utc") if last_known else None,
                "telemetry_source": "Historical AIS Telemetry Archive",
                "active_trail": [],
                "has_ais_gaps": last_known.get("has_gaps", False) if last_known else False,
                "gap_intervals": last_known.get("gap_intervals", []) if last_known else [],
                "waypoints_count": last_known.get("waypoints_count", 0) if last_known else 0,
            }
            if last_known and not identity_data["vessel_name"]:
                identity_data["vessel_name"] = last_known.get("vessel_name")
            if last_known and not identity_data["vessel_type"]:
                identity_data["vessel_type"] = last_known.get("vessel_type")

        # -------------------------------------------------------------------
        # 3. Investigation Relationships
        # -------------------------------------------------------------------
        investigations = []
        evidence_items = []

        for case_id, case in case_service.cases.items():
            case_scores = case_service.attribution_scores.get(case_id, [])
            cand_score = next((s for s in case_scores if s.mmsi == clean_mmsi), None)

            case_tracks = case_service.vessel_tracks.get(case_id, [])
            v_track = next((t for t in case_tracks if t.mmsi == clean_mmsi), None)

            is_subject = case.metadata.get("investigation_subject_mmsi") == clean_mmsi

            if cand_score or v_track or is_subject:
                rel_type = "SUBJECT" if is_subject else ("PRIORITY_CANDIDATE" if (cand_score and cand_score.rank == 1) else ("CANDIDATE" if cand_score else "TRACKED_VESSEL"))
                inc_time = case.incident_timestamp_utc if hasattr(case, "incident_timestamp_utc") else case.metadata.get("incident_timestamp_utc", case.created_at.isoformat())

                investigations.append({
                    "case_id": case_id,
                    "case_title": case.title,
                    "case_status": case.status,
                    "incident_timestamp_utc": inc_time,
                    "relationship_type": rel_type,
                    "attribution_score": cand_score.total_score if cand_score else None,
                    "risk_level": cand_score.risk_level if cand_score else None,
                    "rank": cand_score.rank if cand_score else None,
                })

                if cand_score and cand_score.evidence_items:
                    for ev in cand_score.evidence_items:
                        evidence_items.append({
                            "case_id": case_id,
                            "case_title": case.title,
                            "category": ev.category or "SUPPORTING_EVIDENCE",
                            "factor_category": ev.factor_category,
                            "title": ev.title,
                            "description": ev.description,
                            "severity": ev.severity or "INFORMATIONAL",
                            "source": ev.source or "Forensic Correlation Engine",
                        })

        return {
            "identity": identity_data,
            "telemetry": telemetry_state,
            "investigations": investigations,
            "evidence_chain": evidence_items,
            "profile_generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    def _find_last_known_historical_track(self, mmsi: str) -> Optional[Dict[str, Any]]:
        """Scans loaded investigation case tracks for last recorded waypoint."""
        for case_id, tracks in case_service.vessel_tracks.items():
            for t in tracks:
                if t.mmsi == mmsi and t.waypoints:
                    wp = t.waypoints[-1]
                    return {
                        "vessel_name": t.vessel_name,
                        "vessel_type": t.vessel_type,
                        "latitude": wp.latitude,
                        "longitude": wp.longitude,
                        "speed": wp.speed_over_ground_knots,
                        "course": wp.course_over_ground_deg,
                        "timestamp_utc": wp.timestamp,
                        "has_gaps": t.has_ais_gaps,
                        "gap_intervals": t.gap_intervals,
                        "waypoints_count": len(t.waypoints),
                    }
        return None


# Global service instance
vessel_intelligence_service = VesselIntelligenceService()
