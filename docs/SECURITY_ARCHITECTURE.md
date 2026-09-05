# Enterprise Security Architecture

**System:** Maritime Oil-Spill Attribution Intelligence Platform  
**Module:** Enterprise Application Security, Authentication & Access Control  
**Specification Document:** `docs/SECURITY_ARCHITECTURE.md`

---

## 1. Architectural Principles

This application adheres to enterprise defense-in-depth security standards:
- **Zero Fake Authentication:** Authentication is backed by cryptographic identity verification, salted PBKDF2 hashing, signed JWT tokens, and stateful session revocation.
- **Role-Based Access Control (RBAC):** Every endpoint and forensic operation enforces strict role and permission verification.
- **Zero Secret Exposure:** Secrets and API keys are stored exclusively in environment variables (`.env`). Secrets are never committed to source control, never bundled into client JavaScript, and never transmitted in API responses.
- **Comprehensive Auditability:** All authentication attempts, privilege changes, and administrative actions are immutably logged.

---

## 2. Role-Based Access Control (RBAC) Matrix

The system defines three formal roles with granular permissions:

```
                  +-----------------------------------+
                  |               ADMIN               |
                  |  (System Settings & Provider Mgt) |
                  +-----------------+-----------------+
                                    | inherits
                  +-----------------v-----------------+
                  |              ANALYST              |
                  | (Forensic Pipeline & Case Exec)   |
                  +-----------------+-----------------+
                                    | inherits
                  +-----------------v-----------------+
                  |               VIEWER              |
                  |  (Read-Only Reports & Inspection) |
                  +-----------------------------------+
```

### Granular Permission Mapping

| Permission | Description | ADMIN | ANALYST | VIEWER |
|---|---|:---:|:---:|:---:|
| `manage:users` | Provision users, update roles, deactivate accounts | ✅ | ❌ | ❌ |
| `manage:providers` | Configure external data sources, fallback rules, API timeouts | ✅ | ❌ | ❌ |
| `manage:settings` | Configure global system parameters & security policies | ✅ | ❌ | ❌ |
| `access:all_investigations` | Delete cases, override case locks, manage archives | ✅ | ❌ | ❌ |
| `create:investigations` | Establish new forensic investigation cases | ✅ | ✅ | ❌ |
| `run:investigations` | Trigger backward Lagrangian drift, CFAR segmentation, attribution | ✅ | ✅ | ❌ |
| `access:live_maritime` | View real-time AIS feed & launch investigations from vessels | ✅ | ✅ | ❌ |
| `generate:reports` | Export court-ready forensic PDF dossiers | ✅ | ✅ | ❌ |
| `view:investigations` | Inspect cases, satellite rasters, and attribution matrices | ✅ | ✅ | ✅ |
| `view:reports` | Download and view generated forensic reports | ✅ | ✅ | ✅ |
| `view:live_maritime` | View approved live maritime tracking layer | ✅ | ✅ | ✅ |

---

## 3. Password Security Policy & Cryptography

All local credentials strictly follow **NIST SP 800-63B** guidelines:

### Password Complexity Rules
1. **Length:** Minimum 8 characters.
2. **Character Diversity:** Must contain at least one uppercase letter `[A-Z]`, one lowercase letter `[a-z]`, one decimal digit `[0-9]`, and one non-alphanumeric special character `[\W_]`.

### Cryptographic Hashing
- **Algorithm:** PBKDF2 with HMAC-SHA256.
- **Work Factor:** 100,000 iterations.
- **Salt:** 16-byte cryptographically secure random salt generated via `secrets.token_bytes(16)`.
- **Format:** `pbkdf2_sha256$100000$<salt_hex>$<derived_key_hex>`
- **Constant-Time Verification:** Verification utilizes `hmac.compare_digest` to prevent timing side-channel attacks.

---

## 4. Session & Token Lifecycle

### JSON Web Token (JWT) Specifications
- **Signature Algorithm:** HMAC-SHA256 (`HS256`).
- **Secret Key:** Loaded from `JWT_SECRET_KEY` or `SECRET_KEY` environment variables. If unconfigured in development, a high-entropy 256-bit ephemeral secret is generated at startup.
- **Standard Claims:**
  - `sub`: Username
  - `user_id`: Unique persistent account ID
  - `role`: Assigned RBAC role
  - `jti`: Unique 128-bit cryptographic token identifier
  - `iat` / `nbf`: Token issuance timestamp
  - `exp`: Token expiration timestamp (default: 60 minutes)

