"""Authentication and Security API Router.

Exposes endpoints for:
- User login / JWT token issuance
- Session logout & token revocation
- Current user identity (/me)
- User administration (ADMIN only)
- Immutable security audit logs (ADMIN only)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials

from backend.app.models.user import (
    AuditLogEntry,
    LoginRequest,
    LoginResponse,
    Role,
    UserCreate,
    UserResponse,
    UserUpdateRole,
)
from backend.app.security.audit_logger import audit_logger
from backend.app.security.rbac import (
    get_current_user,
    get_permissions_for_role,
    require_role,
    security_scheme,
)
from backend.app.security.token_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    revoke_token,
)
from backend.app.services.user_service import user_service

auth_router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@auth_router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate User and Issue JWT Session Token",
)
def login(payload: LoginRequest, request: Request):
    """Verifies credentials, records security audit event, and returns signed JWT access token."""
    user = user_service.authenticate(payload.username, payload.password)
    if not user:
        audit_logger.log_request(
            request=request,
            action="AUTH_LOGIN_FAILURE",
            resource="/api/auth/login",
            status="FAILURE",
            username=payload.username,
            details="Invalid username or password provided.",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        subject=user.username,
        user_id=user.id,
        role=user.role.value,
    )

    audit_logger.log_request(
        request=request,
        action="AUTH_LOGIN_SUCCESS",
        resource="/api/auth/login",
        status="SUCCESS",
        user_id=user.id,
        username=user.username,
        details=f"Authenticated with role {user.role.value}.",
    )

    user_resp = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at_utc=user.created_at_utc,
        last_login_utc=user.last_login_utc,
        permissions=get_permissions_for_role(user.role),
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_resp,
    )


@auth_router.post(
    "/logout",
    summary="Revoke Session Token and Logout",
)
def logout(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    current_user: UserResponse = Depends(get_current_user),
):
    """Invalidates the provided token JTI in the revocation blacklist and terminates session."""
    if credentials and credentials.credentials:
        revoke_token(credentials.credentials)

    audit_logger.log_request(
        request=request,
        action="AUTH_LOGOUT",
        resource="/api/auth/logout",
        status="SUCCESS",
        user_id=current_user.id,
        username=current_user.username,
        details="Session token revoked.",
    )

    return {
        "status": "LOGGED_OUT",
        "message": "Session token successfully revoked. User logged out.",
    }


@auth_router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve Current User Identity & Permissions",
)
def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Returns validated identity and role-based permissions for the active session."""
    return current_user


@auth_router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List All System Users (ADMIN only)",
)
def list_users(admin_user: UserResponse = Depends(require_role([Role.ADMIN]))):
    """Returns all registered users. Restricted to ADMIN role."""
    return user_service.list_users()


@auth_router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account (ADMIN only)",
)
def create_user(
    payload: UserCreate,
    request: Request,
    admin_user: UserResponse = Depends(require_role([Role.ADMIN])),
):
    """Provisions a new user with enforced password complexity policy. Restricted to ADMIN role."""
    try:
        new_user = user_service.create_user(payload)
        audit_logger.log_request(
            request=request,
            action="USER_CREATE",
            resource=f"/api/auth/users/{new_user.id}",
            status="SUCCESS",
            user_id=admin_user.id,
            username=admin_user.username,
            details=f"Created account '{new_user.username}' with role {new_user.role.value}.",
        )
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.put(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="Update User Role & Privileges (ADMIN only)",
)
def update_user_role(
    user_id: str,
    payload: UserUpdateRole,
    request: Request,
    admin_user: UserResponse = Depends(require_role([Role.ADMIN])),
):
    """Updates a user's RBAC role. Restricted to ADMIN role."""
    try:
        updated = user_service.update_role(user_id, payload.role)
        audit_logger.log_request(
            request=request,
            action="USER_ROLE_UPDATE",
            resource=f"/api/auth/users/{user_id}/role",
            status="SUCCESS",
            user_id=admin_user.id,
            username=admin_user.username,
            details=f"Updated role of '{updated.username}' to {payload.role.value}.",
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@auth_router.get(
    "/audit-logs",
    response_model=List[AuditLogEntry],
    summary="Query Immutable Security Audit Trail (ADMIN only)",
)
def get_audit_logs(
    limit: int = 100,
    admin_user: UserResponse = Depends(require_role([Role.ADMIN])),
):
    """Returns chronologically ordered security audit log entries. Restricted to ADMIN role."""
    return audit_logger.get_recent_logs(limit=min(limit, 500))


@auth_router.get(
    "/rbac/admin-access",
    summary="RBAC Verification: Admin-Only Route",
)
def test_admin_access(admin_user: UserResponse = Depends(require_role([Role.ADMIN]))):
    """Tests administrative RBAC authorization."""
    return {
        "status": "AUTHORIZED",
        "role": admin_user.role,
        "message": "Administrative privileges verified.",
    }


@auth_router.get(
    "/rbac/analyst-access",
    summary="RBAC Verification: Analyst & Admin Route",
)
def test_analyst_access(analyst_user: UserResponse = Depends(require_role([Role.ADMIN, Role.ANALYST]))):
    """Tests analyst and administrator RBAC authorization."""
    return {
        "status": "AUTHORIZED",
        "role": analyst_user.role,
        "message": "Forensic analyst privileges verified.",
    }


@auth_router.get(
    "/rbac/viewer-access",
    summary="RBAC Verification: Viewer, Analyst & Admin Route",
)
def test_viewer_access(user: UserResponse = Depends(require_role([Role.ADMIN, Role.ANALYST, Role.VIEWER]))):
    """Tests baseline viewer RBAC authorization."""
    return {
        "status": "AUTHORIZED",
        "role": user.role,
        "message": "Viewer privileges verified.",
    }

