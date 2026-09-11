import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["project"] == "BIS Compliance Compiler"
        assert data["team"] == "Zyntrix"
        assert data["sih_problem"] == "26107"


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert data["services"]["api"] == "ok"
        assert "database" in data["services"]
        assert "vector_store" in data["services"]


@pytest.mark.asyncio
async def test_system_info_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/system/info")
        assert response.status_code == 200
        data = response.json()
        assert data["milestone"] == "M0 - Engineering Foundation"
        assert "active_modules" in data
        assert data["active_modules"]["api_gateway"] == "READY"
        assert data["active_modules"]["database_orm"] == "READY"
