"""API Router for Investigation Cases, Health, Drift Simulation, and Pipelines."""

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Path, Query, UploadFile, status
from pydantic import BaseModel, Field

from backend.app.models.schemas import (
    InvestigationCase,
    SARScene,
    SlickDetection,
    SlickPolygon,
    DriftSimulation,
    ProbabilityCloud,
    ReleaseWindow,
    GeoPoint,
    VesselTrack,
    CandidateVessel,
    AttributionScore,
    CaseStatus,
    SARCandidateCollectionResponse,
)
from backend.app.services.case_service import case_service
from backend.app.services.case_creation_service import case_creation_service
from backend.app.services.drift_engine import (
    DriftEngine,
    DriftEngineConfig,
    DriftSimulationResult,
)
from backend.app.services.pipeline_service import (
    pipeline_service,
    PipelineOptions,
    FullInvestigationResponse,
)
from backend.app.services.sar_detector import (
    sar_detector,
    SyntheticSARGenerator,
)
from backend.app.providers.base import (
    BoundingBox,
    SARQuery,
    ProviderUnavailableError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderCoverageError,
    NoSARObservationError,
)
from backend.app.providers.registry import provider_registry
from backend.app.services.live_ais_service import live_ais_service, PREDEFINED_REGIONS
from backend.app.services.data_readiness_service import data_readiness_service
from backend.app.services.persistence_service import persistence_service
from backend.app.services.vessel_intelligence_service import vessel_intelligence_service
from backend.app.services.data_source_control_service import data_source_control_service
from fastapi.responses import FileResponse, StreamingResponse

logger = logging.getLogger("maritime-oil-attribution.api")
api_router = APIRouter()


# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Health check diagnostic payload."""
    status: str = "healthy"
    service: str = "Maritime Oil-Spill Attribution Intelligence API"
    version: str = "0.1.0"
    timestamp_utc: str
    loaded_cases_count: int


class CreateCaseRequest(BaseModel):
    """Payload for creating a new investigation case."""
    title: str = Field(..., min_length=1, max_length=255, description="Case title")
    region_of_interest: Optional[SlickPolygon] = Field(default=None, description="Bounding region polygon")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata dictionary")


class RunDriftRequest(BaseModel):
    """Configuration options for triggering backward Lagrangian drift simulation."""
    time_step_minutes: int = Field(default=30, ge=5, le=120, description="Integration timestep in minutes (5 - 120)")
    max_hours_backward: float = Field(default=48.0, gt=0.0, le=168.0, description="Historical simulation horizon in hours")
    particle_count: int = Field(default=1000, ge=10, le=10000, description="Monte Carlo particle swarm size")
    wind_leeway_factor: float = Field(default=0.03, ge=0.0, le=0.10, description="Wind leeway factor (standard: 0.03)")
    current_advection_factor: float = Field(default=1.00, ge=0.5, le=2.0, description="Current scaling coefficient")
    horizontal_diffusivity_m2_s: float = Field(default=2.5, ge=0.0, le=50.0, description="Turbulent eddy diffusivity (m^2/s)")
    random_seed: int = Field(default=42, description="Fixed random seed for deterministic reproducibility")
    estimated_release_hours_ago: float = Field(default=14.0, ge=0.0, description="Estimated hours before SAR observation for release peak")
    release_window_half_width_hours: float = Field(default=2.0, gt=0.0, description="Half-window duration width (hours)")


class DriftSimulationResponse(BaseModel):
    """Output payload of backward Lagrangian drift simulation."""
    case_id: str
    simulation: DriftSimulation
    release_window: ReleaseWindow
    probability_clouds: List[ProbabilityCloud]
    origin_centroid: GeoPoint
    origin_uncertainty_radius_km: float
    step_count: int
    status: str = "DRIFT_SIMULATION_COMPLETED"


class CaseDetailResponse(BaseModel):
    """Detailed response containing all related case artifacts and telemetry."""
    case: InvestigationCase
    sar_scenes: List[SARScene]
    slicks: List[SlickDetection]
    vessel_tracks: List[VesselTrack]
    environment: Dict[str, Any]
    drift_simulations: List[Any]
    probability_clouds: List[Any]
    release_windows: List[Any]
    candidates: List[CandidateVessel]
    attribution_scores: List[AttributionScore]


class CaseSummaryResponse(BaseModel):
    """Consolidated high-level summary of an investigation case."""
    case_id: str
    title: str
    status: str
    created_at: str
    region_of_interest: Optional[Dict[str, Any]] = None
    synthetic: bool = False
    sar_scene: Optional[Dict[str, Any]] = None
    slick_detection: Optional[Dict[str, Any]] = None
    vessel_count: int
    vessels: List[Dict[str, Any]]
    ocean_currents: Optional[Dict[str, Any]] = None
    wind_data: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------

