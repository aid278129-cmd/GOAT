import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.security import generate_secure_storage_filename, sanitize_sensitive_data


def test_secure_filename_generation():
    orig = "my_confidential_design_drawing.pdf"
    secure = generate_secure_storage_filename(orig)
    assert secure.endswith(".pdf")
    assert "my_confidential_design" not in secure
    assert len(secure) > 32


def test_sanitize_sensitive_payload():
    payload = {
        "product_name": "Smart Water Bottle",
        "api_key": "sk-top-secret-12345",
        "secret_token": "bearer xyz",
        "specs": {
            "capacity": 500,
            "password_hash": "hash123",
        },
    }
    sanitized = sanitize_sensitive_data(payload)
    assert sanitized["product_name"] == "Smart Water Bottle"
    assert sanitized["api_key"] == "********"
    assert sanitized["secret_token"] == "********"
    assert sanitized["specs"]["password_hash"] == "********"
    assert sanitized["specs"]["capacity"] == 500


@pytest.mark.asyncio
async def test_request_id_header_middleware():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health", headers={"X-Request-ID": "test-req-id-12345"})
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == "test-req-id-12345"
        assert "X-Response-Time-MS" in response.headers
