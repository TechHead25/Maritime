"""Role-Based Access Control (RBAC) & Authorization Dependencies.

Defines role hierarchies and permissions:
ADMIN:
- manage users
- manage providers
- manage settings
- access all investigations

ANALYST:
- create investigations
- run investigations
- access live maritime
- generate reports

VIEWER:
- view investigations
- view reports
- view approved live data
"""

from typing import Callable, List, Optional, Set
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.models.user import Role, UserInDB, UserResponse
from backend.app.security.token_service import decode_access_token

security_scheme = HTTPBearer(auto_error=False)

# Explicit Permission Matrix
PERMISSIONS_BY_ROLE = {
    Role.ADMIN: {
        "manage:users",
        "manage:providers",
        "manage:settings",
        "access:all_investigations",
        "create:investigations",
        "run:investigations",
        "access:live_maritime",
        "generate:reports",
        "view:investigations",
        "view:reports",
        "view:live_maritime",
    },
    Role.ANALYST: {
        "create:investigations",
        "run:investigations",
        "access:live_maritime",
        "generate:reports",
        "view:investigations",
        "view:reports",
        "view:live_maritime",
    },
    Role.VIEWER: {
        "view:investigations",
        "view:reports",
        "view:live_maritime",
    },
}


def get_permissions_for_role(role: Role) -> List[str]:
    """Returns sorted list of permissions for a role."""
    return sorted(list(PERMISSIONS_BY_ROLE.get(role, set())))


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> UserResponse:
    """Dependency extracting and validating current user from JWT token."""
    from backend.app.services.user_service import user_service

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    username = payload.get("sub")

    user = user_service.get_by_id(user_id) or user_service.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated.",
        )

    return UserResponse(
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


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> Optional[UserResponse]:
    """Dependency that returns current user if token is provided, or None if anonymous."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_role(allowed_roles: List[Role]) -> Callable:
    """Dependency factory enforcing that the authenticated user possesses one of the allowed roles."""
    async def role_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {[r.value for r in allowed_roles]}.",
            )
        return current_user

    return role_checker


def require_permission(required_permission: str) -> Callable:
    """Dependency factory enforcing that the authenticated user has a specific permission."""
    async def permission_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        granted = PERMISSIONS_BY_ROLE.get(current_user.role, set())
        if required_permission not in granted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Missing required permission '{required_permission}'.",
            )
        return current_user

    return permission_checker
