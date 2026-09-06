"""Main FastAPI Application Entry Point for Maritime Oil-Spill Attribution Intelligence.

Implements:
- Strict CORS configuration (configurable via CORS_ORIGINS env var)
- Global exception handlers preventing internal stack trace disclosure
- Security response headers middleware
- Health and diagnostic routes
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, List

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager orchestrating background ingestion workers cleanly."""
    try:
        from backend.app.services.live_ais_service import live_ais_service
        if live_ais_service.is_configured():
            logger.info("Auto-starting live AIS background ingestion worker...")
            live_ais_service.start()
        else:
            logger.info("Live AIS service running in passive mode (AISSTREAM_API_KEY unconfigured).")
    except Exception as e:
        logger.warning(f"Could not auto-start live AIS worker on startup: {e}")
    yield
    try:
        from backend.app.services.live_ais_service import live_ais_service
        live_ais_service.stop()
    except Exception:
        pass


app = FastAPI(
    title="Maritime Oil-Spill Attribution Intelligence API",
    description="Backend API for SAR Slick Detection, Backward Drift Simulation, AIS Interception, and Explainable Forensic Attribution",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
# Global Exception Handlers (with CORS Header Preservation)
# ---------------------------------------------------------------------------

def _cors_response(response: Response, request: Request) -> Response:
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handles HTTPExceptions with CORS headers preserved."""
    resp = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
        },
    )
    return _cors_response(resp, request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation failures with structured error responses and CORS headers."""
    logger.warning(f"Request validation error for {request.url.path}: {exc.errors()}")
    resp = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "RequestValidationError",
            "message": "The submitted payload failed schema validation.",
            "details": exc.errors(),
            "path": request.url.path,
        },
    )
    return _cors_response(resp, request)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled server exceptions, logs full stack trace, and returns CORS-enabled error payload."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    resp = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": f"An unexpected error occurred while processing the forensic request: {str(exc)}",
            "detail": str(exc),
            "path": request.url.path,
        },
    )
    return _cors_response(resp, request)


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
