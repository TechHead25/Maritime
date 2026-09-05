"""Enterprise Security Audit Logging Service.

Maintains an immutable audit log for all security-critical operations:
- Authentication success & failure
- Logout events
- User creation & privilege escalation
- Case deletion / modification
- External provider reconfiguration

Stores records in an in-memory buffer (for admin queries) and appends to an append-only JSONL log.
"""

from collections import deque
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import secrets
from typing import Any, Dict, List, Optional
from fastapi import Request

from backend.app.models.user import AuditLogEntry

logger = logging.getLogger("maritime-oil-attribution.security.audit")

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
AUDIT_LOG_FILE = DATA_DIR / "audit_log.jsonl"


class SecurityAuditLogger:
    """Records and serves immutable audit log events."""

    def __init__(self, max_memory_entries: int = 1000):
        self._max_memory_entries = max_memory_entries
        self._memory_log = deque(maxlen=max_memory_entries)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load_existing_logs()

    def _load_existing_logs(self):
        """Loads last entries from file on startup."""
        if not AUDIT_LOG_FILE.exists():
            return
        try:
            with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-self._max_memory_entries:]:
                    if line.strip():
                        data = json.loads(line)
                        self._memory_log.append(AuditLogEntry(**data))
        except Exception as e:
            logger.warning(f"Failed to load existing audit logs: {e}")

    def log(
        self,
        action: str,
        resource: str,
        status: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None,
    ) -> AuditLogEntry:
        """Appends a new security event to memory and append-only audit trail."""
        entry = AuditLogEntry(
            id=f"audit_{secrets.token_hex(8)}",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            resource=resource,
            status=status,
            details=details,
        )

        self._memory_log.appendleft(entry)

        try:
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to persist audit log entry: {e}")

        logger.info(f"AUDIT [{status}] {action} on {resource} by {username or 'anonymous'} from {ip_address}")
        return entry

    def log_request(
        self,
        request: Request,
        action: str,
        resource: str,
        status: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        details: Optional[str] = None,
    ) -> AuditLogEntry:
        """Helper extracting IP and User-Agent directly from FastAPI Request."""
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        return self.log(
            action=action,
            resource=resource,
            status=status,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )

    def get_recent_logs(self, limit: int = 100) -> List[AuditLogEntry]:
        """Returns most recent audit events."""
        return list(self._memory_log)[:limit]


audit_logger = SecurityAuditLogger()