@api_router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint verifying API service status and loaded cases."""
    from datetime import datetime, timezone
    cases = case_service.list_cases()
    return HealthResponse(
        status="healthy",
        service="Maritime Oil-Spill Attribution Intelligence API",
        version="0.1.0",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        loaded_cases_count=len(cases)
    )


@api_router.get("/health/live", tags=["Health"])
def liveness_check():
    """Kubernetes / Docker liveness probe endpoint."""
    return {"status": "alive", "timestamp_utc": datetime.now(timezone.utc).isoformat()}


@api_router.get("/health/ready", tags=["Health"])
def readiness_check():
    """Kubernetes / Docker readiness probe endpoint verifying case loading."""
    cases_count = len(case_service.list_cases())
    return {
        "status": "ready",
        "loaded_cases_count": cases_count,
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }


@api_router.get("/cases", response_model=List[InvestigationCase], tags=["Cases"])
def list_cases(
    include_synthetic: bool = Query(False, description="Whether to include synthetic test benchmark cases")
):
    """Retrieve all investigation cases loaded from disk and in memory."""
    cases = case_service.list_cases(include_synthetic=include_synthetic)
    logger.info(f"Listing {len(cases)} active investigation cases (include_synthetic={include_synthetic}).")
    return cases


@api_router.post("/cases", response_model=InvestigationCase, status_code=status.HTTP_201_CREATED, tags=["Cases"])
def create_case(req: CreateCaseRequest):
    """Create a new in-memory investigation case."""
    logger.info(f"Creating case: {req.title}")
    return case_service.create_case(
        title=req.title,
        region_of_interest=req.region_of_interest,
        metadata=req.metadata
    )


@api_router.post("/cases/create-investigation", response_model=InvestigationCase, status_code=status.HTTP_201_CREATED, tags=["Cases"])
async def create_investigation(
    title: str = Form(..., min_length=1, max_length=255),
    description: Optional[str] = Form(None),
    incident_timestamp: Optional[str] = Form(None),
    min_lon: float = Form(80.0),
    min_lat: float = Form(5.0),
    max_lon: float = Form(85.0),
    max_lat: float = Form(10.0),
    ais_file: Optional[UploadFile] = File(None),
    sar_file: Optional[UploadFile] = File(None),
    ocean_file: Optional[UploadFile] = File(None),
    wind_file: Optional[UploadFile] = File(None),
):
    """Securely uploads raw datasets and generates a new persistent investigation case."""
    logger.info(f"Creating custom investigation case: '{title}' with coordinates bbox=[{min_lon}, {min_lat}, {max_lon}, {max_lat}]")
    
    ais_content = await ais_file.read() if ais_file else None
    sar_content = await sar_file.read() if sar_file else None
    ocean_content = await ocean_file.read() if ocean_file else None
    wind_content = await wind_file.read() if wind_file else None

    try:
        case = case_creation_service.create_investigation(
            title=title,
            description=description,
            incident_timestamp_str=incident_timestamp,
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            ais_filename=ais_file.filename if ais_file else None,
            ais_content=ais_content,
            sar_filename=sar_file.filename if sar_file else None,
            sar_content=sar_content,
            ocean_filename=ocean_file.filename if ocean_file else None,
            ocean_content=ocean_content,
            wind_filename=wind_file.filename if wind_file else None,
            wind_content=wind_content,
        )
        return case
    except ValueError as e:
        logger.warning(f"Case creation validation failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating investigation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing investigation datasets: {str(e)}"
        )


@api_router.get("/cases/{case_id}", response_model=CaseDetailResponse, tags=["Cases"])
def get_case(
    case_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$", min_length=1, max_length=128, description="The unique identifier of the investigation case")
):
    """Get full details of a specific investigation case (SAR, Slicks, Vessel Tracks, Environment)."""
    logger.info(f"Fetching full details for case_id='{case_id}'")
    details = case_service.get_case_details(case_id)
    if not details:
        logger.warning(f"Case with ID '{case_id}' not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID '{case_id}' was not found in data stores."
        )
    return details


@api_router.get("/cases/{case_id}/investigation", response_model=FullInvestigationResponse, tags=["Investigation Pipeline"])
def get_investigation_result(
    case_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$", min_length=1, max_length=128, description="The unique identifier of the investigation case")
):
    """Get the persisted or active complete forensic investigation result for a case."""
    logger.info(f"Fetching persisted investigation result for case_id='{case_id}'")
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID '{case_id}' was not found."
        )

    res = case_service.get_investigation_result(case_id)
    if not res:
        # Check on disk via persistence service
        from backend.app.services.persistence_service import persistence_service
        res = persistence_service.load_investigation_run(case_id)
        if res:
            case_service.investigation_results[case_id] = res

    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No completed investigation result found for case '{case_id}'. Execute the pipeline first."
        )
    return res


@api_router.get("/cases/{case_id}/summary", response_model=CaseSummaryResponse, tags=["Cases"])
def get_case_summary(
    case_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$", min_length=1, max_length=128, description="The unique identifier of the investigation case")
):
    """Get a high-level summary of an investigation case for rapid triage and dashboards."""
    logger.info(f"Fetching summary for case_id='{case_id}'")
    summary = case_service.get_case_summary(case_id)
    if not summary:
        logger.warning(f"Case summary with ID '{case_id}' not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID '{case_id}' was not found."
        )
    return summary


# ---------------------------------------------------------------------------
# Drift Simulation Endpoints
# ---------------------------------------------------------------------------

@api_router.post("/cases/{case_id}/drift", response_model=DriftSimulationResponse, tags=["Drift Engine"])
def run_drift_simulation(
    case_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$", min_length=1, max_length=128, description="The unique identifier of the investigation case"),
    req: RunDriftRequest = RunDriftRequest()
):
    """Executes a 2D backward Lagrangian particle drift simulation for a case."""
    logger.info(f"Running drift simulation for case_id='{case_id}' with {req.particle_count} particles.")
    
    # 1. Load case
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID '{case_id}' was not found."
        )

    # 2. Load slicks and SAR scenes
    slicks = case_service.slicks.get(case_id, [])
    if not slicks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No oil slick detection found for case '{case_id}'. Cannot execute drift simulation."
        )
    primary_slick = slicks[0]

    sar_scenes = case_service.sar_scenes.get(case_id, [])
    obs_timestamp = sar_scenes[0].acquisition_timestamp if sar_scenes else case.created_at

    # 3. Load environmental data
    env = case_service.environments.get(case_id, {})
    ocean_data = env.get("ocean_currents")
    wind_data = env.get("wind_data")

    # 4. Configure and run drift engine
    config = DriftEngineConfig(
        time_step_minutes=req.time_step_minutes,
        max_hours_backward=req.max_hours_backward,
        particle_count=req.particle_count,
        wind_leeway_factor=req.wind_leeway_factor,
        current_advection_factor=req.current_advection_factor,
        horizontal_diffusivity_m2_s=req.horizontal_diffusivity_m2_s,
        random_seed=req.random_seed
    )
    engine = DriftEngine(config=config)

    sim_result: DriftSimulationResult = engine.run_backward_drift(
        slick_detection=primary_slick,
        observation_timestamp=obs_timestamp,
        ocean_current_data=ocean_data,
        wind_data=wind_data,
        estimated_release_hours_ago=req.estimated_release_hours_ago,
        release_window_half_width_hours=req.release_window_half_width_hours
    )

    # 5. Save simulation result to case state
    case_service.save_drift_result(case_id=case_id, result=sim_result)

    return DriftSimulationResponse(
        case_id=case_id,
        simulation=sim_result.simulation,
        release_window=sim_result.release_window,
        probability_clouds=sim_result.probability_clouds,
        origin_centroid=sim_result.origin_centroid,
        origin_uncertainty_radius_km=sim_result.origin_uncertainty_radius_km,
        step_count=len(sim_result.probability_clouds),
        status="DRIFT_SIMULATION_COMPLETED"
    )


@api_router.get("/cases/{case_id}/drift", response_model=DriftSimulationResponse, tags=["Drift Engine"])
def get_latest_drift_simulation(
    case_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$", min_length=1, max_length=128, description="The unique identifier of the investigation case")
):
    """Retrieves the most recent backward drift simulation computed for a case."""
    logger.info(f"Retrieving latest drift simulation for case_id='{case_id}'")
    
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID '{case_id}' was not found."
        )

    sim_result = case_service.get_latest_drift_result(case_id)
    if not sim_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No drift simulation has been computed yet for case '{case_id}'. Trigger POST /api/cases/{case_id}/drift first."
        )

    return DriftSimulationResponse(
        case_id=case_id,
        simulation=sim_result.simulation,
        release_window=sim_result.release_window,
        probability_clouds=sim_result.probability_clouds,
        origin_centroid=sim_result.origin_centroid,
        origin_uncertainty_radius_km=sim_result.origin_uncertainty_radius_km,
        step_count=len(sim_result.probability_clouds),
        status="DRIFT_SIMULATION_COMPLETED"
    )


# ---------------------------------------------------------------------------
# Complete Investigation Pipeline Endpoints
# ---------------------------------------------------------------------------

@api_router.post("/cases/{case_id}/investigate", response_model=FullInvestigationResponse, tags=["Forensic Pipeline"])
@api_router.post("/cases/{case_id}/run-full-investigation", response_model=FullInvestigationResponse, tags=["Forensic Pipeline"])
def run_investigation_pipeline(
    case_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$", min_length=1, max_length=128, description="The unique identifier of the investigation case"),
    options: PipelineOptions = PipelineOptions()
):
    """Executes the complete end-to-end maritime forensic investigation pipeline.
    
    Pipeline Stages:
    1. Case Validation & Synthetic SAR Slick Extraction
    2. Backward Lagrangian Particle Drift Simulation
    3. Origin Estimation & Release Window Bracketing
    4. AIS Spatiotemporal Trajectory Interception & Gap Analysis
    5. Multi-Factor Explainable Attribution Scoring Matrix
    6. Complete Verifiable Evidence Chain Assembly
    """
    logger.info(f"Executing full forensic pipeline for case_id='{case_id}'")
    try:
        response = pipeline_service.run_pipeline(case_id=case_id, options=options)
        return response
    except ValueError as e:
        logger.warning(f"Pipeline error for case '{case_id}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected pipeline failure for case '{case_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pipeline error: {str(e)}")


# ---------------------------------------------------------------------------
# SAR Lookalike Candidate Collection Endpoints
# ---------------------------------------------------------------------------

@api_router.get(
    "/cases/{case_id}/sar-candidates",
    response_model=SARCandidateCollectionResponse,
    tags=["SAR Detection & Lookalikes"],
)
def get_sar_candidates(
    case_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$", min_length=1, max_length=128, description="The unique identifier of the investigation case")
):
    """Retrieves all detected SAR candidate dark patches, including accepted slicks and rejected lookalikes with audit reasons."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID '{case_id}' was not found."
        )

    sar_scenes = case_service.sar_scenes.get(case_id, [])
    if not sar_scenes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No SAR scene metadata available for case '{case_id}'."
        )
    primary_scene = sar_scenes[0]

    # Ingest georeferenced SAR raster via historical adapter or registered SAR provider
    from backend.app.providers.sar_adapter import HistoricalSARAdapter
    sar_prov = HistoricalSARAdapter(seed=42)
    if sar_prov.is_available():
        raster = sar_prov.fetch_raster(primary_scene)
    elif provider_registry.allow_synthetic or (case.metadata and case.metadata.get("synthetic")):
        raster = SyntheticSARGenerator.create_synthetic_scene(seed=42)
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data source unavailable: Calibrated SAR backscatter raster is missing for scene '{primary_scene.id}'. Zero synthetic fallback permitted in production."
        )

    response = sar_detector.get_candidate_collection(
        case_id=case_id,
        scene=primary_scene,
        raster=raster,
    )
    return response


