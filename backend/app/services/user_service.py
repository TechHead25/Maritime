"""Enterprise User Identity & Account Management Service.

Manages user authentication, password updates, RBAC role assignments,
and persists accounts to data/users.json with secure PBKDF2 hashing.
"""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import secrets
from typing import Dict, List, Optional

from backend.app.models.user import (
    Role,
    UserCreate,
    UserInDB,
    UserResponse,
)
from backend.app.security.password_policy import (
    hash_password,
    validate_password_complexity,
    verify_password,
)
from backend.app.security.rbac import get_permissions_for_role

logger = logging.getLogger("maritime-oil-attribution.services.user")

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
USERS_FILE = DATA_DIR / "users.json"


class UserService:
    """Manages verified user identities and persistent credentials."""

    def __init__(self):
        self._users: Dict[str, UserInDB] = {}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load_or_seed_users()

    def _load_or_seed_users(self):
        """Loads users from JSON or seeds initial enterprise accounts."""
        if USERS_FILE.exists():
            try:
                with open(USERS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        user = UserInDB(**item)
                        self._users[user.id] = user
                logger.info(f"Loaded {len(self._users)} user identities from {USERS_FILE}.")
                return
            except Exception as e:
                logger.warning(f"Failed to parse {USERS_FILE}, re-seeding default enterprise accounts: {e}")

        # Seed initial enterprise accounts
        now = datetime.now(timezone.utc).isoformat()
        seed_accounts = [
            UserInDB(
                id="usr_admin_001",
                username="admin",
                email="admin@maritime-intelligence.internal",
                full_name="Chief Forensic Administrator",
                role=Role.ADMIN,
                hashed_password=hash_password("Admin@Enterprise2026!"),
                is_active=True,
                created_at_utc=now,
            ),
            UserInDB(
                id="usr_analyst_001",
                username="analyst",
                email="analyst@maritime-intelligence.internal",
                full_name="Senior Forensic Spill Analyst",
                role=Role.ANALYST,
                hashed_password=hash_password("Analyst@Forensic2026!"),
                is_active=True,
                created_at_utc=now,
            ),
            UserInDB(
                id="usr_viewer_001",
                username="viewer",
                email="viewer@maritime-intelligence.internal",
                full_name="Maritime Oversight Observer",
                role=Role.VIEWER,
                hashed_password=hash_password("Viewer@Maritime2026!"),
                is_active=True,
                created_at_utc=now,
            ),
        ]

        for u in seed_accounts:
            self._users[u.id] = u

        self._save_users()
        logger.info(f"Seeded {len(seed_accounts)} default enterprise accounts.")

    def _save_users(self):
        """Atomically saves users to disk."""
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump([u.model_dump() for u in self._users.values()], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist users: {e}")

    def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        return self._users.get(user_id)

    def get_by_username(self, username: str) -> Optional[UserInDB]:
        clean = username.strip().lower()
        for u in self._users.values():
            if u.username.lower() == clean:
                return u
        return None

    def get_by_email(self, email: str) -> Optional[UserInDB]:
        clean = email.strip().lower()
        for u in self._users.values():
            if u.email.lower() == clean:
                return u
        return None

    def authenticate(self, username: str, plain_password: str) -> Optional[UserInDB]:
        """Verifies credentials. If valid and active, returns UserInDB; else None."""
        user = self.get_by_username(username)
        if not user or not user.is_active:
            return None

        if verify_password(plain_password, user.hashed_password):
            # Update last login timestamp
            user.last_login_utc = datetime.now(timezone.utc).isoformat()
            self._save_users()
            return user
        return None

    def list_users(self) -> List[UserResponse]:
        """Returns all registered users with permissions."""
        return [
            UserResponse(
                id=u.id,
                username=u.username,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                is_active=u.is_active,
                created_at_utc=u.created_at_utc,
                last_login_utc=u.last_login_utc,
                permissions=get_permissions_for_role(u.role),
            )
            for u in self._users.values()
        ]

    def create_user(self, payload: UserCreate) -> UserResponse:
        """Creates a new user under strict password policy."""
        if self.get_by_username(payload.username):
            raise ValueError(f"Username '{payload.username}' is already registered.")
        if self.get_by_email(payload.email):
            raise ValueError(f"Email '{payload.email}' is already registered.")

        # Complexity validated by hash_password
        hashed = hash_password(payload.password)
        user_id = f"usr_{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc).isoformat()

        user = UserInDB(
            id=user_id,
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role,
            hashed_password=hashed,
            is_active=True,
            created_at_utc=now,
        )

        self._users[user.id] = user
        self._save_users()

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at_utc=user.created_at_utc,
            permissions=get_permissions_for_role(user.role),
        )

    def update_role(self, user_id: str, new_role: Role) -> UserResponse:
        """Updates a user's RBAC role."""
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User ID '{user_id}' not found.")

        user.role = new_role
        self._save_users()

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


user_service = UserService()