### Logout & Token Revocation
Unlike stateless JWT architectures that cannot immediately terminate sessions, this platform enforces cryptographic token revocation:
1. Upon `POST /api/auth/logout`, the token's `jti` is permanently committed to the backend `TokenRevocationStore`.
2. Every subsequent API request checks the `jti` against the revocation blacklist; revoked tokens are immediately rejected with HTTP 401 Unauthorized.

---

## 5. Security Audit Logging

Security-critical events are recorded by [`SecurityAuditLogger`](file:///c:/Projects/Maritime_Oil/backend/app/security/audit_logger.py) to both an in-memory query buffer and an append-only file (`data/audit_log.jsonl`):

### Audited Actions
- `AUTH_LOGIN_SUCCESS`: Successful authentication
- `AUTH_LOGIN_FAILURE`: Failed authentication attempt (bad credentials)
- `AUTH_LOGOUT`: Session revocation and token invalidation
- `USER_CREATE`: Account creation
- `USER_ROLE_UPDATE`: Role or privilege elevation
- `PROVIDER_CONFIGURE`: Modification of data source parameters
- `INVESTIGATION_DELETE`: Permanent deletion of forensic case

### Audit Record Schema
```json
{
  "id": "audit_8f2b7194a02c9183",
  "timestamp_utc": "2026-09-03T05:30:12.849201Z",
  "user_id": "usr_admin_001",
  "username": "admin",
  "ip_address": "192.168.1.50",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
  "action": "USER_ROLE_UPDATE",
  "resource": "/api/auth/users/usr_analyst_001/role",
  "status": "SUCCESS",
  "details": "Updated role of 'analyst' to ADMIN."
}
```

---

## 6. Rate Limiting & Denial-of-Service (DoS) Mitigation

The application implements a sliding-window in-memory rate limiter ([`RateLimiterMiddleware`](file:///c:/Projects/Maritime_Oil/backend/app/security/rate_limiter.py)):

| Route Class | Rate Limit Threshold | Window | Mitigation Target |
|---|---|---|---|
| Authentication (`/api/auth/login`) | **10 requests / minute** | 60 seconds | Brute-force credential guessing |
| General API (`/api/*`) | **180 requests / minute** | 60 seconds | Pipeline DoS & resource exhaustion |

When a client exceeds the limit, the server responds with **HTTP 429 Too Many Requests**, providing standard RFC 6585 headers:
- `X-RateLimit-Limit`: Maximum allowed requests per window
- `X-RateLimit-Remaining`: Remaining request quota
- `Retry-After`: Seconds until quota replenishment

---

## 7. Defensive HTTP Security Headers

Every HTTP response produced by the FastAPI gateway includes defensive security headers via [`SecurityHeadersMiddleware`](file:///c:/Projects/Maritime_Oil/backend/app/main.py):

| Header | Value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type confusion attacks |
| `X-Frame-Options` | `DENY` | Prevents clickjacking and iframe embedding |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Enforces HTTPS communication |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Minimizes URL leakage in external requests |
| `X-XSS-Protection` | `1; mode=block` | Enables legacy browser cross-site scripting filters |
| `Content-Security-Policy` | Strict CSP policy | Prevents malicious script execution and external injection |
| `Permissions-Policy` | `geolocation=(), camera=(), microphone=()` | Disables unwanted browser capabilities |

---

## 8. Input Validation & Secure File Uploads

[`backend/app/security/sanitizer.py`](file:///c:/Projects/Maritime_Oil/backend/app/security/sanitizer.py) provides strict boundary sanitation:
- **Directory Traversal Neutralization (CWE-22):** All uploaded filenames are stripped of path components (`../`, `..\`) and null bytes, restricting characters to safe alphanumeric tokens.
- **Path Resolution Check:** `safe_join_path` validates that all resolved file targets strictly remain within the designated root directory.
- **Upload File Restrictions (CWE-434):**
  - Allowed extensions: `.tif`, `.tiff`, `.nc`, `.csv`, `.geojson`, `.json`, `.pdf`.
  - Maximum upload size: **50 MB** per file.

---

## 9. Default Enterprise Identities (Seeded Accounts)

For enterprise testing and local deployments, the following accounts are initialized with compliant credentials:

| Username | Default Password | Role | Primary Function |
|---|---|---|---|
| `admin` | `Admin@Enterprise2026!` | `ADMIN` | System administration, user provisioning, provider settings |
| `analyst` | `Analyst@Forensic2026!` | `ANALYST` | Full forensic investigation execution, drift simulation, reporting |
| `viewer` | `Viewer@Maritime2026!` | `VIEWER` | Read-only inspection of reports and approved live data |

*(Note: In production environments, default passwords should be updated immediately via the user management console).*
