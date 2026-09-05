"""Production Live AIS Ingestion & Real-Time Maritime Service.

Architectural Pipeline:
External AIS Provider (WSS) -> WebSocket Client -> Message Validator -> Normalizer
-> Event Stream -> Current Vessel State -> Historical Track Store -> WebSocket/SSE -> Frontend.

Compliant with GEMINI.md:
- Browser NEVER connects directly to external AIS stream; server mediates all connections.
- ZERO fake vessels: if disconnected or empty, reports DISCONNECTED / empty state honestly.
- Bounded in-memory rolling retention to prevent unbounded memory growth.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import math
import os
import re
import threading
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Tuple

from backend.app.models.schemas import (
    VesselPosition,
    VesselTrack,
    VesselType,
    ensure_utc,
    validate_latitude,
    validate_longitude,
)
from backend.app.providers.base import BoundingBox, ProviderProvenance
from backend.app.providers.vessel_identity import MaritimeVesselIdentityAdapter

logger = logging.getLogger("maritime-oil-attribution.services.live_ais")


# ---------------------------------------------------------------------------
# 1. Predefined Geographic Maritime Regions
# ---------------------------------------------------------------------------

PREDEFINED_REGIONS: Dict[str, BoundingBox] = {
    "SRI_LANKA_SOUTH": BoundingBox(min_lon=80.0, min_lat=5.0, max_lon=83.5, max_lat=9.0),
    "STRAIT_OF_MALACCA": BoundingBox(min_lon=99.0, min_lat=1.0, max_lon=104.5, max_lat=5.0),
    "BAY_OF_BENGAL": BoundingBox(min_lon=80.0, min_lat=10.0, max_lon=93.0, max_lat=21.0),
    "ARABIAN_SEA": BoundingBox(min_lon=68.0, min_lat=15.0, max_lon=75.0, max_lat=24.0),
    "GLOBAL": BoundingBox(min_lon=-180.0, min_lat=-90.0, max_lon=180.0, max_lat=90.0),
}


# ---------------------------------------------------------------------------
# 2. AIS Message Validator
# ---------------------------------------------------------------------------

class AISMessageValidator:
    """Validates raw incoming AIS frames against physical and maritime bounds."""

    @staticmethod
    def validate_mmsi(mmsi_val: Any) -> Tuple[bool, Optional[str]]:
        """Validates that MMSI is a valid 9-digit numerical identifier."""
        s = re.sub(r"[^\d]", "", str(mmsi_val))
        if len(s) != 9 or s.startswith("0") or s == "999999999" or s == "000000000":
            return False, None
        return True, s

    @staticmethod
    def validate_coordinates(lat: Any, lon: Any) -> bool:
        """Validates latitude and longitude within WGS84 bounds, rejecting standard 91/181 null sentinels."""
        try:
            f_lat = float(lat)
            f_lon = float(lon)
            if not (-90.0 <= f_lat <= 90.0) or not (-180.0 <= f_lon <= 180.0):
                return False
            # Standard NMEA null indicator (91.0 or 181.0)
            if abs(f_lat - 91.0) < 0.01 or abs(f_lon - 181.0) < 0.01:
                return False
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_kinematics(sog: Any, cog: Any) -> Tuple[float, float]:
        """Clamps and validates speed over ground (0 - 102.2 kn) and course over ground (0 - 360 deg)."""
        try:
            f_sog = float(sog) if sog is not None else 0.0
            f_sog = max(0.0, min(102.2, f_sog))
        except (ValueError, TypeError):
            f_sog = 0.0

        try:
            f_cog = float(cog) if cog is not None else 0.0
            f_cog = (f_cog % 360.0 + 360.0) % 360.0
        except (ValueError, TypeError):
            f_cog = 0.0

        return f_sog, f_cog


# ---------------------------------------------------------------------------
# 3. AIS Message Normalizer
# ---------------------------------------------------------------------------

class AISNormalizer:
    """Standardizes heterogeneous AIS frames into canonical typed structures."""

    @staticmethod
    def normalize_timestamp(raw_time: Any) -> datetime:
        """Parses UTC timestamp or defaults to current UTC time."""
        if not raw_time:
            return datetime.now(timezone.utc)
        if isinstance(raw_time, datetime):
            return ensure_utc(raw_time)
        try:
            s = str(raw_time).replace("Z", "+00:00")
            return ensure_utc(datetime.fromisoformat(s))
        except Exception:
            return datetime.now(timezone.utc)

    @staticmethod
    def map_vessel_type(type_code: Any, vessel_name: str = "") -> str:
        """Maps numeric AIS ShipType codes or naming cues to canonical categories."""
        v_name_upper = vessel_name.upper()
        if "TANKER" in v_name_upper or "OIL" in v_name_upper or "VLCC" in v_name_upper:
            return "TANKER"
        if "CARGO" in v_name_upper or "BULK" in v_name_upper or "CONTAINER" in v_name_upper:
            return "CARGO"
        if "TUG" in v_name_upper:
            return "TUG"
        if "PILOT" in v_name_upper or "PATROL" in v_name_upper:
            return "PILOT"

        try:
            code = int(type_code)
            if 80 <= code <= 89:
                return "TANKER"
            elif 70 <= code <= 79:
                return "CARGO"
            elif 52 == code or 31 <= code <= 32:
                return "TUG"
            elif 30 == code:
                return "FISHING"
            elif 60 <= code <= 69:
                return "PASSENGER"
        except (ValueError, TypeError):
            pass

        return "OTHER"


# ---------------------------------------------------------------------------
# 4. Current Vessel State & Historical Track Store
# ---------------------------------------------------------------------------

class CurrentVesselState:
    """Thread-safe snapshot cache of the latest position and telemetry for each active vessel."""

    def __init__(self):
        self._vessels: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def update(self, mmsi: str, telemetry: Dict[str, Any]):
        with self._lock:
            self._vessels[mmsi] = telemetry

    def get_all(
        self,
        bbox: Optional[BoundingBox] = None,
        vessel_type: Optional[str] = None,
        min_speed: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        results = []
        with self._lock:
            for mmsi, state in self._vessels.items():
                lat = state.get("latitude")
                lon = state.get("longitude")
                if lat is None or lon is None:
                    continue

                if bbox is not None:
                    if not (bbox.min_lon <= lon <= bbox.max_lon and bbox.min_lat <= lat <= bbox.max_lat):
                        continue

                if vessel_type and vessel_type != "ALL":
                    if state.get("vessel_type") != vessel_type:
                        continue

                speed = state.get("speed_over_ground_knots", 0.0)
                if min_speed is not None and speed < min_speed:
                    continue

                # Compute live data age in seconds
                last_ts = state.get("last_update_utc")
                if isinstance(last_ts, datetime):
                    age_seconds = max(0.0, (now - last_ts).total_seconds())
                else:
                    age_seconds = 0.0

                item = dict(state)
                item["data_age_seconds"] = round(age_seconds, 1)
                item["is_stale"] = age_seconds > 1800.0  # >30 mins without ping
                results.append(item)

        return results

    def get(self, mmsi: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            v = self._vessels.get(mmsi)
            if not v:
                return None
            item = dict(v)
            now = datetime.now(timezone.utc)
            last_ts = item.get("last_update_utc")
            if isinstance(last_ts, datetime):
                item["data_age_seconds"] = round(max(0.0, (now - last_ts).total_seconds()), 1)
            return item

    def count(self) -> int:
        with self._lock:
            return len(self._vessels)

    def clear(self):
        with self._lock:
            self._vessels.clear()


class HistoricalTrackStore:
    """Thread-safe rolling buffer of past waypoints per vessel with bounded memory retention."""

    def __init__(self, max_waypoints_per_vessel: int = 500, retention_hours: float = 12.0):
        self.max_waypoints = max_waypoints_per_vessel
        self.retention_hours = retention_hours
        self._tracks: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def clear(self):
        with self._lock:
            self._tracks.clear()

    def add_waypoint(self, mmsi: str, wp: Dict[str, Any]):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
        with self._lock:
            if mmsi not in self._tracks:
                self._tracks[mmsi] = []

            lst = self._tracks[mmsi]
            lst.append(wp)

            # Prune by age and count
            if len(lst) > self.max_waypoints or (len(lst) % 20 == 0):
                self._tracks[mmsi] = [
                    p for p in lst[-self.max_waypoints:]
                    if p.get("timestamp_utc", datetime.now(timezone.utc)) >= cutoff
                ]

    def get_track(self, mmsi: str) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._tracks.get(mmsi, []))

    def prune_all(self):
        """Global periodic maintenance removing tracks older than retention limit."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
        with self._lock:
            empty_keys = []
            for mmsi, wps in self._tracks.items():
                filtered = [p for p in wps if p.get("timestamp_utc", datetime.now(timezone.utc)) >= cutoff]
                if not filtered:
                    empty_keys.append(mmsi)
                else:
                    self._tracks[mmsi] = filtered
            for k in empty_keys:
                del self._tracks[k]