@api_router.get(
    "/cases/{case_id}/sar-image",
    tags=["SAR Detection & Lookalikes"],
    summary="Retrieve Processed SAR Radar Imagery & Diagnostics",
)
def get_case_sar_image(
    case_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$", min_length=1, max_length=128, description="The unique identifier of the investigation case"),
    view: str = Query("diagnostics", description="View type: 'diagnostics' (6-panel suite) or 'detection' (radar slick crop)"),
    force_refresh: bool = Query(False, description="Bypass cache and re-render image"),
):
    """Dynamically generates and streams high-resolution case-specific SAR radar diagnostics or slick detection plot."""
    import io
    from fastapi.responses import StreamingResponse
    from backend.app.services.sar_visualizer import sar_visualizer

    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID '{case_id}' was not found.",
        )

    sar_scenes = case_service.sar_scenes.get(case_id, [])
    if not sar_scenes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No SAR scene metadata available for case '{case_id}'.",
        )
    primary_scene = sar_scenes[0]

    slicks = case_service.slicks.get(case_id, [])
    if not slicks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No slick detection available for case '{case_id}'.",
        )
    primary_slick = slicks[0]

    # Ingest / build georeferenced SAR raster tailored to this case
    if case_id == "case_new_diamond_2020" or "new-diamond" in primary_scene.id:
        from backend.app.providers.sar_adapter import HistoricalSARAdapter
        sar_prov = HistoricalSARAdapter(seed=42)
        raster = sar_prov.fetch_raster(primary_scene)
    else:
        # Determine ROI coordinates for this case
        top_lon = 80.15
        top_lat = 13.50
        if primary_scene.footprint_polygon and primary_scene.footprint_polygon.coordinates:
            coords = primary_scene.footprint_polygon.coordinates[0]
            top_lon = min(c[0] for c in coords)
            top_lat = max(c[1] for c in coords)
        elif case.region_of_interest and case.region_of_interest.coordinates:
            coords = case.region_of_interest.coordinates[0]
            top_lon = min(c[0] for c in coords)
            top_lat = max(c[1] for c in coords)
        elif primary_slick.centroid and primary_slick.centroid.coordinates:
            c_lon, c_lat = primary_slick.centroid.coordinates
            top_lon = c_lon - 0.25
            top_lat = c_lat + 0.25

        raster = SyntheticSARGenerator.create_synthetic_scene(
            top_left_lon=round(top_lon, 4),
            top_left_lat=round(top_lat, 4),
            seed=42,
        )

    try:
        img_bytes = sar_visualizer.get_or_render_sar_image(
            case_id=case_id,
            view=view,
            scene=primary_scene,
            slick=primary_slick,
            raster=raster,
            force_refresh=force_refresh,
        )
        return StreamingResponse(
            io.BytesIO(img_bytes),
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-Case-ID": case_id,
                "X-SAR-View": view,
            },
        )
    except Exception as e:
        logger.error(f"Failed to render SAR image for case '{case_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SAR imagery: {str(e)}",
        )



