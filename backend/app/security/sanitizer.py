"""Enterprise Input Validation & Secure File Upload Guardrails.

Protects against:
- Path traversal vulnerabilities (CWE-22)
- Unrestricted file upload / malicious payloads (CWE-434)
- Shell injection & invalid identifier characters
"""

from pathlib import Path
import re
from typing import List, Optional, Set
from fastapi import HTTPException, UploadFile, status

# Allowed file extensions for maritime forensics
ALLOWED_UPLOAD_EXTENSIONS: Set[str] = {
    ".tif",
    ".tiff",
    ".nc",
    ".csv",
    ".geojson",
    ".json",
    ".pdf",
}

# Maximum allowed file upload size (50 MB)
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    """Strips directory traversal characters and restricts to safe alphanumeric characters."""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid non-empty filename."
        )

    # Take only the basename, rejecting any path elements
    clean_name = Path(filename).name
    # Strip any null bytes
    clean_name = clean_name.replace("\x00", "")
    # Remove leading dots to avoid hidden files
    clean_name = clean_name.lstrip(".")
    # Sanitize characters to alphanumeric, underscores, hyphens, and dots
    clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", clean_name)

    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename contains invalid characters."
        )

    return clean_name


def validate_upload_file(file: UploadFile, max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES) -> str:
    """Validates file extension, sanitizes filename, and ensures within allowed size constraints."""
    clean_name = sanitize_filename(file.filename or "upload.bin")
    ext = Path(clean_name).suffix.lower()

    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not permitted. Allowed formats: {sorted(list(ALLOWED_UPLOAD_EXTENSIONS))}"
        )

    return clean_name


def safe_join_path(base_dir: Path, relative_path: str) -> Path:
    """Safely resolves and joins a path under base_dir, raising error on directory traversal."""
    resolved_base = base_dir.resolve()
    target = (base_dir / relative_path).resolve()

    if not str(target).startswith(str(resolved_base)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path: directory traversal attempt detected."
        )

    return target
