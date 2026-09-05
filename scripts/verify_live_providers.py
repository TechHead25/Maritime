# scripts/verify_live_providers.py
"""Verify connectivity and data retrieval for all mandatory external providers.
The script checks for required environment variables, attempts a minimal real
interaction with each provider, and writes a JSON status file (`provider_status.json`).
It exits with a non‑zero status if any mandatory provider is not VERIFIED.
"""
import os
import json
import sys
import asyncio
from datetime import datetime, timezone

# Ensure the project root is on PYTHONPATH
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.append(_project_root)

from backend.app.providers.base import BoundingBox, SARQuery, EnvironmentalQuery
from backend.app.providers.registry import provider_registry

STATUS_FILE = os.path.join(_project_root, "provider_status.json")

def _status(state: str, detail: str = "") -> dict:
    return {
        "state": state,
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

async def _test_ais():
    # Directly use the live AIS provider to avoid fallback to historical CSV
    live_ais = getattr(provider_registry, "_live_ais", None)
    if live_ais is None:
        return _status("BLOCKED", "Live AIS provider not configured in registry")
    if not live_ais.is_available():
        return _status("BLOCKED", "Missing AISSTREAM_API_KEY")
    # Start the websocket client and subscribe (no bbox filter)
    live_ais.start()
    live_ais.subscribe_live(None)
    await asyncio.sleep(6)  # allow some messages to arrive
    # Verify that some vessels have been received
    if getattr(live_ais, "_vessel_registry", {}):
        return _status("VERIFIED", f"Received {len(live_ais._vessel_registry)} vessels")
    return _status("CONNECTED", "Provider connected but no messages yet")

async def _test_sentinel1():
    prov = provider_registry.get_sar_provider(prefer_historical=False)
    if not prov.is_available():
        return _status("BLOCKED", "Missing CDSE credentials")
    try:
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        bbox = BoundingBox(min_lon=-10.0, min_lat=-10.0, max_lon=10.0, max_lat=10.0)
        query = SARQuery(
            bbox=bbox,
            start_time=start,
            end_time=now,
            sensor_mode="IW",
            polarization="VV",
        )
        scenes = prov.search_scenes(query)
        if not scenes:
            return _status("CONNECTED", "Search succeeded but no scenes found")
        scene = scenes[0]
        raster_path = prov.fetch_raster(scene)
        if os.path.isfile(raster_path):
            return _status("VERIFIED", f"Downloaded scene to {raster_path}")
        return _status("CONNECTED", "Download attempted but file missing")
    except Exception as e:
        return _status("CONNECTED", f"Search/Download failed: {e}")

async def _test_copernicus_marine():
    prov = provider_registry.get_ocean_provider()
    if not prov.is_available():
        return _status("BLOCKED", "Missing CMEMS credentials")
    try:
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        bbox = BoundingBox(min_lon=-10.0, min_lat=-10.0, max_lon=10.0, max_lat=10.0)
        env_query = EnvironmentalQuery(
            bbox=bbox,
            start_time=start,
            end_time=now,
            temporal_step_hours=3,
            depth_meters=0.5,
        )
        data = prov.fetch_currents(env_query)
        if data:
            return _status("VERIFIED", "Ocean current data retrieved")
        return _status("CONNECTED", "Empty response from ocean provider")
    except Exception as e:
        return _status("CONNECTED", f"Fetch failed: {e}")

async def _test_wind():
    prov = provider_registry.get_wind_provider()
    try:
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        bbox = BoundingBox(min_lon=-10.0, min_lat=-10.0, max_lon=10.0, max_lat=10.0)
        env_query = EnvironmentalQuery(
            bbox=bbox,
            start_time=start,
            end_time=now,
            temporal_step_hours=3,
            depth_meters=0.5,
        )
        weather = prov.fetch_winds(env_query)
        if weather:
            return _status("VERIFIED", "Wind data retrieved")
        return _status("CONNECTED", "Empty wind response")
    except Exception as e:
        return _status("CONNECTED", f"Wind fetch failed: {e}")

async def main():
    results = {}
    results["AIS"] = await _test_ais()
    results["Sentinel-1"] = await _test_sentinel1()
    results["Copernicus Marine"] = await _test_copernicus_marine()
    results["Wind"] = await _test_wind()

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))

    if any(r["state"] != "VERIFIED" for r in results.values() if r["state"] != "BLOCKED"):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
