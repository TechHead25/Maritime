"""Abstract Data Provider Interfaces for Maritime Forensic Intelligence.

Compliant with PRD FR1-FR5 and permanent engineering rules (GEMINI.md).
Decouples the core scientific calculation engine from external telemetry data APIs
(e.g., Copernicus CDSE, Spire/AISStream, CMEMS, ECMWF ERA5, Open-Meteo).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.schemas import (
    GeoPoint,
    SARScene,
    SlickPolygon,
    VesselTrack,
    ensure_utc,
)
from backend.app.services.sar_detector import SARRaster


# ---------------------------------------------------------------------------
# Custom Provider Exceptions
# ---------------------------------------------------------------------------

class ProviderError(Exception):
    """Base exception for all external data provider operations."""
    pass


class ProviderUnavailableError(ProviderError):
    """Raised when a requested external data provider is unavailable or unconfigured."""
    pass


class ProviderAuthenticationError(ProviderError):
    """Raised when credentials for an external provider are invalid or expired."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised when an external data provider rate limit has been exceeded."""
    pass


class ProviderTimeoutError(ProviderError):
    """Raised when an external data provider fails to respond within the allowed timeout."""
    pass


class ProviderCoverageError(ProviderError):
    """Raised when a spatial or temporal query falls outside the provider's valid coverage envelope."""
    pass


class NoSARObservationError(ProviderError):
    """Raised when no satellite SAR observation intersects the requested area and time window."""
    pass


# ---------------------------------------------------------------------------
# Provenance & Data Models
# ---------------------------------------------------------------------------

class ProviderProvenance(BaseModel):
    """Immutable provenance record attached to external observations."""
    model_config = ConfigDict(extra="allow")

    provider: str = Field(..., description="Canonical provider name")
    dataset: str = Field(..., description="Dataset or collection identifier")
    request_time_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    observation_time_utc: Optional[datetime] = Field(default=None)
    geographic_extent: Optional[Tuple[float, float, float, float]] = Field(default=None, description="[min_lon, min_lat, max_lon, max_lat]")
    resolution: Optional[str] = Field(default=None, description="Spatial resolution (e.g. 10m, 0.083 deg)")
    version: Optional[str] = Field(default=None, description="Dataset/model release version")
    source_identifier: str = Field(..., description="Original product or track UUID/granule ID")
    checksum_sha256: Optional[str] = Field(default=None, description="SHA-256 integrity hash")


# ---------------------------------------------------------------------------
# Query Parameter Models
# ---------------------------------------------------------------------------

class BoundingBox(BaseModel):
    """Geographic bounding box [min_lon, min_lat, max_lon, max_lat] in decimal degrees."""
    min_lon: float = Field(..., ge=-180.0, le=180.0)
    min_lat: float = Field(..., ge=-90.0, le=90.0)
    max_lon: float = Field(..., ge=-180.0, le=180.0)
    max_lat: float = Field(..., ge=-90.0, le=90.0)

    @property
    def as_tuple(self) -> Tuple[float, float, float, float]:
        return (self.min_lon, self.min_lat, self.max_lon, self.max_lat)


class SARQuery(BaseModel):
    """Query parameters for searching and acquiring SAR satellite scenes."""
    model_config = ConfigDict(extra="forbid")

    bbox: BoundingBox
    start_time: datetime
    end_time: datetime
    satellite_platform: Optional[str] = "Sentinel-1A"
    sensor_mode: Optional[str] = "IW"
    polarization: Optional[str] = "VV"


class AISQuery(BaseModel):
    """Query parameters for searching historical AIS vessel positions and tracks."""
    model_config = ConfigDict(extra="forbid")

    bbox: BoundingBox
    start_time: datetime
    end_time: datetime
    mmsi_filter: Optional[List[str]] = None
    vessel_types: Optional[List[str]] = None


class EnvironmentalQuery(BaseModel):
    """Query parameters for oceanographic hydrodynamic and atmospheric reanalysis models."""
    model_config = ConfigDict(extra="forbid")

    bbox: BoundingBox
    start_time: datetime
    end_time: datetime
    depth_meters: float = Field(default=0.0, ge=0.0, description="Ocean depth level (0.0 = surface current)")
    temporal_step_hours: float = Field(default=1.0, gt=0.0)


# ---------------------------------------------------------------------------
# Base Provider Interface
# ---------------------------------------------------------------------------

