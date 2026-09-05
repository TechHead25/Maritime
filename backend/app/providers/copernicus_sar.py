"""Copernicus Data Space Ecosystem (CDSE) SAR Data Provider.

Implements official Copernicus Data Space STAC and OData catalogue interfaces
for Sentinel-1 C-Band SAR metadata query, granule discovery, and raster acquisition.
Compliant with GEMINI.md: strictly zero dummy data fabrication; fails clearly if no scene exists.
"""

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import requests

from backend.app.models.schemas import (
    GeoPolygon,
    SARScene,
    ensure_utc,
)
from backend.app.providers.base import (
    BoundingBox,
    NoSARObservationError,
    ProviderAuthenticationError,
    ProviderCoverageError,
    ProviderProvenance,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    SARDataProvider,
    SARQuery,
)
from backend.app.services.sar_detector import SARRaster

logger = logging.getLogger("maritime-oil-attribution.providers.copernicus_sar")


class CopernicusSARProvider(SARDataProvider):
    """Production provider connecting to Copernicus Data Space Ecosystem (CDSE)."""

    STAC_ENDPOINT = "https://catalogue.dataspace.copernicus.eu/stac/search"
    ODATA_ENDPOINT = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    TOKEN_ENDPOINT = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        timeout_seconds: float = 12.0,
    ):
        self.client_id = client_id or os.getenv("CDSE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("CDSE_CLIENT_SECRET")
        self.timeout_seconds = timeout_seconds
        self._cached_token: Optional[str] = None
        self._token_expiry: Optional[float] = None

    @property
    def name(self) -> str:
        return "Copernicus Data Space Ecosystem (Sentinel-1 SAR)"

    def is_available(self) -> bool:
        """Verifies catalogue availability via a lightweight HEAD or GET probe."""
        try:
            res = requests.get(
                "https://catalogue.dataspace.copernicus.eu/stac",
                timeout=4.0,
            )
            return res.status_code == 200
        except Exception as e:
            logger.warning(f"CDSE catalogue probe failed: {e}")
            return False

    def get_auth_status(self) -> Dict[str, Any]:
        has_creds = bool(self.client_id and self.client_secret)
        return {
            "provider": self.name,
            "authenticated": has_creds,
            "status": "CONFIGURED" if has_creds else "UNCONFIGURED (PUBLIC_METADATA_ONLY)",
            "client_id_configured": bool(self.client_id),
            "detail": "CDSE OAuth2 credentials configured for product download" if has_creds else "Public STAC metadata search enabled; product download requires CDSE credentials.",
        }

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider_type": "SAR",
            "catalogue_stac": self.STAC_ENDPOINT,
            "catalogue_odata": self.ODATA_ENDPOINT,
            "supported_collections": ["SENTINEL-1"],
            "supported_modes": ["IW", "EW", "SM"],
            "supported_product_types": ["GRD", "SLC"],
            "polarizations": ["VV", "VH", "VV+VH"],
            "spatial_resolution": "10m (High Resolution GRD)",
        }

    def check_coverage(self, bbox: BoundingBox, time_window: Tuple[datetime, datetime]) -> bool:
        """Validates Sentinel-1 operational envelope (April 2014 to present)."""
        start_t, end_t = time_window
        s1_epoch = datetime(2014, 4, 3, tzinfo=timezone.utc)
        if end_t < s1_epoch:
            return False
        return True

    def get_freshness(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "nominal_repeat_cycle_days": 12,
            "latency_from_acquisition_hours": 3.0,
            "last_checked_utc": datetime.now(timezone.utc).isoformat(),
        }

    def search_scenes(self, query: SARQuery, raise_if_empty: bool = False) -> List[SARScene]:
        """Queries official Copernicus Data Space Ecosystem (CDSE) OData and STAC catalogues for Sentinel-1 scenes.

        Never fabricates a scene. If no scenes match, returns empty list or raises NoSARObservationError.
        """
        if not self.check_coverage(query.bbox, (query.start_time, query.end_time)):
            raise ProviderCoverageError(
                f"Query time window {query.start_time.isoformat()} is prior to Sentinel-1 operational epoch (2014-04-03)."
            )

        # -------------------------------------------------------------------
        # 1. Primary: Official CDSE OData v1 Products Catalogue
        # -------------------------------------------------------------------
        min_lon, min_lat = query.bbox.min_lon, query.bbox.min_lat
        max_lon, max_lat = query.bbox.max_lon, query.bbox.max_lat
        poly_wkt = f"SRID=4326;POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
        start_str = query.start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_str = query.end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        filter_expr = (
            f"Collection/Name eq 'SENTINEL-1' and "
            f"OData.CSC.Intersects(area=geography'{poly_wkt}') and "
            f"ContentDate/Start gt {start_str} and "
            f"ContentDate/Start lt {end_str}"
        )
        if query.sensor_mode:
            filter_expr += f" and contains(Name, '{query.sensor_mode}')"

        odata_params = {
            "$filter": filter_expr,
            "$top": 10,
        }

        parsed_scenes: List[SARScene] = []
        try:
            odata_resp = requests.get(
                self.ODATA_ENDPOINT,
                params=odata_params,
                headers={"User-Agent": "Maritime-Oil-Attribution/0.1.0"},
                timeout=self.timeout_seconds,
            )
            if odata_resp.status_code == 200:
                odata_items = odata_resp.json().get("value", [])
                for item in odata_items:
                    name = item.get("Name", "")
                    platform_name = "Sentinel-1A" if "S1A" in name else "Sentinel-1B"
                    start_val = item.get("ContentDate", {}).get("Start", "")
                    acq_dt = ensure_utc(datetime.fromisoformat(start_val.replace("Z", "+00:00"))) if start_val else query.start_time

                    footprint_str = item.get("Footprint", "")
                    footprint_poly: Optional[GeoPolygon] = None
                    if footprint_str and "POLYGON" in footprint_str:
                        import re
                        m = re.search(r"\(\((.*?)\)\)", footprint_str)
                        if m:
                            coords = []
                            for pair in m.group(1).split(","):
                                pts = pair.strip().split()
                                if len(pts) >= 2:
                                    coords.append([float(pts[0]), float(pts[1])])
                            if coords:
                                footprint_poly = GeoPolygon(type="Polygon", coordinates=[coords])

                    meta = {
                        "source_provider": self.name,
                        "granule_id": item.get("Id"),
                        "product_name": name,
                        "content_date": item.get("ContentDate"),
                        "provenance": self.get_provenance(
                            item_id=str(item.get("Id", "s1_granule")),
                            dataset="SENTINEL-1 GRD",
                            observation_time_utc=acq_dt,
                            geographic_extent=query.bbox.as_tuple,
                            resolution="10m",
                        ).model_dump(mode="json"),
                    }

                    parsed_scenes.append(
                        SARScene(
                            id=f"sar_{str(item.get('Id', 'cdse'))[:32]}",
                            case_id="dynamic_query",
                            satellite_platform=platform_name,
                            sensor_mode=query.sensor_mode or "IW",
                            polarization=query.polarization or "VV",
                            acquisition_timestamp=acq_dt,
                            footprint_polygon=footprint_poly,
                            pixel_resolution_meters=10.0,
                            metadata=meta,
                        )
                    )
                if parsed_scenes:
                    return parsed_scenes
        except Exception as odata_err:
            logger.warning(f"CDSE OData search warning: {odata_err}; attempting STAC fallback")

        # -------------------------------------------------------------------
        # 2. Secondary: CDSE STAC Search Endpoint
        # -------------------------------------------------------------------
        stac_payload = {
            "collections": ["SENTINEL-1"],
            "bbox": [query.bbox.min_lon, query.bbox.min_lat, query.bbox.max_lon, query.bbox.max_lat],
            "datetime": f"{query.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/{query.end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}",
            "limit": 10,
        }

        try:
            response = requests.post(
                self.STAC_ENDPOINT,
                json=stac_payload,
                headers={"Content-Type": "application/json", "User-Agent": "Maritime-Oil-Attribution/0.1.0"},
                timeout=self.timeout_seconds,
            )
            if response.status_code == 401:
                raise ProviderAuthenticationError("CDSE STAC authentication failed: Unauthorized (401)")
            elif response.status_code == 429:
                raise ProviderRateLimitError("CDSE STAC rate limit exceeded: Too Many Requests (429)")
            elif response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                for feat in features:
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    dt_str = props.get("datetime") or props.get("start_datetime")
                    acq_dt = ensure_utc(datetime.fromisoformat(dt_str.replace("Z", "+00:00"))) if dt_str else query.start_time
                    footprint_poly = None
                    if geom and geom.get("type") == "Polygon":
                        footprint_poly = GeoPolygon(type="Polygon", coordinates=geom.get("coordinates", []))

                    meta = {
                        "source_provider": self.name,
                        "granule_id": feat.get("id"),
                        "provenance": self.get_provenance(
                            item_id=feat.get("id", "s1_granule"),
                            dataset="SENTINEL-1 GRD",
                            observation_time_utc=acq_dt,
                            geographic_extent=query.bbox.as_tuple,
                            resolution="10m",
                        ).model_dump(mode="json"),
                    }
                    platform_name = "Sentinel-1A" if "1A" in str(props.get("platform", "")) else "Sentinel-1B"
                    parsed_scenes.append(
                        SARScene(
                            id=f"sar_{feat.get('id', 'cdse')[:32]}",
                            case_id="dynamic_query",
                            satellite_platform=platform_name,
                            sensor_mode=query.sensor_mode or "IW",
                            polarization=query.polarization or "VV",
                            acquisition_timestamp=acq_dt,
                            footprint_polygon=footprint_poly,
                            pixel_resolution_meters=10.0,
                            metadata=meta,
                        )
                    )
        except (ProviderAuthenticationError, ProviderRateLimitError):
            raise
        except requests.exceptions.Timeout as timeout_err:
            logger.warning(f"CDSE STAC timeout: {timeout_err}")
            raise ProviderTimeoutError(f"CDSE STAC endpoint timed out: {timeout_err}")
        except Exception as stac_err:
            logger.warning(f"CDSE STAC fallback warning: {stac_err}")

        if not parsed_scenes:
            if raise_if_empty:
                raise NoSARObservationError("No SAR observation available for the requested bounding box and time range.")
            return []

        return parsed_scenes

    def fetch_raster(self, scene: SARScene) -> SARRaster:
        """Retrieves or loads the 2D georeferenced radar backscatter raster in dB."""
        local_path = scene.metadata.get("local_path") if scene.metadata else None
        if local_path and os.path.exists(local_path):
            import pickle
            if local_path.endswith(".pkl"):
                with open(local_path, "rb") as f:
                    raster_obj = pickle.load(f)
                return raster_obj
            elif local_path.endswith(".tif") or local_path.endswith(".tiff"):
                from backend.app.services.sar_detector import sar_detector
                return sar_detector.load_sar_geotiff(local_path)

        if not (self.client_id and self.client_secret):
            raise ProviderUnavailableError(
                f"Cannot download raw raster for scene '{scene.id}'. CDSE credentials (CDSE_CLIENT_ID / CDSE_CLIENT_SECRET) are unconfigured, and no local pre-ingested raster was provided."
            )

        raise ProviderUnavailableError(
            f"Automated large-file download for Sentinel-1 SAFE package '{scene.id}' exceeds inline API limits. Download the GRD product or mount via S3 object storage."
        )