# ---------------------------------------------------------------------------
# 5. Live AIS Service (Pipeline Orchestrator)
# ---------------------------------------------------------------------------

class LiveAISService:
    """Enterprise backend orchestrator for real-time streaming AIS telemetry."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        ws_url: Optional[str] = None,
        default_region: str = "SRI_LANKA_SOUTH",
        retention_hours: float = 12.0,
    ):
        self.api_key = api_key or os.getenv("AISSTREAM_API_KEY") or os.getenv("AIS_PROVIDER_KEY")
        self.ws_url = ws_url or os.getenv("AIS_WS_URL", "wss://stream.aisstream.io/v0/stream")
        self.current_region = default_region
        self.active_bbox = PREDEFINED_REGIONS.get(default_region, PREDEFINED_REGIONS["SRI_LANKA_SOUTH"])

        # Components
        self.validator = AISMessageValidator()
        self.normalizer = AISNormalizer()
        self.current_state = CurrentVesselState()
        self.track_store = HistoricalTrackStore(max_waypoints_per_vessel=500, retention_hours=retention_hours)
        self.identity_adapter = MaritimeVesselIdentityAdapter()

        # Connection & Health Lifecycle
        self._running = False
        self._connected = False
        self._worker_thread: Optional[threading.Thread] = None
        self._last_message_time: Optional[datetime] = None
        self._connection_attempts = 0
        self._total_messages_received = 0
        self._last_error: Optional[str] = None

        # Event stream subscribers (asyncio queues for SSE)
        self._subscribers: Set[asyncio.Queue] = set()
        self._sub_lock = threading.Lock()

    def is_configured(self) -> bool:
        """Returns True if provider credentials are set."""
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    def get_status(self) -> str:
        """Returns connection health state: LIVE, STALE, or DISCONNECTED."""
        if not self.is_configured() or not self._connected:
            return "DISCONNECTED"

        if self._last_message_time is None:
            return "DISCONNECTED"

        age = (datetime.now(timezone.utc) - self._last_message_time).total_seconds()
        if age > 45.0:
            return "STALE"
        return "LIVE"

    def get_health_telemetry(self) -> Dict[str, Any]:
        return {
            "status": self.get_status(),
            "configured": self.is_configured(),
            "connected": self._connected,
            "active_region": self.current_region,
            "active_bbox": self.active_bbox.as_tuple,
            "total_messages_processed": self._total_messages_received,
            "active_vessels_count": self.current_state.count(),
            "last_message_utc": self._last_message_time.isoformat() if self._last_message_time else None,
            "connection_attempts": self._connection_attempts,
            "last_error": self._last_error,
        }

    def set_active_region(self, region_name: str, custom_bbox: Optional[BoundingBox] = None):
        """Updates active subscription region."""
        if custom_bbox:
            self.current_region = "CUSTOM_VIEWPORT"
            self.active_bbox = custom_bbox
        elif region_name in PREDEFINED_REGIONS:
            self.current_region = region_name
            self.active_bbox = PREDEFINED_REGIONS[region_name]
        else:
            raise ValueError(f"Unknown predefined region '{region_name}'. Available: {list(PREDEFINED_REGIONS.keys())}")
        logger.info(f"Updated live AIS subscription region: {self.current_region} -> {self.active_bbox.as_tuple}")

    def ingest_raw_packet(self, raw_json_str: str) -> bool:
        """Processes an incoming raw AIS frame through validator and normalizer."""
        try:
            data = json.loads(raw_json_str)
        except Exception:
            return False

        meta = data.get("MetaData", {})
        msg_type = data.get("MessageType")
        raw_mmsi = meta.get("MMSI") or meta.get("mmsi") or data.get("mmsi")

        valid_mmsi, clean_mmsi = self.validator.validate_mmsi(raw_mmsi)
        if not valid_mmsi or not clean_mmsi:
            return False

        msg_body = data.get("Message", {}).get(msg_type, {}) if msg_type else data
        lat = msg_body.get("Latitude") or meta.get("latitude")
        lon = msg_body.get("Longitude") or meta.get("longitude")

        if not self.validator.validate_coordinates(lat, lon):
            return False

        sog_raw = msg_body.get("Sog") or msg_body.get("speed_over_ground")
        cog_raw = msg_body.get("Cog") or msg_body.get("course_over_ground")
        sog, cog = self.validator.validate_kinematics(sog_raw, cog_raw)
        heading = float(msg_body.get("TrueHeading") or cog)

        ts = self.normalizer.normalize_timestamp(meta.get("time_utc") or data.get("Timestamp"))
        ship_name = str(meta.get("ShipName") or msg_body.get("ShipName") or "UNKNOWN").strip()
        v_type = self.normalizer.map_vessel_type(msg_body.get("Type") or msg_body.get("ShipType"), ship_name)

        # Enriched Identity lookup
        ident = self.identity_adapter.lookup_by_mmsi(clean_mmsi) or {}

        normalized = {
            "mmsi": clean_mmsi,
            "vessel_name": ident.get("vessel_name") or ship_name,
            "vessel_type": ident.get("vessel_type") or v_type,
            "imo": ident.get("imo"),
            "flag_country": ident.get("flag_country"),
            "callsign": ident.get("callsign"),
            "latitude": round(float(lat), 6),
            "longitude": round(float(lon), 6),
            "speed_over_ground_knots": round(sog, 1),
            "course_over_ground_deg": round(cog, 1),
            "heading_deg": round(heading, 1),
            "last_update_utc": ts,
            "source_provider": "Live AIS Stream (WSS)",
        }

        # Update Current State
        self.current_state.update(clean_mmsi, normalized)

        # Store in rolling historical track
        self.track_store.add_waypoint(clean_mmsi, {
            "timestamp_utc": ts,
            "latitude": normalized["latitude"],
            "longitude": normalized["longitude"],
            "speed_over_ground_knots": normalized["speed_over_ground_knots"],
            "course_over_ground_deg": normalized["course_over_ground_deg"],
            "heading_deg": normalized["heading_deg"],
        })

        self._total_messages_received += 1
        self._last_message_time = datetime.now(timezone.utc)

        # Broadcast to event stream subscribers
        self._broadcast_event({
            "type": "VESSEL_UPDATE",
            "mmsi": clean_mmsi,
            "data": {
                **normalized,
                "last_update_utc": ts.isoformat(),
            },
        })

        return True

    def _broadcast_event(self, event_data: dict):
        """Pushes event payload to all active SSE subscriber queues."""
        with self._sub_lock:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(event_data)
                except Exception:
                    pass

    def start(self):
        """Spawns the resilient background WebSocket streaming client thread."""
        if not self.is_configured():
            logger.info("Live AIS service starting in passive mode (AISSTREAM_API_KEY unconfigured).")
            return

        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._run_async_worker, daemon=True, name="LiveAIS-Streamer")
        self._worker_thread.start()

    def stop(self):
        self._running = False
        self._connected = False

    def reset(self):
        """Resets all live cached states, tracks, and counters (useful for isolated tests)."""
        self.stop()
        self.current_state.clear()
        self.track_store.clear()
        self._last_message_time = None
        self._total_messages_received = 0
        self._last_error = None

    def _run_async_worker(self):
        asyncio.run(self._worker_lifecycle())

    async def _worker_lifecycle(self):
        import websockets

        backoff = 1.0
        while self._running:
            self._connection_attempts += 1
            try:
                logger.info(f"Connecting to live AIS stream at {self.ws_url} (Region: {self.current_region})...")
                async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=10) as ws:
                    self._connected = True
                    backoff = 1.0
                    self._last_message_time = datetime.now(timezone.utc)

                    b = self.active_bbox
                    sub_message = {
                        "APIKey": self.api_key,
                        "BoundingBoxes": [[[b.min_lat, b.min_lon], [b.max_lat, b.max_lon]]],
                        "FilterMessageTypes": ["PositionReport", "ShipStaticData"],
                    }
                    await ws.send(json.dumps(sub_message))
                    logger.info(f"AIS bounding box subscription sent for {self.current_region}: {b.as_tuple}")

                    while self._running:
                        msg_raw = await ws.recv()
                        self.ingest_raw_packet(msg_raw)

            except Exception as e:
                self._connected = False
                self._last_error = str(e)
                logger.warning(f"AIS connection interrupted: {e}. Reconnecting in {backoff:.1f}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, 60.0)

    # -----------------------------------------------------------------------
    # Queries & SSE Streams
    # -----------------------------------------------------------------------

    def get_live_vessels(
        self,
        bbox: Optional[BoundingBox] = None,
        vessel_type: Optional[str] = None,
        min_speed: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Queries currently buffered vessel states matching spatial/filter constraints."""
        target_bbox = bbox or self.active_bbox
        return self.current_state.get_all(bbox=target_bbox, vessel_type=vessel_type, min_speed=min_speed)

    def get_vessel_details(self, mmsi: str) -> Optional[Dict[str, Any]]:
        """Returns comprehensive telemetry, identity, and historical track trail for a single vessel."""
        v = self.current_state.get(mmsi)
        if not v:
            return None

        track = self.track_store.get_track(mmsi)
        serialized_track = []
        for wp in track:
            ts = wp.get("timestamp_utc")
            serialized_track.append({
                **wp,
                "timestamp_utc": ts.isoformat() if isinstance(ts, datetime) else str(ts),
            })

        # Calculate track gaps
        has_gaps = False
        gap_intervals = []
        if len(track) >= 2:
            for i in range(len(track) - 1):
                t1 = track[i].get("timestamp_utc")
                t2 = track[i + 1].get("timestamp_utc")
                if isinstance(t1, datetime) and isinstance(t2, datetime):
                    diff_hours = (t2 - t1).total_seconds() / 3600.0
                    if diff_hours > 1.0:
                        has_gaps = True
                        gap_intervals.append((t1.isoformat(), t2.isoformat()))

        details = dict(v)
        last_ts = details.get("last_update_utc")
        if isinstance(last_ts, datetime):
            details["last_update_utc"] = last_ts.isoformat()

        details["trail"] = serialized_track
        details["has_ais_gaps"] = has_gaps
        details["gap_intervals"] = gap_intervals
        details["waypoints_count"] = len(serialized_track)
        return details

    async def event_generator(self) -> AsyncGenerator[str, None]:
        """Server-Sent Events (SSE) generator streaming vessel events directly to browser clients."""
        q = asyncio.Queue()
        with self._sub_lock:
            self._subscribers.add(q)

        try:
            # Yield initial connection status handshake
            initial_msg = json.dumps({
                "type": "INITIAL_STATUS",
                "status": self.get_status(),
                "region": self.current_region,
                "active_vessels_count": self.current_state.count(),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            })
            yield f"data: {initial_msg}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send periodic heartbeat
                    hb = json.dumps({
                        "type": "HEARTBEAT",
                        "status": self.get_status(),
                        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    })
                    yield f"data: {hb}\n\n"
        finally:
            with self._sub_lock:
                self._subscribers.discard(q)


# Singleton production instance
live_ais_service = LiveAISService()
