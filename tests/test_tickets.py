import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

async def test_create_ticket(client: AsyncClient):
    ticket_payload = {
        "title": "Bug on checkout",
        "description": "I am trying to complete my purchase but the pay button does not work."
    }
    response = await client.post("/tickets", json=ticket_payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == ticket_payload["title"]
    assert data["description"] == ticket_payload["description"]
    assert data["status"] == "received"
    assert data["created_at"] is not None
