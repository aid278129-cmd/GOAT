import sys
import asyncio

if sys.platform == "win32" and sys.version_info < (3, 14):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import logger, RequestLoggingMiddleware
from backend.app.core.exceptions import (
    ComplianceCompilerException,
    compliance_exception_handler,
    global_exception_handler,
)
from backend.app.api.health import router as health_router
from backend.app.api import api_router
from backend.app.database.postgres import init_db_extensions
from backend.app.database.session import create_tables_if_needed


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} (Team: {settings.PROJECT_TEAM}) v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT} | SIH Problem: {settings.SIH_PROBLEM_ID}")
    logger.info(f"Host: {settings.HOST}:{settings.PORT} | Demo Mode: {settings.DEMO_MODE}")

    # Attempt PostgreSQL extensions initialization & schema creation
    await init_db_extensions()
    await create_tables_if_needed()

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="BIS Compliance Compiler - AI-powered Intelligent Assistant for Indian Standards & Compliance Intelligence (SIH 26107)",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Exception handlers
app.add_exception_handler(ComplianceCompilerException, compliance_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Custom logging & request ID middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health checks (/health, /health/db, /health/vector)
app.include_router(health_router)

# Versioned API routes (/api/v1/... and /api/...)
app.include_router(api_router, prefix=settings.API_V1_STR)
if settings.API_V1_STR != "/api":
    app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "team": settings.PROJECT_TEAM,
        "sih_problem": settings.SIH_PROBLEM_ID,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "status": "operational",
    }
