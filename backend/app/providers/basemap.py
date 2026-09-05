"""Basemap and Nautical Chart Tile Provider.

Exposes CartoDB Dark Matter nautical basemap tiles and OpenStreetMap spatial boundaries.
Compliant with GEMINI.md: strictly open data, unmetered CDN with real health inspection.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional, Tuple
import requests

from backend.app.providers.base import (
    BaseDataProvider,
    BoundingBox,
    ProviderProvenance,
)


class BasemapTileProvider(BaseDataProvider):
    """Provides high-contrast nautical dark basemap vector/raster tiles for map visualization."""

    def __init__(self):
        self._tile_template = "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
        self._sample_tile_url = "https://a.basemaps.cartocdn.com/dark_all/5/23/15.png"
        self._last_success_utc: Optional[str] = None
        self._last_latency_ms: float = 42.0

    @property
    def name(self) -> str:
        return "CartoDB Dark Matter Nautical Basemap (CARTO / OpenStreetMap)"

    @property
    def provider_type(self) -> str:
        return "BASEMAP"

    def is_available(self) -> bool:
        return True

    def get_auth_status(self) -> Dict[str, Any]:
        return {
            "authenticated": True,
            "status": "PUBLIC_OPEN_ACCESS",
            "auth_type": "None (Public CDN)",
            "masked_credential": "Open Access (No Secret Required)",
            "detail": "OpenStreetMap & CARTO public vector tile layer active.",
        }

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "service_name": "CARTO Dark Matter XYZ Tile Layer",
            "endpoint": "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            "tile_format": "PNG / WebP (256x256)",
            "max_zoom": 19,
            "coverage": "Global (-180° to 180°, -85° to 85° WGS84)",
            "rate_limit": "Nominal (Unmetered CDN Cached)",
            "rate_limit_active": False,
        }

    def check_coverage(self, bbox: BoundingBox, time_window: Tuple[datetime, datetime]) -> bool:
        return True

    def get_freshness(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "latency_seconds": 0.0,
            "last_check_utc": datetime.now(timezone.utc).isoformat(),
        }

    def ping(self) -> Dict[str, Any]:
        """Performs a live HEAD request against the tile CDN to calculate round-trip latency."""
        t0 = time.time()
        try:
            resp = requests.head(self._sample_tile_url, timeout=4.0)
            latency_ms = round((time.time() - t0) * 1000.0, 1)
            self._last_latency_ms = latency_ms
            if resp.status_code < 400:
                self._last_success_utc = datetime.now(timezone.utc).isoformat()
                return {"status": "ONLINE", "latency_ms": latency_ms, "http_status": resp.status_code, "error": None}
            return {"status": "DEGRADED", "latency_ms": latency_ms, "http_status": resp.status_code, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"status": "UNAVAILABLE", "latency_ms": 0.0, "error": str(e)}


basemap_tile_provider = BasemapTileProvider()
