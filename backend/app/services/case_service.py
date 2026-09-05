"""Case Service managing investigation case lifecycles, persistence, and disk loading."""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from backend.app.models.schemas import (
    InvestigationCase,
    SARScene,
    SlickDetection,
    SlickPolygon,
    DriftSimulation,
    ProbabilityCloud,
    ReleaseWindow,
    VesselTrack,
    CandidateVessel,
    AttributionScore,
    CaseStatus,
)
from backend.app.services.case_loader import load_case_from_disk, LoadedCase
from backend.app.services.drift_engine import DriftSimulationResult

logger = logging.getLogger("maritime-oil-attribution.case_service")


class CaseService:
    """In-memory and disk-backed Case management service."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("data/cases")
        self.cases: Dict[str, InvestigationCase] = {}
        self.sar_scenes: Dict[str, List[SARScene]] = {}
        self.slicks: Dict[str, List[SlickDetection]] = {}
        self.vessel_tracks: Dict[str, List[VesselTrack]] = {}
        self.environments: Dict[str, Dict[str, Any]] = {}
        self.drift_sims: Dict[str, List[DriftSimulation]] = {}
        self.probability_clouds: Dict[str, List[ProbabilityCloud]] = {}
        self.release_windows: Dict[str, List[ReleaseWindow]] = {}
        self.latest_drift_results: Dict[str, DriftSimulationResult] = {}
        self.candidates: Dict[str, List[CandidateVessel]] = {}
        self.attribution_scores: Dict[str, List[AttributionScore]] = {}
        self.investigation_results: Dict[str, Any] = {}
        
        # Load available cases from disk
        self.reload_cases_from_disk()

    def reload_cases_from_disk(self):
        """Scans the cases directory and loads all valid case folders into memory."""
        if not self.data_dir.exists():
            logger.warning(f"Data directory {self.data_dir} does not exist. Skipping disk reload.")
            return

        loaded_count = 0
        for sub_dir in self.data_dir.iterdir():
            if sub_dir.is_dir() and (sub_dir / "case.json").exists():
                try:
                    loaded: LoadedCase = load_case_from_disk(sub_dir)
                    case_id = loaded.case.id
                    
                    self.cases[case_id] = loaded.case
                    self.sar_scenes[case_id] = [loaded.sar_scene]
                    self.slicks[case_id] = [loaded.slick_detection]
                    self.vessel_tracks[case_id] = loaded.vessel_tracks
                    self.environments[case_id] = {
                        "ocean_currents": loaded.environment.ocean_currents,
                        "wind_data": loaded.environment.wind_data,
                    }

                    # Load persisted investigation results if present
                    res_file = sub_dir / "investigation_result.json"
                    if res_file.exists():
                        try:
                            with open(res_file, "r", encoding="utf-8") as f:
                                res_data = json.load(f)
                            self.investigation_results[case_id] = res_data
                            
                            if "drift_simulations" in res_data and res_data["drift_simulations"]:
                                self.drift_sims[case_id] = [DriftSimulation(**d) for d in res_data["drift_simulations"]]
                            if "probability_clouds" in res_data and res_data["probability_clouds"]:
                                self.probability_clouds[case_id] = [ProbabilityCloud(**c) for c in res_data["probability_clouds"]]
                            if "release_windows" in res_data and res_data["release_windows"]:
                                self.release_windows[case_id] = [ReleaseWindow(**rw) for rw in res_data["release_windows"]]
                            
                            cands_raw = res_data.get("candidate_vessels") or res_data.get("candidates") or []
                            if cands_raw:
                                self.candidates[case_id] = [CandidateVessel(**cand) for cand in cands_raw]
                            
                            if "attribution_scores" in res_data and res_data["attribution_scores"]:
                                self.attribution_scores[case_id] = [AttributionScore(**score) for score in res_data["attribution_scores"]]
                            logger.info(f"Loaded persisted investigation results for case '{case_id}' from disk.")
                        except Exception as e:
                            logger.warning(f"Failed to parse persisted investigation result for case '{case_id}': {e}")

                    loaded_count += 1
                    logger.info(f"Successfully loaded case '{case_id}' from {sub_dir}")
                except Exception as e:
                    logger.error(f"Failed to load case from {sub_dir}: {e}", exc_info=True)

        logger.info(f"CaseService initialized with {loaded_count} cases from disk.")

    def list_cases(self, include_synthetic: bool = False) -> List[InvestigationCase]:
        """Returns a list of all active investigation cases, filtering synthetic benchmark scenarios in production."""
        allow_synthetic = os.getenv("ALLOW_SYNTHETIC_PROVIDERS", "false").lower() in ("true", "1")
        if include_synthetic or allow_synthetic:
            return list(self.cases.values())
        return [
            c for c in self.cases.values()
            if not (c.metadata and c.metadata.get("synthetic"))
            and not c.id.startswith("demo-")
            and not c.id.startswith("demo_")
        ]

    def get_case(self, case_id: str) -> Optional[InvestigationCase]:
        """Returns the base InvestigationCase model or None if not found."""
        return self.cases.get(case_id)

    def create_case(
        self,
        title: str,
        region_of_interest: Optional[SlickPolygon] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InvestigationCase:
        """Creates a new in-memory investigation case."""
        case = InvestigationCase(
            title=title,
            region_of_interest=region_of_interest,
            metadata=metadata or {}
        )
        self.cases[case.id] = case
        self.sar_scenes[case.id] = []
        self.slicks[case.id] = []
        self.vessel_tracks[case.id] = []
        self.environments[case.id] = {}
        logger.info(f"Created new investigation case '{case.id}' with title '{case.title}'.")
        return case

    def save_drift_result(self, case_id: str, result: DriftSimulationResult):
        """Saves drift simulation outputs to the case state."""
        self.drift_sims[case_id] = [result.simulation]
        self.release_windows[case_id] = [result.release_window]
        self.probability_clouds[case_id] = result.probability_clouds
        self.latest_drift_results[case_id] = result
        
        if case_id in self.cases:
            self.cases[case_id].status = CaseStatus.DRIFT_SIMULATED
            self.cases[case_id].updated_at = datetime.now(timezone.utc)
        logger.info(f"Saved drift simulation '{result.simulation.id}' for case '{case_id}'.")

    def get_latest_drift_result(self, case_id: str) -> Optional[DriftSimulationResult]:
        """Returns the most recent DriftSimulationResult for the case."""
        return self.latest_drift_results.get(case_id)

    def get_investigation_result(self, case_id: str) -> Optional[Any]:
        """Returns the persisted or active complete investigation result for a case."""
        return self.investigation_results.get(case_id)

    def get_case_details(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Returns complete case details including SAR, slick, vessel tracks, and environment."""
        case = self.cases.get(case_id)
        if not case:
            return None

        return {
            "case": case,
            "sar_scenes": self.sar_scenes.get(case_id, []),
            "slicks": self.slicks.get(case_id, []),
            "vessel_tracks": self.vessel_tracks.get(case_id, []),
            "environment": self.environments.get(case_id, {}),
            "drift_simulations": self.drift_sims.get(case_id, []),
            "probability_clouds": self.probability_clouds.get(case_id, []),
            "release_windows": self.release_windows.get(case_id, []),
            "candidates": self.candidates.get(case_id, []),
            "attribution_scores": self.attribution_scores.get(case_id, [])
        }

    def get_case_summary(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Returns a consolidated high-level summary of the case."""
        case = self.cases.get(case_id)
        if not case:
            return None

        sar_scenes = self.sar_scenes.get(case_id, [])
        slicks = self.slicks.get(case_id, [])
        tracks = self.vessel_tracks.get(case_id, [])
        env = self.environments.get(case_id, {})

        primary_sar = sar_scenes[0] if sar_scenes else None
        primary_slick = slicks[0] if slicks else None

        vessel_summaries = []
        for t in tracks:
            vessel_summaries.append({
                "mmsi": t.mmsi,
                "vessel_name": t.vessel_name,
                "vessel_type": t.vessel_type.value,
                "flag_country": t.flag_country,
                "waypoint_count": len(t.waypoints),
                "has_ais_gaps": t.has_ais_gaps
            })

        return {
            "case_id": case.id,
            "title": case.title,
            "status": case.status.value,
            "created_at": case.created_at.isoformat(),
            "region_of_interest": case.region_of_interest.model_dump() if case.region_of_interest else None,
            "synthetic": case.metadata.get("synthetic", False),
            "sar_scene": {
                "id": primary_sar.id,
                "platform": primary_sar.satellite_platform,
                "acquisition_timestamp": primary_sar.acquisition_timestamp.isoformat(),
                "sensor_mode": primary_sar.sensor_mode
            } if primary_sar else None,
            "slick_detection": {
                "id": primary_slick.id,
                "centroid": primary_slick.centroid.model_dump(),
                "area_sq_km": primary_slick.area_sq_km,
                "perimeter_km": primary_slick.perimeter_km,
                "orientation_deg": primary_slick.major_axis_orientation_deg,
                "confidence_score": primary_slick.confidence_score
            } if primary_slick else None,
            "vessel_count": len(tracks),
            "vessels": vessel_summaries,
            "ocean_currents": env.get("ocean_currents", {}).get("mean_current_vectors") if "ocean_currents" in env else None,
            "wind_data": env.get("wind_data", {}).get("mean_wind_vectors") if "wind_data" in env else None
        }


# Global instance
case_service = CaseService()
