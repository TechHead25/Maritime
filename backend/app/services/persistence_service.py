"""Durable Atomic Persistence Service for Investigation Execution Results and Artifacts."""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

logger = logging.getLogger("maritime-oil-attribution.persistence")


class PersistenceService:
    """Safely and atomically persists investigation execution results, configurations, and provenance."""

    def __init__(self, base_cases_dir: Optional[Path] = None):
        self.base_cases_dir = base_cases_dir or Path("data/cases")

    def get_case_dir(self, case_id: str) -> Path:
        """Resolves the root directory for a specific case."""
        return self.base_cases_dir / case_id

    def persist_investigation_run(
        self,
        case_id: str,
        investigation_result_dict: Dict[str, Any],
        config_dict: Dict[str, Any],
        execution_duration_sec: float = 0.0,
    ) -> Path:
        """Atomically writes investigation results, execution config, and provenance to disk.
        
        Args:
            case_id: Target case identifier.
            investigation_result_dict: Full serialized investigation result payload.
            config_dict: Execution options and parameters dictionary.
            execution_duration_sec: Measured pipeline runtime in seconds.
            
        Returns:
            Path to the verified investigation_result.json file.
        """
        case_dir = self.get_case_dir(case_id)
        if not case_dir.exists():
            case_dir.mkdir(parents=True, exist_ok=True)

        # Ensure structured artifact directories exist
        (case_dir / "inputs").mkdir(exist_ok=True)
        (case_dir / "outputs").mkdir(exist_ok=True)
        (case_dir / "figures").mkdir(exist_ok=True)
        (case_dir / "reports").mkdir(exist_ok=True)

        # 1. Persist investigation_config.json
        config_path = case_dir / "investigation_config.json"
        self._atomic_write_json(config_path, config_dict)

        # 2. Persist provenance.json
        provenance = {
            "case_id": case_id,
            "pipeline_version": "0.1.0-mvp",
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "execution_duration_sec": round(execution_duration_sec, 3),
            "engine_components": {
                "sar_detector": "DeterministicSARDetector (CFAR & Morphological Segmentation)",
                "drift_engine": "Lagrangian2DDriftEngine (Forward Euler & Runge-Kutta Advection)",
                "ais_interceptor": "AISEngine (Geodesic CPA & Spatiotemporal Envelope Interceptor)",
                "attribution_engine": "ScoringEngine (5-Factor Calibrated Forensic Scoring Matrix)",
            },
            "parameters": config_dict,
            "status": "PERSISTENCE_VERIFIED"
        }
        provenance_path = case_dir / "provenance.json"
        self._atomic_write_json(provenance_path, provenance)

        # 3. Persist investigation_result.json atomically and verify integrity
        result_path = case_dir / "investigation_result.json"
        self._atomic_write_json(result_path, investigation_result_dict)

        # Also write a copy to outputs/ for historical archive
        output_archive_path = case_dir / "outputs" / "investigation_result.json"
        self._atomic_write_json(output_archive_path, investigation_result_dict)

        # 4. Update case.json status to ATTRIBUTION_COMPLETED
        case_file = case_dir / "case.json"
        if case_file.exists():
            try:
                with open(case_file, "r", encoding="utf-8") as f:
                    case_data = json.load(f)
                case_data["status"] = "ATTRIBUTION_COMPLETED"
                case_data["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._atomic_write_json(case_file, case_data)
            except Exception as e:
                logger.warning(f"Failed to update status in case.json: {e}")

        logger.info(f"Successfully persisted complete investigation results for '{case_id}' in '{case_dir}'")
        return result_path

    def load_investigation_run(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Loads and verifies a persisted investigation result from disk."""
        case_dir = self.get_case_dir(case_id)
        result_path = case_dir / "investigation_result.json"

        if not result_path.exists():
            return None

        try:
            with open(result_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Sanity verification
            if not isinstance(data, dict) or "attribution_scores" not in data:
                logger.warning(f"Corrupted or invalid investigation result format in {result_path}")
                return None

            return data
        except Exception as e:
            logger.error(f"Failed to load persisted investigation result from {result_path}: {e}")
            return None

    def persist_versioned_run(
        self,
        case_id: str,
        investigation_result_dict: Dict[str, Any],
        config_dict: Dict[str, Any],
        execution_duration_sec: float = 0.0,
    ) -> Dict[str, Any]:
        """Persists a new numbered, immutable run under data/cases/{case_id}/runs/."""
        case_dir = self.get_case_dir(case_id)
        runs_dir = case_dir / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = runs_dir / "manifest.json"
        manifest: List[Dict[str, Any]] = []
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                manifest = []

        next_run_num = len(manifest) + 1
        run_id = f"run_{next_run_num}"
        run_file = runs_dir / f"{run_id}.json"

        # Write run file
        run_payload = {
            "run_id": run_id,
            "case_id": case_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "duration_sec": round(execution_duration_sec, 2),
            "config": config_dict,
            "results": investigation_result_dict,
        }
        self._atomic_write_json(run_file, run_payload)

        # Update manifest
        scores = investigation_result_dict.get("attribution_scores", [])
        top_cand = scores[0].get("candidate_name") if scores else "None"
        top_score = scores[0].get("total_score") if scores else 0.0

        run_summary = {
            "run_id": run_id,
            "run_number": next_run_num,
            "created_at_utc": run_payload["created_at_utc"],
            "duration_sec": run_payload["duration_sec"],
            "candidates_count": len(investigation_result_dict.get("candidate_vessels", [])),
            "top_candidate": top_cand,
            "top_score": round(float(top_score), 1),
            "origin_centroid": investigation_result_dict.get("origin_centroid"),
            "config": config_dict,
        }
        manifest.append(run_summary)
        self._atomic_write_json(manifest_path, manifest)

        # Also maintain latest investigation_result.json
        self.persist_investigation_run(
            case_id=case_id,
            investigation_result_dict=investigation_result_dict,
            config_dict=config_dict,
            execution_duration_sec=execution_duration_sec,
        )

        logger.info(f"Persisted versioned run '{run_id}' for case '{case_id}'")
        return run_summary

    def list_case_runs(self, case_id: str) -> List[Dict[str, Any]]:
        """Lists all persisted historical runs for a case."""
        case_dir = self.get_case_dir(case_id)
        manifest_path = case_dir / "runs" / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def load_case_run(self, case_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Loads a specific historical versioned run."""
        case_dir = self.get_case_dir(case_id)
        run_file = case_dir / "runs" / f"{run_id}.json"
        if not run_file.exists():
            return None
        try:
            with open(run_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load run {run_id} for case {case_id}: {e}")
            return None

    def compare_case_runs(self, case_id: str, run_id_a: str, run_id_b: str) -> Dict[str, Any]:
        """Compares two historical investigation runs and calculates differences."""
        data_a = self.load_case_run(case_id, run_id_a)
        data_b = self.load_case_run(case_id, run_id_b)

        if not data_a or not data_b:
            raise ValueError(f"One or both runs ('{run_id_a}', '{run_id_b}') not found for case '{case_id}'.")

        cfg_a = data_a.get("config", {})
        cfg_b = data_b.get("config", {})

        # Compute parameter deltas
        all_keys = set(cfg_a.keys()).union(set(cfg_b.keys()))
        param_diffs = {}
        for k in all_keys:
            val_a = cfg_a.get(k)
            val_b = cfg_b.get(k)
            if val_a != val_b:
                param_diffs[k] = {"run_a": val_a, "run_b": val_b}

        # Compare candidates
        scores_a = data_a.get("results", {}).get("attribution_scores", [])
        scores_b = data_b.get("results", {}).get("attribution_scores", [])

        top_a = scores_a[0] if scores_a else {}
        top_b = scores_b[0] if scores_b else {}

        # Compare origin centroids
        orig_a = data_a.get("results", {}).get("origin_centroid", {})
        orig_b = data_b.get("results", {}).get("origin_centroid", {})

        return {
            "case_id": case_id,
            "run_a": {
                "run_id": run_id_a,
                "created_at_utc": data_a.get("created_at_utc"),
                "top_candidate": top_a.get("candidate_name"),
                "top_score": top_a.get("total_score"),
                "candidates_count": len(scores_a),
            },
            "run_b": {
                "run_id": run_id_b,
                "created_at_utc": data_b.get("created_at_utc"),
                "top_candidate": top_b.get("candidate_name"),
                "top_score": top_b.get("total_score"),
                "candidates_count": len(scores_b),
            },
            "parameter_changes": param_diffs,
            "candidate_ranking_changed": top_a.get("mmsi") != top_b.get("mmsi"),
            "origin_centroid_a": orig_a,
            "origin_centroid_b": orig_b,
        }

    def delete_case(self, case_id: str) -> bool:
        """Deletes a case and its persisted directory."""
        import shutil
        case_dir = self.get_case_dir(case_id)
        if case_dir.exists():
            shutil.rmtree(case_dir)
            logger.info(f"Successfully deleted case directory: {case_dir}")
            return True
        return False

    def _atomic_write_json(self, target_path: Path, data: Any):
        """Writes JSON to a temporary file in the target directory and atomically replaces it."""
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        temp_file = target_dir / f".{target_path.name}.{os.getpid()}_{time.time_ns()}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())

            # Verify readability before replace
            with open(temp_file, "r", encoding="utf-8") as f:
                json.load(f)

            # Atomic replace
            os.replace(temp_file, target_path)
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass


persistence_service = PersistenceService()