# ---------------------------------------------------------------------------
# Investigation PDF Report Generation Endpoints
# ---------------------------------------------------------------------------

@api_router.get(
    "/cases/{case_id}/report/pdf",
    tags=["Investigation Report"],
    summary="Download Maritime Oil-Spill Investigation Report (PDF)",
)
def download_investigation_report_pdf(
    case_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$", min_length=1, max_length=128, description="The unique identifier of the investigation case")
):
    """Generates and streams the official Maritime Oil-Spill Investigation Report in PDF format."""
    import pathlib
    import tempfile
    from fastapi.responses import FileResponse
    from backend.app.services.report_generator import report_generator

    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID '{case_id}' was not found."
        )

    # Run full investigation pipeline and generate PDF
    try:
        pipeline_resp = pipeline_service.run_pipeline(case_id=case_id)

        output_dir = pathlib.Path(tempfile.gettempdir()) / "maritime_reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_output_path = str(output_dir / f"Investigation_Report_{case_id}.pdf")

        report_generator.generate_pdf(response=pipeline_resp, output_path=pdf_output_path)

        if not os.path.exists(pdf_output_path) or os.path.getsize(pdf_output_path) == 0:
            raise RuntimeError(f"Generated PDF report missing or empty at {pdf_output_path}")

        return FileResponse(
            path=pdf_output_path,
            media_type="application/pdf",
            filename=f"Maritime_Oil_Investigation_Report_{case_id}.pdf",
        )
    except Exception as e:
        logger.error(f"Error executing pipeline or generating PDF report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile investigation report metrics: {str(e)}"
        )


