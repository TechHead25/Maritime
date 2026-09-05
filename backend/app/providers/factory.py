"""Provider Factory and Registry for Multi-Source Ingestion.

Allows dynamic selection between synthetic local test providers and real external data source adapters.
"""

from enum import Enum
import logging
from typing import Optional

from backend.app.providers.base import (
    AISDataProvider,
    OceanCurrentProvider,
    SARDataProvider,
    WindDataProvider,
)
from backend.app.providers.synthetic import (
    SyntheticAISProvider,
    SyntheticOceanCurrentProvider,
    SyntheticSARProvider,
    SyntheticWindProvider,
)
from backend.app.providers.ais_adapter import HistoricalAISCSVAdapter
from backend.app.providers.ocean_adapter import HistoricalOceanCurrentAdapter
from backend.app.providers.wind_adapter import HistoricalWindAdapter

logger = logging.getLogger("maritime-oil-attribution.providers.factory")


class ProviderMode(str, Enum):
    """Execution mode for data ingestion providers."""
    SYNTHETIC = "SYNTHETIC"
    EXTERNAL_HISTORICAL = "EXTERNAL_HISTORICAL"


class ProviderRegistry:
    """Registry managing active provider instances for each scientific modality."""

    def __init__(self, mode: ProviderMode = ProviderMode.SYNTHETIC):
        self.mode = mode
        self._sar_provider: Optional[SARDataProvider] = None
        self._ais_provider: Optional[AISDataProvider] = None
        self._ocean_provider: Optional[OceanCurrentProvider] = None
        self._wind_provider: Optional[WindDataProvider] = None

    def get_sar_provider(self) -> SARDataProvider:
        if self._sar_provider is None:
            if self.mode == ProviderMode.SYNTHETIC:
                self._sar_provider = SyntheticSARProvider()
            else:
                logger.info("Using SyntheticSARProvider as base SAR provider.")
                self._sar_provider = SyntheticSARProvider()
        return self._sar_provider

    def get_ais_provider(self) -> AISDataProvider:
        if self._ais_provider is None:
            if self.mode == ProviderMode.SYNTHETIC:
                self._ais_provider = SyntheticAISProvider()
            else:
                logger.info("Instantiating HistoricalAISCSVAdapter for external historical AIS ingestion.")
                self._ais_provider = HistoricalAISCSVAdapter()
        return self._ais_provider

    def get_ocean_provider(self) -> OceanCurrentProvider:
        if self._ocean_provider is None:
            if self.mode == ProviderMode.SYNTHETIC:
                self._ocean_provider = SyntheticOceanCurrentProvider()
            else:
                logger.info("Instantiating HistoricalOceanCurrentAdapter for CMEMS current ingestion.")
                self._ocean_provider = HistoricalOceanCurrentAdapter()
        return self._ocean_provider

    def get_wind_provider(self) -> WindDataProvider:
        if self._wind_provider is None:
            if self.mode == ProviderMode.SYNTHETIC:
                self._wind_provider = SyntheticWindProvider()
            else:
                logger.info("Instantiating HistoricalWindAdapter for ERA5 surface wind ingestion.")
                self._wind_provider = HistoricalWindAdapter()
        return self._wind_provider

    def set_providers(
        self,
        sar: Optional[SARDataProvider] = None,
        ais: Optional[AISDataProvider] = None,
        ocean: Optional[OceanCurrentProvider] = None,
        wind: Optional[WindDataProvider] = None,
    ):
        """Custom injection for testing or specific external connector instances."""
        if sar:
            self._sar_provider = sar
        if ais:
            self._ais_provider = ais
        if ocean:
            self._ocean_provider = ocean
        if wind:
            self._wind_provider = wind


# Global registry instance
default_provider_registry = ProviderRegistry(mode=ProviderMode.SYNTHETIC)
