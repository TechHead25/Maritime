"""User and Security Schemas for Authentication and RBAC.

Enforces strictly typed models for:
- Roles: ADMIN, ANALYST, VIEWER
- Credentials & Tokens
- Audit Log Records
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Role(str, Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class UserBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    email: str = Field(..., min_length=5, max_length=120)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: Role = Role.VIEWER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdateRole(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role


class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at_utc: str
    last_login_utc: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)


class UserInDB(UserBase):
    id: str
    hashed_password: str
    is_active: bool = True
    created_at_utc: str
    last_login_utc: Optional[str] = None


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserResponse


class AuditLogEntry(BaseModel):
    id: str
    timestamp_utc: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    action: str
    resource: str
    status: str  # SUCCESS or FAILURE
    details: Optional[str] = None
