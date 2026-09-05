"""Main FastAPI Application Entry Point for Maritime Oil-Spill Attribution Intelligence.

Implements:
- Strict CORS configuration (configurable via CORS_ORIGINS env var)
- Global exception handlers preventing internal stack trace disclosure
- Security response headers middleware
- Health and diagnostic routes
"""

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, List

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.api.router import api_router
from backend.app.api.auth_router import auth_router
from backend.app.security.rate_limiter import RateLimiterMiddleware

# Configure structured logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("maritime-oil-attribution")

app = FastAPI(
    title="Maritime Oil-Spill Attribution Intelligence API",
    description="Backend API for SAR Slick Detection, Backward Drift Simulation, AIS Interception, and Explainable Forensic Attribution",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects defensive HTTP security headers into all API responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' https: ws: wss:; "
            "frame-ancestors 'none';"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimiterMiddleware)


# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------

cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

# If wildcard "*" is included or no specific restriction is configured,
# use allow_origin_regex to permit any Vercel preview or localhost deployment seamlessly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$|^http:\/\/localhost(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global Exception Handlers
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation failures with structured, non-leaking error responses."""
    logger.warning(f"Request validation error for {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "RequestValidationError",
            "message": "The submitted payload failed schema validation.",
            "details": exc.errors(),
            "path": request.url.path,
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled server exceptions, logs full stack trace, and returns safe error payload."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the forensic analysis request.",
            "path": request.url.path,
        }
    )


# ---------------------------------------------------------------------------
# Router Mounting & Root Status
# ---------------------------------------------------------------------------

app.include_router(auth_router, prefix="/api")
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "platform": "Maritime Oil-Spill Attribution Intelligence Platform",
        "subtitle": "Maritime Environmental Intelligence & Forensic Decision Support",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health",
        "cases": "/api/cases"
    }


@app.get("/health", tags=["Health"])
def root_health():
    from backend.app.services.case_service import case_service
    return {
        "status": "healthy",
        "service": "Maritime Oil-Spill Attribution Intelligence API",
        "version": "0.1.0-mvp",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "loaded_cases_count": len(case_service.list_cases())
    }


@app.get("/health/live", tags=["Health"])
def root_liveness():
    return {"status": "alive", "timestamp_utc": datetime.now(timezone.utc).isoformat()}


@app.get("/health/ready", tags=["Health"])
def root_readiness():
    from backend.app.services.case_service import case_service
    return {
        "status": "ready",
        "loaded_cases_count": len(case_service.list_cases()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=True)
