"""Enterprise Data Provider Registry for Multi-Modal Ingestion.

Dynamically inspects and orchestrates real external telemetry and model data providers.
Enforces permanent engineering rules (GEMINI.md):
- NEVER silently falls back to synthetic data in production.
- Synthetic providers are strictly gated behind ALLOW_SYNTHETIC_PROVIDERS=true (test-only).
- Fails clearly with ProviderUnavailableError if a required provider is unconfigured.
"""

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, List, Optional

from backend.app.providers.base import (
    AISDataProvider,
    BaseDataProvider,
    OceanCurrentProvider,
    ProviderUnavailableError,
    SARDataProvider,
    VesselIdentityProvider,
    WindDataProvider,
)
from backend.app.providers.copernicus_sar import CopernicusSARProvider
from backend.app.providers.sar_adapter import HistoricalSARAdapter
from backend.app.providers.live_ais import LiveAISWebSocketProvider
from backend.app.providers.ais_adapter import HistoricalAISCSVAdapter
from backend.app.providers.copernicus_marine import CopernicusMarineCurrentProvider
from backend.app.providers.openmeteo_wind import OpenMeteoMarineWindProvider
from backend.app.providers.vessel_identity import MaritimeVesselIdentityAdapter
from backend.app.providers.synthetic import (
    SyntheticAISProvider,
    SyntheticOceanCurrentProvider,
    SyntheticSARProvider,
    SyntheticWindProvider,
)

logger = logging.getLogger("maritime-oil-attribution.providers.registry")


