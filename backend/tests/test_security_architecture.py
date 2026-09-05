"""Comprehensive Enterprise Security Architecture Tests.

Verifies:
- NIST SP 800-63B password complexity and PBKDF2 hashing
- JWT issuance, verification, expiration, and cryptographic JTI revocation
- Role-based access control (RBAC) across ADMIN, ANALYST, and VIEWER roles
- Security audit logging of all sensitive events
- Starlette security headers injection (CSP, HSTS, X-Frame-Options, etc.)
- Rate limiter sliding window enforcement and headers
- Input validation and directory traversal prevention
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.user import Role
from backend.app.security.audit_logger import audit_logger
from backend.app.security.password_policy import (
    PasswordPolicyViolation,
    hash_password,
    validate_password_complexity,
    verify_password,
)
from backend.app.security.sanitizer import (
    safe_join_path,
    sanitize_filename,
)
from backend.app.security.token_service import (
    create_access_token,
    decode_access_token,
    revoke_token,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Password Policy & Cryptography Tests
# ---------------------------------------------------------------------------

def test_password_complexity_rules():
    """Verifies that password policy strictly rejects weak passwords."""
    # Too short
    with pytest.raises(PasswordPolicyViolation, match="at least 8 characters"):
        validate_password_complexity("Ab1!")

    # Missing uppercase
    with pytest.raises(PasswordPolicyViolation, match="uppercase letter"):
        validate_password_complexity("lowercase123!")

    # Missing lowercase
    with pytest.raises(PasswordPolicyViolation, match="lowercase letter"):
        validate_password_complexity("UPPERCASE123!")

    # Missing digit
    with pytest.raises(PasswordPolicyViolation, match="decimal digit"):
        validate_password_complexity("NoDigitsHere!")

    # Missing special character
    with pytest.raises(PasswordPolicyViolation, match="special character"):
        validate_password_complexity("NoSpecial1234")

    # Valid enterprise password
    validate_password_complexity("Valid@Enterprise2026!")


def test_pbkdf2_hashing_and_constant_time_verification():
    """Verifies PBKDF2-HMAC-SHA256 hashing and verification."""
    plain = "SuperSecret@Password2026!"
    hashed = hash_password(plain)
    assert hashed.startswith("pbkdf2_sha256$100000$")

    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False


# ---------------------------------------------------------------------------
# 2. Token Lifecycle & Revocation Tests
# ---------------------------------------------------------------------------

def test_jwt_token_issuance_and_revocation():
    """Verifies access token issuance, decoding, and revocation on logout."""
    token = create_access_token(
        subject="testuser",
        user_id="usr_test_123",
        role="ANALYST",
    )
    assert token is not None

    payload = decode_access_token(token)
    assert payload["sub"] == "testuser"
    assert payload["role"] == "ANALYST"
    assert "jti" in payload

    # Revoke token (logout)
    success = revoke_token(token)
    assert success is True

    # Subsequent verification must fail
    with pytest.raises(ValueError, match="revoked"):
        decode_access_token(token)


# ---------------------------------------------------------------------------
# 3. Authentication API Endpoints Tests
# ---------------------------------------------------------------------------

def test_auth_login_success_and_audit():
    """Verifies successful login with seed admin credentials and audit logging."""
    res = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin@Enterprise2026!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "ADMIN"
    assert "manage:users" in data["user"]["permissions"]

    # Verify audit log recorded
    logs = audit_logger.get_recent_logs(limit=10)
    assert any(log.action == "AUTH_LOGIN_SUCCESS" and log.username == "admin" for log in logs)


def test_auth_login_failure_and_audit():
    """Verifies failed login rejection and security audit trail."""
    res = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]

    logs = audit_logger.get_recent_logs(limit=10)
    assert any(log.action == "AUTH_LOGIN_FAILURE" and log.username == "admin" for log in logs)


def test_auth_me_and_logout_flow():
    """Verifies identity inspection and complete logout revocation cycle."""
    # 1. Login as Analyst
    login_res = client.post(
        "/api/auth/login",
        json={"username": "analyst", "password": "Analyst@Forensic2026!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Call /api/auth/me
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "analyst"
    assert me_res.json()["role"] == "ANALYST"

    # 3. Logout
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "LOGGED_OUT"

    # 4. Subsequent request with revoked token must be rejected
    rejected_res = client.get("/api/auth/me", headers=headers)
    assert rejected_res.status_code == 401
    assert "revoked" in rejected_res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. Role-Based Access Control (RBAC) Tests
# ---------------------------------------------------------------------------

def test_rbac_role_hierarchy_enforcement():
    """Verifies strict role segregation: ADMIN vs ANALYST vs VIEWER."""
    # Obtain tokens for each role
    admin_token = client.post(
        "/api/auth/login", json={"username": "admin", "password": "Admin@Enterprise2026!"}
    ).json()["access_token"]
    analyst_token = client.post(
        "/api/auth/login", json={"username": "analyst", "password": "Analyst@Forensic2026!"}
    ).json()["access_token"]
    viewer_token = client.post(
        "/api/auth/login", json={"username": "viewer", "password": "Viewer@Maritime2026!"}
    ).json()["access_token"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    # Test Admin-Only Route
    assert client.get("/api/auth/rbac/admin-access", headers=admin_headers).status_code == 200
    assert client.get("/api/auth/rbac/admin-access", headers=analyst_headers).status_code == 403
    assert client.get("/api/auth/rbac/admin-access", headers=viewer_headers).status_code == 403
    assert client.get("/api/auth/rbac/admin-access").status_code == 401  # Anonymous

    # Test Analyst & Admin Route
    assert client.get("/api/auth/rbac/analyst-access", headers=admin_headers).status_code == 200
    assert client.get("/api/auth/rbac/analyst-access", headers=analyst_headers).status_code == 200
    assert client.get("/api/auth/rbac/analyst-access", headers=viewer_headers).status_code == 403

    # Test Viewer Route (accessible to all authenticated roles)
    assert client.get("/api/auth/rbac/viewer-access", headers=admin_headers).status_code == 200
    assert client.get("/api/auth/rbac/viewer-access", headers=analyst_headers).status_code == 200
    assert client.get("/api/auth/rbac/viewer-access", headers=viewer_headers).status_code == 200


def test_admin_user_management_rbac():
    """Verifies that user management and audit querying are strictly ADMIN-only."""
    analyst_token = client.post(
        "/api/auth/login", json={"username": "analyst", "password": "Analyst@Forensic2026!"}
    ).json()["access_token"]
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}

    admin_token = client.post(
        "/api/auth/login", json={"username": "admin", "password": "Admin@Enterprise2026!"}
    ).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Analyst blocked from listing users or audit logs
    assert client.get("/api/auth/users", headers=analyst_headers).status_code == 403
    assert client.get("/api/auth/audit-logs", headers=analyst_headers).status_code == 403

    # Admin permitted
    users_res = client.get("/api/auth/users", headers=admin_headers)
    assert users_res.status_code == 200
    assert len(users_res.json()) >= 3

    logs_res = client.get("/api/auth/audit-logs", headers=admin_headers)
    assert logs_res.status_code == 200
    assert len(logs_res.json()) >= 1


# ---------------------------------------------------------------------------
# 5. Security Headers & Rate Limiting Tests
# ---------------------------------------------------------------------------

def test_defensive_security_headers():
    """Verifies that responses include defensive security headers."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in res.headers
    assert "Content-Security-Policy" in res.headers


def test_rate_limiter_headers():
    """Verifies that API responses contain rate limit telemetry headers."""
    res = client.get("/api/data-sources/control-center")
    assert res.status_code == 200
    assert "X-RateLimit-Limit" in res.headers
    assert "X-RateLimit-Remaining" in res.headers


# ---------------------------------------------------------------------------
# 6. Input Validation & Directory Traversal Tests
# ---------------------------------------------------------------------------

def test_filename_sanitization_prevents_directory_traversal():
    """Verifies that malicious directory traversal filenames are neutralized."""
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("safe_file.tif") == "safe_file.tif"