@api_router.get(
    "/cases/{case_id}/report",
    tags=["Investigation Report"],
    summary="Download Maritime Oil-Spill Investigation Report (PDF Alias)",
)
def download_investigation_report_alias(
    case_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$", min_length=1, max_length=128, description="The unique identifier of the investigation case")
):
    """Alias route supporting /cases/{case_id}/report by returning the compiled PDF dossier."""
    return download_investigation_report_pdf(case_id=case_id)


# ---------------------------------------------------------------------------
# Data Sources & Provider Health Endpoints
# ---------------------------------------------------------------------------

@api_router.get(
    "/data-sources",
    tags=["Data Sources"],
    summary="List Registered External Data Providers",
)
def list_data_sources():
    """Returns list of registered external telemetry and model providers."""
    providers = provider_registry.get_all_providers()
    return [
        {
            "name": p.name,
            "provider_type": p.provider_type,
            "is_available": p.is_available(),
            "auth_status": p.get_auth_status(),
            "metadata": p.get_metadata(),
            "freshness": p.get_freshness(),
        }
        for p in providers
    ]


@api_router.get(
    "/data-sources/health",
    tags=["Data Sources"],
    summary="Data Provider Health & Readiness Matrix",
)
def get_data_sources_health():
    """Returns comprehensive health, latency, and credential telemetry for all data providers."""
    return provider_registry.get_health_summary()


class ProviderConfigRequest(BaseModel):
    fallback_enabled: Optional[bool] = Field(None, description="Allow verified local fallback archive if external is unreachable")
    custom_timeout_seconds: Optional[float] = Field(None, ge=1.0, le=60.0, description="HTTP socket connection timeout")
    rate_limit_rpm: Optional[int] = Field(None, ge=1, le=1000, description="Rate limit requests per minute")


@api_router.get(
    "/data-sources/control-center",
    tags=["Data Sources"],
    summary="Comprehensive Data Source Control Center Telemetry",
)
def get_data_sources_control_center():
    """Returns all 6 provider categories with masked authentication, status, latency, and freshness metrics."""
    return {
        "status": "OPERATIONAL",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "providers": data_source_control_service.get_all_providers_status(),
    }


@api_router.post(
    "/data-sources/{provider_id}/ping",
    tags=["Data Sources"],
    summary="Execute Live Latency Ping Probe",
)
def ping_data_source(
    provider_id: str = Path(..., description="Provider category ID (earth_observation, ais, ocean, weather, vessel_identity, basemap)")
):
    """Executes live network HEAD/GET probe against external provider endpoint and returns real latency."""
    return data_source_control_service.ping_provider(provider_id)


@api_router.post(
    "/data-sources/{provider_id}/configure",
    tags=["Data Sources"],
    summary="Update Non-Secret Provider Runtime Parameters",
)
def configure_data_source(
    provider_id: str = Path(..., description="Provider category ID"),
    payload: ProviderConfigRequest = ...
):
    """Safely updates non-secret provider settings without exposing or altering sensitive credentials."""
    return data_source_control_service.update_configuration(
        provider_id=provider_id,
        payload=payload.model_dump(exclude_unset=True)
    )



@api_router.get(
    "/data-sources/{provider}/coverage",
    tags=["Data Sources"],
    summary="Query Provider Coverage Envelope",
)
def check_provider_coverage(
    provider: str = Path(..., description="Provider category: sar, ais, ocean, wind, vessel"),
    min_lon: float = -180.0,
    min_lat: float = -90.0,
    max_lon: float = 180.0,
    max_lat: float = 90.0,
    start_time_iso: Optional[str] = None,
    end_time_iso: Optional[str] = None,
):
    """Checks whether the requested spatiotemporal window falls within provider coverage."""
    start_dt = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00")) if start_time_iso else datetime(2020, 1, 1, tzinfo=timezone.utc)
    end_dt = datetime.fromisoformat(end_time_iso.replace("Z", "+00:00")) if end_time_iso else datetime.now(timezone.utc)

    bbox = BoundingBox(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)

    p_map = {
        "sar": provider_registry._copernicus_sar,
        "ais": provider_registry._live_ais,
        "ocean": provider_registry._copernicus_marine,
        "wind": provider_registry._openmeteo_wind,
        "vessel": provider_registry._vessel_identity,
    }

    prov = p_map.get(provider.lower())
    if not prov:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found. Available: {list(p_map.keys())}")

    covered = prov.check_coverage(bbox, (start_dt, end_dt))
    return {
        "provider": prov.name,
        "provider_type": prov.provider_type,
        "query_bbox": bbox.as_tuple,
        "time_window": (start_dt.isoformat(), end_dt.isoformat()),
        "within_coverage": covered,
    }


