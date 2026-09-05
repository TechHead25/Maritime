# Real Historical AIS Data Adapter & Validation Pipeline

**Component:** AIS Ingestion & Trajectory Normalization Subsystem  
**Module:** `backend/app/providers/ais_adapter.py`  
**Audit Utility:** `backend/app/utils/validate_ais_dataset.py`  
**Dataset Case Study:** *MT New Diamond* (September 2020, Bay of Bengal / Sri Lanka)

---

## 1. Overview & Forensic Architecture

The Historical AIS Data Adapter ingests raw telemetry feeds (CSV / JSON / GeoJSON / NMEA extracts) and converts them into strongly-typed, chronologically-ordered `VesselTrack` domain models without modifying the underlying attribution scoring formula.

```
[ Raw AIS Dataset (CSV / JSON) ]
               │
               ▼
[ HistoricalAISCSVAdapter ]
  ├── 1. Schema & Column Key Normalization
  ├── 2. Strict 9-Digit MMSI Validation
  ├── 3. Coordinate Bounds Validation ([-90, 90], [-180, 180])
  ├── 4. ISO 8601 UTC Timestamp Enforcement
  ├── 5. Duplicate Ping Deduplication
  ├── 6. ITU-R M.1371 Ship Type Code Mapping
  └── 7. Transponder Gap Detection (> 60 min)
               │
               ▼
   [ List[VesselTrack] ] (Canonical Domain Models)
```

---

## 2. Ingestion & Transformation Rules

In strict compliance with `GEMINI.md` rules (**Zero Data Fabrication & No Silent Repairs**):

### 2.1 UTC Timestamp Normalization
- All timestamps are converted to `datetime.timezone.utc`.
- Ambiguous local timestamps are rejected or strictly cast to UTC based on ISO 8601 `Z` specifiers.

### 2.2 MMSI Numerical Validation
- Validated against standard Maritime Mobile Service Identity specifications ($9\text{ digits}$, starting with MID digit $2-7$).
- Test identifiers (`999999999`), base station buoys (`00...`), or non-numeric strings (`INVALID_MMSI`) are logged in the rejection audit and filtered out.

### 2.3 Coordinate Validation
- Longitudes outside $[-180.0, 180.0]$ and Latitudes outside $[-90.0, 90.0]$ (e.g. sensor glitch $95.0^\circ\text{N}$) are immediately flagged as invalid and rejected.
- Coordinates are never "clamped" or silently repaired.

### 2.4 Duplicate Ping Deduplication
- Pings sharing the exact same `(MMSI, UTC_timestamp)` are deduplicated, preserving the first valid record.

### 2.5 ITU-R M.1371 Ship Type Classification
Maps international numeric AIS ship type codes to canonical `VesselType`:
- **80–89:** `VesselType.TANKER` (Crude, Chemical, Product, LNG/LPG)
- **70–79:** `VesselType.CARGO` (Container, Bulk Carrier, General Cargo)
- **31, 32, 52:** `VesselType.BUNKER` (Tugs, Port Service, Bunkering)
- **30:** `VesselType.FISHING` (Trawlers, Longliners)
- **60–69:** `VesselType.PASSENGER` (Ferries, Cruise Ships)
- **Other:** `VesselType.OTHER`

### 2.6 Transponder Gap Detection
- Chronological time intervals between successive waypoints exceeding $3600\text{ seconds}$ ($1\text{ hour}$) are flagged:
  - `track.has_ais_gaps = True`
  - `track.gap_intervals.append((T_last, T_resume))`

---

## 3. Data Validation Audit Tool (`validate_ais_dataset.py`)

Run the standalone validation tool from the project root:

```bash
python -m backend.app.utils.validate_ais_dataset data/ais/new_diamond_ais_raw.csv
```

### Sample Audit Output (*MT New Diamond* Benchmark):
```
======================================================================
  MARITIME AIS DATASET VALIDATION & INTEGRITY AUDIT REPORT
======================================================================
File Path:                data/ais/new_diamond_ais_raw.csv
Total Rows Ingested:      29
Valid Position Reports:   25
Rejected Invalid Rows:    4
Unique Vessels (MMSIs):   5
----------------------------------------------------------------------
TIME ENVELOPE (UTC):
  Earliest Timestamp:     2020-09-02T22:00:00+00:00
  Latest Timestamp:       2020-09-03T15:00:00+00:00
  Span Duration:          17.0 hours
----------------------------------------------------------------------
GEOGRAPHIC BOUNDING BOX:
  Longitude:              [82.0124°E, 83.1524°E]
  Latitude:               [7.2014°N, 8.4751°N]
----------------------------------------------------------------------
DATA QUALITY AUDIT:
  Duplicate Records:      1 (Deduplicated)
  Invalid Coordinates:    1 (Rejected: Lat=95.0000°N)
  Invalid/Test MMSIs:     2 (Rejected: '999999999', 'INVALID_MMSI')
----------------------------------------------------------------------
UNIQUE VESSELS IDENTIFIED:
  • MMSI: 353130000 | Vessel: MSC LAUREN (Cargo / Container)
  • MMSI: 371584000 | Vessel: MT NEW DIAMOND (Tanker / VLCC - Gap at 03:25 UTC)
  • MMSI: 419001122 | Vessel: JAG LALIT (Tanker / Crude)
  • MMSI: 440129000 | Vessel: GLOVIS SYMPHONY (Cargo / Vehicle Carrier)
  • MMSI: 538008821 | Vessel: PACIFIC DOLPHIN (Tanker / Chemical)
======================================================================
```
