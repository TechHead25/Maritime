# Security & Production-Readiness Assessment

**Project:** Maritime Oil-Spill Forensic Attribution Intelligence (SIH26143)  
**Security Policy Version:** 1.0.0 (SIH Demonstration & MVP Scope)  
**Document:** `SECURITY.md`  
**Last Audited:** 2026-09-02  

---

## 1. Security Philosophy & Scope

This platform is a **forensic decision-support intelligence tool** designed for maritime environmental protection authorities. In accordance with the SIH Hackathon prototype requirements, it focuses on deterministic mathematical integrity, observational data provenance, robust input sanitization, and defensive API architecture without unnecessary enterprise identity management overhead.

---

## 2. Defensive Controls Implemented

### 2.1 API Input Validation & Geospatial Sanitization
- **Strict Coordinate Bounding:** All incoming latitudes are enforced to $[-90.0^\circ, +90.0^\circ]$ and longitudes to $[-180.0^\circ, +180.0^\circ]$ via custom Pydantic validators (`backend/app/models/schemas.py`).
- **GeoJSON Polygon Validation:** Polygon geometries must contain at least 4 coordinate vertices and strictly enforce closed linear rings ($p_0 = p_n$).
- **MMSI Format Validation:** Maritime Mobile Service Identity numbers are validated against standard 9-digit formats (`^\d{9}$`), rejecting reserved broadcast strings (e.g., `999999999` or leading zeros).
- **Temporal Strictness:** All datetime inputs are parsed and converted to ISO 8601 UTC (`datetime.timezone.utc`). Naive timestamps are automatically converted to UTC to prevent timezone skew.

### 2.2 Path Traversal & Unsafe File Handling Mitigations
- **Strict Route Parameter Regex:** All `case_id` route path parameters enforce alphanumeric, hyphen, and underscore regex patterns (`^[a-zA-Z0-9_\-]+$`, max 128 characters), preventing directory traversal vectors (`../`, `..\\`).
- **Controlled File Generation:** Report generation restricts output paths within designated local directories (`docs/` and `data/`), blocking arbitrary disk writes.

### 2.3 Exception Masking & Information Disclosure Prevention
- **Global Error Handlers:** Unhandled server exceptions are intercepted by a global exception handler in `backend/app/main.py`. Tracebacks are logged internally while returning sanitized, structured JSON responses without leaking internal file paths or stack frames to the client.
- **Defensive HTTP Headers:** All responses include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-XSS-Protection: 1; mode=block`.

### 2.4 CORS Configuration
- CORS middleware is configured to support explicit allowed origins via the `CORS_ORIGINS` environment variable, defaulting to standard local frontend development ports (`http://localhost:5173`, `http://localhost:3000`).

---

## 3. Secret & Credential Management

- **Zero Committed Secrets:** The repository contains no API keys, private certificates, or database credentials.
- **Environment Template:** The `.env.example` file provides a standardized template for server ports, log levels, and allowed origins.

---

## 4. Remaining Limitations for Enterprise Production (Out of MVP Scope)

| Feature | Current Prototype Posture | Production Enterprise Recommendation |
|---|---|---|
| **Authentication & RBAC** | Open endpoints for local demo & evaluation. | Integrate OAuth2 / OpenID Connect (e.g. Keycloak, Auth0) with role-based access for Analysts, Lead Investigators, and Admins. |
| **Rate Limiting** | Unlimited local queries for testing. | Deploy Redis-backed token bucket rate limiting (e.g., `slowapi`) to mitigate DoS risks on CPU-intensive Monte Carlo simulations. |
| **Data Encryption at Rest** | Local filesystem storage (`data/cases/`). | Implement AES-256 encrypted storage volumes for sensitive telemetry dossiers. |
| **Live Telemetry Stream Auth** | Offline historical datasets and synthetic fixtures. | Implement TLS mutual authentication (mTLS) for real-time AIS receiver feeds and Copernicus CDSE API tokens. |

---

## 5. Security Incident Response

To report a vulnerability or security defect in this codebase, contact the project engineering team at the Smart India Hackathon coordination repository.
