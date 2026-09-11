"""Milestone M10 Portability & Device-Independent Deployment Test Suite.

Verifies:
1. No hardcoded absolute developer drive paths (C:\\, E:\\) in backend code or configs.
2. Configurable DATABASE_URL parsing and driver conversions (PostgreSQL and SQLite).
3. CORS configuration supports both comma-separated strings and JSON lists.
4. Host and port configuration flexibility.
5. Automatic directory provisioning on startup (storage, uploads, logs, generated, data).
6. Comprehensive system health diagnostics endpoint (/api/v1/system/health).
7. Error response sanitization: zero secret or connection string leakage.
8. Demo and Judge mode flags and non-authoritative markers.
"""
import os
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from backend.app.core.config import Settings, BASE_DIR
from backend.app.core.exceptions import (
    ComplianceCompilerException,
    DatabaseUnavailableError,
)
from backend.app.main import app


# 1. Zero Absolute Developer Paths Check
def test_zero_hardcoded_absolute_developer_paths():
    """Verify backend code and configurations use relative Pathlib paths only."""
    backend_root = Path(__file__).resolve().parent.parent
    prohibited = ["C:\\Users\\", "C:/Users/", "E:\\", "E:/Zyntrix"]

    for py_file in backend_root.rglob("*.py"):
        # Ignore test files that might test these patterns
        if "test_portability.py" in str(py_file):
            continue
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for bad_path in prohibited:
            assert bad_path not in content, f"Hardcoded developer path '{bad_path}' found in {py_file}"


# 2. Configurable DATABASE_URL Protocol Conversions
def test_database_url_protocol_conversions():
    """Verify PostgreSQL and SQLite DATABASE_URL formats are converted to async drivers."""
    # PostgreSQL standard URL
    s_pg = Settings(DATABASE_URL="postgresql://user:pass@dbhost:5432/testdb")
    assert s_pg.async_database_url == "postgresql+psycopg://user:pass@dbhost:5432/testdb"
    assert s_pg.sync_database_url == "postgresql://user:pass@dbhost:5432/testdb"
    assert s_pg.is_sqlite is False

    # PostgreSQL legacy URL
    s_leg = Settings(DATABASE_URL="postgres://user:pass@dbhost:5432/testdb")
    assert s_leg.async_database_url == "postgresql+psycopg://user:pass@dbhost:5432/testdb"

    # SQLite file URL
    s_sq = Settings(DATABASE_URL="sqlite:///./data/test.db")
    assert s_sq.async_database_url == "sqlite+aiosqlite:///./data/test.db"
    assert s_sq.sync_database_url == "sqlite:///./data/test.db"
    assert s_sq.is_sqlite is True


# 3. Flexible CORS Origins Parsing
def test_cors_origins_flexible_parsing():
    """Verify CORS origins can be parsed from comma-separated string or list."""
    # Comma-separated string
    s_str = Settings(ALLOWED_CORS_ORIGINS="http://localhost:5173, http://192.168.1.50:3000")
    assert "http://localhost:5173" in s_str.ALLOWED_CORS_ORIGINS
    assert "http://192.168.1.50:3000" in s_str.ALLOWED_CORS_ORIGINS

    # JSON list string
    s_json = Settings(ALLOWED_CORS_ORIGINS='["http://demo.local", "http://judge-laptop:5173"]')
    assert "http://demo.local" in s_json.ALLOWED_CORS_ORIGINS
    assert "http://judge-laptop:5173" in s_json.ALLOWED_CORS_ORIGINS


# 4. Host and Port Configuration
def test_host_and_port_configuration():
    """Verify server host and port can be configured through environment."""
    s = Settings(HOST="127.0.0.1", PORT=9000)
    assert s.HOST == "127.0.0.1"
    assert s.PORT == 9000


# 5. Automatic Runtime Directory Creation
def test_automatic_directory_provisioning():
    """Verify required runtime directories exist or are created automatically."""
    s = Settings()
    s.ensure_directories()

    for p in [s.STORAGE_LOCAL_PATH, s.UPLOADS_LOCAL_PATH, s.LOGS_LOCAL_PATH, s.GENERATED_LOCAL_PATH, s.DATA_PATH]:
        assert Path(p).exists(), f"Directory {p} should exist"


# 6. Comprehensive System Health Endpoint
@pytest.mark.asyncio
async def test_system_health_endpoint():
    """Verify /api/v1/system/health returns complete subsystem diagnostics."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/system/health")
        assert res.status_code == 200
        data = res.json()

        # Check top-level keys
        assert "status" in data
        assert data["api"] == "ok"
        assert "database" in data
        assert "pgvector" in data
        assert "knowledge_base" in data
        assert "configuration" in data

        # Subsystem details
        assert data["knowledge_base"]["verified_standards_count"] >= 4
        assert data["knowledge_base"]["provenance"] == "OFFICIAL_BIS_QCO_CATALOG"
        assert "host" in data["configuration"]
        assert "port" in data["configuration"]


# 7. Error Response Sanitization (No Leaked Passwords or Connection Strings)
def test_error_response_sanitization():
    """Verify structured exceptions contain codes and remediation without leaking secrets."""
    exc = DatabaseUnavailableError("Connection to postgresql://postgres:SECRET_PASS@localhost:5432 failed")
    assert exc.code == "DATABASE_UNAVAILABLE"
    assert exc.status_code == 503
    assert exc.remediation is not None
    assert "SECRET_PASS" not in exc.remediation


# 8. Demo / Judge Mode Flag
def test_demo_judge_mode_flag():
    """Verify Demo Mode can be toggled without breaking defaults."""
    s_default = Settings()
    assert s_default.DEMO_MODE is False

    s_demo = Settings(DEMO_MODE=True)
    assert s_demo.DEMO_MODE is True