class BaseDataProvider(ABC):
    """Base interface for all data providers in the enterprise pipeline."""

    @property
    def name(self) -> str:
        """Human-readable provider identifier."""
        return self.__class__.__name__

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Category: SAR, AIS, OCEAN_CURRENT, WIND, VESSEL_IDENTITY."""
        pass

    def is_available(self) -> bool:
        """Verifies if the provider service or data source is accessible."""
        return True

    def get_auth_status(self) -> Dict[str, Any]:
        """Returns authentication and credential readiness details."""
        return {"authenticated": True, "status": "OPEN_DATA", "detail": "No authentication required"}

    def get_metadata(self) -> Dict[str, Any]:
        """Returns provider specifications, documentation, and rate limits."""
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "status": "ONLINE" if self.is_available() else "UNAVAILABLE",
        }

    def check_coverage(self, bbox: BoundingBox, time_window: Tuple[datetime, datetime]) -> bool:
        """Validates that a bounding box and time window fall within provider coverage."""
        return True

    def get_freshness(self) -> Dict[str, Any]:
        """Returns timestamp metrics regarding provider observation latency."""
        return {
            "provider": self.name,
            "latency_seconds": 0.0,
            "last_check_utc": datetime.now(timezone.utc).isoformat(),
        }

    def get_provenance(self, item_id: str, **kwargs) -> ProviderProvenance:
        """Generates an immutable provenance record for a fetched item."""
        return ProviderProvenance(
            provider=self.name,
            dataset=kwargs.get("dataset", self.name),
            source_identifier=item_id,
            request_time_utc=datetime.now(timezone.utc),
            observation_time_utc=kwargs.get("observation_time_utc"),
            geographic_extent=kwargs.get("geographic_extent"),
            resolution=kwargs.get("resolution"),
            version=kwargs.get("version"),
            checksum_sha256=kwargs.get("checksum_sha256"),
        )


# ---------------------------------------------------------------------------
# Specific Modality Interfaces
# ---------------------------------------------------------------------------

class SARDataProvider(BaseDataProvider):
    """Interface for SAR satellite scene search and raster ingestion."""

    @property
    def provider_type(self) -> str:
        return "SAR"

    @abstractmethod
    def search_scenes(self, query: SARQuery) -> List[SARScene]:
        """Queries SAR metadata catalogue matching spatial and temporal constraints."""
        pass

    @abstractmethod
    def fetch_raster(self, scene: SARScene) -> SARRaster:
        """Retrieves and calibrates the 2D georeferenced radar backscatter array in dB."""
        pass


class AISDataProvider(BaseDataProvider):
    """Interface for historical and streaming AIS vessel trajectory ingestion."""

    @property
    def provider_type(self) -> str:
        return "AIS"

    @abstractmethod
    def fetch_vessel_tracks(self, query: AISQuery) -> List[VesselTrack]:
        """Retrieves time-sequenced vessel waypoints intersecting the query spatiotemporal envelope."""
        pass

    def subscribe_live(self, bbox: BoundingBox):
        """Optional subscription for streaming real-time AIS feeds."""
        pass

    def get_live_vessels(self, bbox: Optional[BoundingBox] = None) -> List[VesselTrack]:
        """Retrieves currently buffered live vessel tracks."""
        return []


class OceanCurrentProvider(BaseDataProvider):
    """Interface for ocean hydrodynamic surface current data."""

    @property
    def provider_type(self) -> str:
        return "OCEAN_CURRENT"

    @abstractmethod
    def fetch_currents(self, query: EnvironmentalQuery) -> Dict[str, Any]:
        """Retrieves canonical ocean current vector grids (u, v in m/s) with source metadata."""
        pass


class WindDataProvider(BaseDataProvider):
    """Interface for atmospheric surface wind reanalysis data."""

    @property
    def provider_type(self) -> str:
        return "WIND"

    @abstractmethod
    def fetch_winds(self, query: EnvironmentalQuery) -> Dict[str, Any]:
        """Retrieves canonical surface wind vector grids (u, v in m/s) with source metadata."""
        pass


class VesselIdentityProvider(BaseDataProvider):
    """Interface for maritime vessel identity enrichment (IMO, MMSI, ownership)."""

    @property
    def provider_type(self) -> str:
        return "VESSEL_IDENTITY"

    @abstractmethod
    def lookup_by_mmsi(self, mmsi: str) -> Optional[Dict[str, Any]]:
        """Enriches vessel particulars using official maritime MMSI registry."""
        pass

    @abstractmethod
    def lookup_by_imo(self, imo: str) -> Optional[Dict[str, Any]]:
        """Enriches vessel particulars using official IMO registry."""
        pass

    @abstractmethod
    def lookup_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Enriches vessel particulars matching vessel name substring."""
        pass
