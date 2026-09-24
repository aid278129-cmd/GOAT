import pytest
import sys
import os
import asyncio
from pathlib import Path
from httpx import AsyncClient, ASGITransport

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# Ensure repository root is in sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Set test environment database defaults to prevent TCP socket hangs when PostgreSQL is not running locally
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{repo_root}/data/goat.db")
os.environ.setdefault("DEV_FALLBACK_SQLITE", "true")

from backend.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