# ---------------------------------------------------------------------------
# Copernicus Sentinel-1 SAR Catalogue Search Endpoint
# ---------------------------------------------------------------------------

@api_router.get(
    "/sar/search",
    tags=["SAR Catalogue"],
    summary="Search Copernicus Sentinel-1 Observations",
)
def search_copernicus_sar(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    start_time_iso: str,
    end_time_iso: str,
    sensor_mode: str = "IW",
    polarization: str = "VV",
):
    """Searches official Copernicus Data Space STAC catalogue for Sentinel-1 GRD scenes.

    Returns matching SARScene models. If no scene exists, returns 'No SAR observation available'.
    """
    try:
        start_dt = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time_iso.replace("Z", "+00:00"))
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=f"Invalid ISO datetime string: {val_err}")

    bbox = BoundingBox(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)
    query = SARQuery(
        bbox=bbox,
        start_time=start_dt,
        end_time=end_dt,
        sensor_mode=sensor_mode,
        polarization=polarization,
    )

    sar_prov = provider_registry.get_sar_provider(prefer_historical=False)
    try:
        scenes = sar_prov.search_scenes(query, raise_if_empty=True)
        return {
            "status": "SUCCESS",
            "provider": sar_prov.name,
            "scenes_found": len(scenes),
            "scenes": scenes,
        }
    except NoSARObservationError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No SAR observation available for the requested bounding box and time range.",
        )
    except ProviderError as p_err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(p_err))


# ---------------------------------------------------------------------------
# Production Live AIS Maritime Tracking Endpoints
# ---------------------------------------------------------------------------

class LiveSubscriptionRequest(BaseModel):
    """Payload for updating active geographic subscription zone."""
    region_name: Optional[str] = Field(default=None, description="Predefined region name")
    custom_bbox: Optional[BoundingBox] = Field(default=None, description="Custom viewport bounding box")


@api_router.get(
    "/live/status",
    tags=["Live Maritime Tracking"],
    summary="Get Live AIS Ingestion Health and Connection State",
)
def get_live_status():
    """Returns connection state (LIVE, STALE, or DISCONNECTED), active subscription, and throughput."""
    return live_ais_service.get_health_telemetry()


@api_router.get(
    "/live/vessels",
    tags=["Live Maritime Tracking"],
    summary="Get Real-Time Filtered Vessel States",
)
def get_live_vessels(
    min_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
    max_lat: Optional[float] = None,
    vessel_type: Optional[str] = None,
    min_speed: Optional[float] = None,
):
    """Queries currently tracked live vessels in the active subscription or custom bounding box.

    Zero synthetic vessels are returned. Reports actual provider status.
    """
    bbox = None
    if all(v is not None for v in (min_lon, min_lat, max_lon, max_lat)):
        bbox = BoundingBox(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)

    vessels = live_ais_service.get_live_vessels(
        bbox=bbox,
        vessel_type=vessel_type,
        min_speed=min_speed,
    )

    return {
        "status": live_ais_service.get_status(),
        "configured": live_ais_service.is_configured(),
        "region": live_ais_service.current_region,
        "active_bbox": live_ais_service.active_bbox.as_tuple,
        "total_count": len(vessels),
        "vessels": vessels,
    }


@api_router.get(
    "/live/vessels/{mmsi}",
    tags=["Live Maritime Tracking"],
    summary="Get Detailed Vessel Telemetry and Recent Track Trail",
)
def get_live_vessel_details(
    mmsi: str = Path(..., pattern=r"^\d{9}$", description="9-digit Maritime Mobile Service Identity")
):
    """Retrieves full kinematics, identity particulars, transponder gaps, and historical waypoint trail."""
    details = live_ais_service.get_vessel_details(mmsi)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Live vessel with MMSI '{mmsi}' was not found in active tracking buffer."
        )
    return details


