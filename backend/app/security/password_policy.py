"""Enterprise Password Security Policy & Cryptographic Hashing.

Compliant with NIST SP 800-63B:
- PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte cryptographically random salt.
- Constant-time verification prevents timing side-channel attacks.
- Strict password composition policy.
"""

import hashlib
import hmac
import re
import secrets
from typing import Tuple


class PasswordPolicyViolation(ValueError):
    """Raised when a proposed password fails enterprise security complexity rules."""
    pass


def validate_password_complexity(password: str) -> None:
    """Validates that password meets enterprise security standards.

    Rules:
    - Minimum 8 characters in length
    - At least one uppercase ASCII letter [A-Z]
    - At least one lowercase ASCII letter [a-z]
    - At least one decimal digit [0-9]
    - At least one non-alphanumeric special symbol
    """
    if not password or len(password) < 8:
        raise PasswordPolicyViolation("Password must be at least 8 characters in length.")

    if not re.search(r"[A-Z]", password):
        raise PasswordPolicyViolation("Password must contain at least one uppercase letter (A-Z).")

    if not re.search(r"[a-z]", password):
        raise PasswordPolicyViolation("Password must contain at least one lowercase letter (a-z).")

    if not re.search(r"[0-9]", password):
        raise PasswordPolicyViolation("Password must contain at least one decimal digit (0-9).")

    if not re.search(r"[\W_]", password):
        raise PasswordPolicyViolation("Password must contain at least one special character or symbol.")


def hash_password(password: str) -> str:
    """Computes a cryptographically salted PBKDF2-HMAC-SHA256 hash.

    Format: pbkdf2_sha256$100000$<hex_salt>$<hex_hash>
    """
    validate_password_complexity(password)
    salt = secrets.token_bytes(16)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored PBKDF2 hash using constant-time comparison."""
    if not plain_password or not hashed_password:
        return False

    parts = hashed_password.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False

    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])

        candidate_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(candidate_hash, expected_hash)
    except Exception:
        return False
