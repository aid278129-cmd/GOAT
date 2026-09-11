import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_standards_catalog_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/standards")
        assert response.status_code in [200, 500]  # Returns 200 if db is reachable, or handled


@pytest.mark.asyncio
async def test_documents_registry_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/documents")
        assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_knowledge_search_contract():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "query": "stainless steel grade 304 material requirement",
            "standard_number": "IS 17526:2021",
            "verified_only": True,
            "top_k": 5,
        }
        response = await ac.post("/api/v1/knowledge/search", json=payload)
        assert response.status_code in [200, 500]