@api_router.post(
    "/live/subscription",
    tags=["Live Maritime Tracking"],
    summary="Update Geographic Subscription Region",
)
def update_live_subscription(payload: LiveSubscriptionRequest):
    """Updates geographic bounding box subscription without full system restart."""
    try:
        if payload.custom_bbox:
            live_ais_service.set_active_region("CUSTOM_VIEWPORT", custom_bbox=payload.custom_bbox)
        elif payload.region_name:
            live_ais_service.set_active_region(payload.region_name)
        else:
            raise HTTPException(status_code=400, detail="Must provide either region_name or custom_bbox.")

        return {
            "status": "SUCCESS",
            "region": live_ais_service.current_region,
            "active_bbox": live_ais_service.active_bbox.as_tuple,
            "available_predefined_regions": list(PREDEFINED_REGIONS.keys()),
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@api_router.get(
    "/live/stream",
    tags=["Live Maritime Tracking"],
    summary="Server-Sent Events (SSE) Live Telemetry Stream",
)
def stream_live_vessels():
    """Event stream delivering real-time vessel position updates directly to open browser clients."""
    return StreamingResponse(
        live_ais_service.event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Real Investigation Discovery, Readiness, Progress & Versioned Runs
# ---------------------------------------------------------------------------

class DataDiscoveryRequest(BaseModel):
    min_lon: float = Field(..., ge=-180.0, le=180.0)
    min_lat: float = Field(..., ge=-90.0, le=90.0)
    max_lon: float = Field(..., ge=-180.0, le=180.0)
    max_lat: float = Field(..., ge=-90.0, le=90.0)
    incident_time_utc: str = Field(..., description="ISO 8601 UTC timestamp")
    window_hours: float = Field(default=48.0, ge=1.0, le=168.0)
    allow_partial_data: bool = Field(default=False)


class ExecuteInvestigationRequest(BaseModel):
    options: Optional[PipelineOptions] = None
    allow_partial_data: bool = False


@api_router.post(
    "/investigations/readiness",
    tags=["Investigation Workspace"],
    summary="Evaluate Data Readiness Matrix across SAR, AIS, Currents, and Winds",
)
def evaluate_investigation_readiness(payload: DataDiscoveryRequest):
    """Discovers available observations from configured providers and calculates forensic readiness."""
    try:
        inc_dt = datetime.fromisoformat(payload.incident_time_utc.replace("Z", "+00:00"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid incident_time_utc format: {e}")

    bbox = BoundingBox(
        min_lon=payload.min_lon,
        min_lat=payload.min_lat,
        max_lon=payload.max_lon,
        max_lat=payload.max_lat,
    )

    assessment = data_readiness_service.discover_and_assess(
        bbox=bbox,
        incident_time=inc_dt,
        analysis_window_hours=payload.window_hours,
        allow_partial_data=payload.allow_partial_data,
    )
    return assessment.model_dump()


@api_router.post(
    "/cases/{case_id}/execute",
    tags=["Investigation Workspace"],
    summary="Start Dynamic Asynchronous Investigation Run with Job Progress",
)
def execute_investigation(
    case_id: str,
    payload: Optional[ExecuteInvestigationRequest] = None,
):
    """Spawns an asynchronous pipeline execution job and returns tracking job ID."""
    opts = payload.options if payload else None
    job_id = pipeline_service.start_investigation_job(case_id=case_id, options=opts)
    return {
        "status": "QUEUED",
        "job_id": job_id,
        "case_id": case_id,
        "progress_endpoint": f"/api/cases/{case_id}/jobs/{job_id}/progress",
    }


@api_router.get(
    "/cases/{case_id}/jobs/{job_id}/progress",
    tags=["Investigation Workspace"],
    summary="Poll Active Investigation Job Progress",
)
def get_job_progress(case_id: str, job_id: str):
    """Returns dynamic progress percentage, active stage message, and final result if completed."""
    job = pipeline_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' for case '{case_id}' was not found.")

    res = None
    if job.status == "COMPLETED":
        res_model = pipeline_service.get_job_result(job_id)
        if res_model:
            res = res_model.model_dump(mode="json")

    return {
        **job.model_dump(),
        "result": res,
    }


@api_router.get(
    "/cases/{case_id}/runs",
    tags=["Investigation Workspace"],
    summary="List All Persisted Historical Runs for a Case",
)
def list_investigation_runs(case_id: str):
    """Returns the immutable version history of all execution runs for this case."""
    runs = persistence_service.list_case_runs(case_id)
    return {
        "case_id": case_id,
        "total_runs": len(runs),
        "runs": runs,
    }


@api_router.get(
    "/cases/{case_id}/runs/{run_id}",
    tags=["Investigation Workspace"],
    summary="Load a Specific Historical Investigation Run",
)
def get_investigation_run(case_id: str, run_id: str):
    """Retrieves full snapshot and parameters of a specific numbered run."""
    run_data = persistence_service.load_case_run(case_id, run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found for case '{case_id}'.")
    return run_data


@api_router.get(
    "/cases/{case_id}/runs-compare",
    tags=["Investigation Workspace"],
    summary="Compare Two Historical Runs Side by Side",
)
def compare_investigation_runs(case_id: str, run_a: str, run_b: str):
    """Computes parameter deltas, top candidate shifts, and score differences between two runs."""
    try:
        comparison = persistence_service.compare_case_runs(case_id, run_a, run_b)
        return comparison
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@api_router.delete(
    "/cases/{case_id}",
    tags=["Investigation Workspace"],
    summary="Delete an Investigation and Its Data from Disk",
)
def delete_investigation_case(case_id: str):
    """Safely removes an investigation directory and all its runs."""
    # Delete from in-memory case service registry
    if case_id in case_service.cases:
        del case_service.cases[case_id]
    case_service.sar_scenes.pop(case_id, None)
    case_service.slicks.pop(case_id, None)
    case_service.drift_sims.pop(case_id, None)
    case_service.candidates.pop(case_id, None)
    case_service.attribution_scores.pop(case_id, None)
    case_service.investigation_results.pop(case_id, None)

    # Delete directory from disk
    deleted = persistence_service.delete_case(case_id)
    return {
        "status": "SUCCESS",
        "case_id": case_id,
        "deleted_from_disk": deleted,
    }


# ---------------------------------------------------------------------------
# Vessel Intelligence & Live-Investigation Integration Endpoints
# ---------------------------------------------------------------------------

class InvestigationFromVesselRequest(BaseModel):
    mmsi: str = Field(..., pattern=r"^\d{9}$", description="9-digit Maritime Mobile Service Identity")
    title: Optional[str] = Field(None, description="Custom investigation title")
    description: Optional[str] = Field(None, description="Investigation synopsis")
    buffer_degrees: float = Field(0.8, ge=0.1, le=5.0, description="Spatial AOI radius buffer in degrees")


@api_router.get(
    "/vessels/{mmsi}/intelligence",
    tags=["Vessel Intelligence"],
    summary="Get Unified Vessel Intelligence Profile",
)
def get_vessel_intelligence(
    mmsi: str = Path(..., pattern=r"^\d{9}$", description="9-digit Maritime Mobile Service Identity")
):
    """Aggregates verified identity registry, real-time live kinematics, investigation relationships, and forensic evidence."""
    profile = vessel_intelligence_service.get_unified_vessel_profile(mmsi)
    return profile


@api_router.post(
    "/investigations/from-vessel",
    tags=["Investigation Workspace"],
    summary="Create Investigation Around Vessel Location and Mark as Subject",
)
def create_investigation_from_vessel(payload: InvestigationFromVesselRequest):
    """Creates a new historical investigation centered on a vessel's coordinates and establishes subject relationship."""
    profile = vessel_intelligence_service.get_unified_vessel_profile(payload.mmsi)
    telemetry = profile.get("telemetry", {})
    identity = profile.get("identity", {})

    lat = telemetry.get("latitude")
    lon = telemetry.get("longitude")

    buf = payload.buffer_degrees
    if lat is not None and lon is not None:
        min_lon = max(-180.0, float(lon) - buf)
        min_lat = max(-90.0, float(lat) - buf)
        max_lon = min(180.0, float(lon) + buf)
        max_lat = min(90.0, float(lat) + buf)
        incident_ts = telemetry.get("last_update_utc") or datetime.now(timezone.utc).isoformat()
    else:
        # Default maritime regional corridor
        min_lon, min_lat, max_lon, max_lat = 80.0, 5.0, 85.0, 10.0
        incident_ts = datetime.now(timezone.utc).isoformat()

    vessel_name = identity.get("vessel_name") or f"Vessel MMSI {payload.mmsi}"
    case_title = payload.title or f"Forensic Inquiry: {vessel_name} ({payload.mmsi})"
    case_desc = payload.description or f"Investigation initiated around vessel {vessel_name} (MMSI: {payload.mmsi}, Type: {identity.get('vessel_type')})."

    try:
        case = case_creation_service.create_investigation(
            title=case_title,
            description=case_desc,
            incident_timestamp_str=incident_ts,
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
        )

        # Mark vessel as subject in case metadata
        case.metadata["investigation_subject_mmsi"] = payload.mmsi
        case.metadata["vessel_name"] = vessel_name
        case.metadata["vessel_type"] = identity.get("vessel_type")
        case.metadata["created_from_vessel_profile"] = True

        # Save metadata update to disk
        case_dir = case_creation_service.base_cases_dir / case.id
        if case_dir.exists():
            case_file = case_dir / "case.json"
            with open(case_file, "w", encoding="utf-8") as f:
                f.write(case.model_dump_json(indent=2))

        return {
            "status": "SUCCESS",
            "case": case,
            "subject_vessel": {
                "mmsi": payload.mmsi,
                "name": vessel_name,
                "type": identity.get("vessel_type"),
            },
            "initial_bbox": [min_lon, min_lat, max_lon, max_lat],
        }
    except Exception as e:
        logger.error(f"Failed to create investigation from vessel: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize investigation for vessel {payload.mmsi}: {str(e)}"
        )


# ===========================================================================
# Automated Satellite Surveillance Endpoints
# ===========================================================================

@api_router.get("/surveillance/status", tags=["Satellite Surveillance"])
def get_surveillance_status():
    """Retrieve operational status, monitored sectors, and stats for the automated satellite surveillance worker."""
    from backend.app.services.satellite_watcher_service import satellite_watcher_service
    return satellite_watcher_service.get_status()


@api_router.get("/surveillance/alerts", tags=["Satellite Surveillance"])
def get_surveillance_alerts(limit: int = Query(50, ge=1, le=200)):
    """Retrieve historical automated detection alerts and their associated forensic case links."""
    from backend.app.services.satellite_watcher_service import satellite_watcher_service
    return satellite_watcher_service.get_alerts(limit=limit)


class ScanSectorRequest(BaseModel):
    sector_id: Optional[str] = Field(None, description="Specific sector ID to scan (or null to sweep all active sectors)")


@api_router.post("/surveillance/scan-now", tags=["Satellite Surveillance"])
def trigger_surveillance_sweep(request: Optional[ScanSectorRequest] = None):
    """Trigger an on-demand satellite surveillance pass across monitored sectors.
    
    Checks SAR satellite observation footprints, applies CFAR slick detection, runs lookalike
    rejection against ECMWF wind patterns, and auto-spawns cases with full backward drift
    attribution when confident slicks are detected.
    """
    from backend.app.services.satellite_watcher_service import satellite_watcher_service
    sector_id = request.sector_id if request else None
    result = satellite_watcher_service.run_scan_cycle(sector_id=sector_id)
    return result