class ProviderRegistry:
    """Central registry dynamically resolving active providers with zero synthetic fallback in production."""

    def __init__(self):
        self.allow_synthetic = os.getenv("ALLOW_SYNTHETIC_PROVIDERS", "false").lower() in ("true", "1")

        # Instantiate production adapters
        self._copernicus_sar = CopernicusSARProvider()
        self._historical_sar = HistoricalSARAdapter()

        self._live_ais = LiveAISWebSocketProvider()
        self._historical_ais = HistoricalAISCSVAdapter()

        self._copernicus_marine = CopernicusMarineCurrentProvider()
        self._openmeteo_wind = OpenMeteoMarineWindProvider()
        self._vessel_identity = MaritimeVesselIdentityAdapter()

        # Synthetic providers strictly for test/ci
        self._synthetic_sar = SyntheticSARProvider()
        self._synthetic_ais = SyntheticAISProvider()
        self._synthetic_ocean = SyntheticOceanCurrentProvider()
        self._synthetic_wind = SyntheticWindProvider()

        # Injected overrides
        self._custom_sar: Optional[SARDataProvider] = None
        self._custom_ais: Optional[AISDataProvider] = None
        self._custom_ocean: Optional[OceanCurrentProvider] = None
        self._custom_wind: Optional[WindDataProvider] = None
        self._custom_vessel_id: Optional[VesselIdentityProvider] = None

    def get_sar_provider(self, prefer_historical: bool = True) -> SARDataProvider:
        """Resolves active SAR data provider."""
        if self._custom_sar:
            return self._custom_sar

        if prefer_historical and self._historical_sar.is_available():
            return self._historical_sar

        if self._copernicus_sar.is_available():
            return self._copernicus_sar

        if self.allow_synthetic:
            logger.info("TEST MODE: Using SyntheticSARProvider because ALLOW_SYNTHETIC_PROVIDERS=true.")
            return self._synthetic_sar

        raise ProviderUnavailableError(
            "Data source unavailable: No active SAR provider available. Copernicus CDSE is unreachable and no valid historical SAR raster was found."
        )

    def get_ais_provider(self, prefer_live: bool = False) -> AISDataProvider:
        """Resolves active AIS provider."""
        if self._custom_ais:
            return self._custom_ais

        if prefer_live and self._live_ais.is_available():
            return self._live_ais

        if self._historical_ais.is_available():
            return self._historical_ais

        if self._live_ais.is_available():
            return self._live_ais

        if self.allow_synthetic:
            logger.info("TEST MODE: Using SyntheticAISProvider because ALLOW_SYNTHETIC_PROVIDERS=true.")
            return self._synthetic_ais

        raise ProviderUnavailableError(
            "Data source unavailable: No active AIS provider available. Live AIS WebSocket credentials (AISSTREAM_API_KEY) are unconfigured and no local AIS archive is present."
        )

    def get_ocean_provider(self) -> OceanCurrentProvider:
        """Resolves active ocean hydrodynamic current provider."""
        if self._custom_ocean:
            return self._custom_ocean

        if self._copernicus_marine.is_available():
            return self._copernicus_marine

        if self.allow_synthetic:
            logger.info("TEST MODE: Using SyntheticOceanCurrentProvider because ALLOW_SYNTHETIC_PROVIDERS=true.")
            return self._synthetic_ocean

        raise ProviderUnavailableError(
            "Data source unavailable: Copernicus Marine current service is unavailable and no local hydrodynamic grids exist."
        )

    def get_wind_provider(self) -> WindDataProvider:
        """Resolves active atmospheric wind provider."""
        if self._custom_wind:
            return self._custom_wind

        if self._openmeteo_wind.is_available():
            return self._openmeteo_wind

        if self.allow_synthetic:
            logger.info("TEST MODE: Using SyntheticWindProvider because ALLOW_SYNTHETIC_PROVIDERS=true.")
            return self._synthetic_wind

        raise ProviderUnavailableError(
            "Data source unavailable: Marine atmospheric wind service is unavailable and no local reanalysis grids exist."
        )

    def get_vessel_identity_provider(self) -> VesselIdentityProvider:
        """Resolves vessel identity enrichment provider."""
        if self._custom_vessel_id:
            return self._custom_vessel_id
        return self._vessel_identity

    def get_all_providers(self) -> List[BaseDataProvider]:
        """Returns all registered production data providers."""
        return [
            self._copernicus_sar,
            self._live_ais,
            self._copernicus_marine,
            self._openmeteo_wind,
            self._vessel_identity,
        ]

    def get_health_summary(self) -> Dict[str, Any]:
        """Exposes health, availability, latency, and credential readiness across all providers."""
        providers = self.get_all_providers()
        summary = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "synthetic_mode_allowed": self.allow_synthetic,
            "overall_status": "OPERATIONAL" if any(p.is_available() for p in providers) else "DEGRADED",
            "providers": {},
        }

        for p in providers:
            p_key = p.provider_type.lower()
            try:
                available = p.is_available()
                auth = p.get_auth_status()
                meta = p.get_metadata()
                freshness = p.get_freshness()

                summary["providers"][p_key] = {
                    "name": p.name,
                    "provider_type": p.provider_type,
                    "available": available,
                    "status": "ONLINE" if available else "UNAVAILABLE",
                    "auth": auth,
                    "metadata": meta,
                    "freshness": freshness,
                }
            except Exception as e:
                summary["providers"][p_key] = {
                    "name": p.name,
                    "provider_type": p.provider_type,
                    "available": False,
                    "status": "ERROR",
                    "error": str(e),
                }

        return summary

    def set_custom_providers(
        self,
        sar: Optional[SARDataProvider] = None,
        ais: Optional[AISDataProvider] = None,
        ocean: Optional[OceanCurrentProvider] = None,
        wind: Optional[WindDataProvider] = None,
        vessel_id: Optional[VesselIdentityProvider] = None,
    ):
        """Allows test fixtures to inject custom or mock providers."""
        if sar is not None:
            self._custom_sar = sar
        if ais is not None:
            self._custom_ais = ais
        if ocean is not None:
            self._custom_ocean = ocean
        if wind is not None:
            self._custom_wind = wind
        if vessel_id is not None:
            self._custom_vessel_id = vessel_id


# Global production registry instance
provider_registry = ProviderRegistry()
