import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.models.classification import TicketClassification

pytestmark = pytest.mark.asyncio

async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("app.api.routes.classify_ticket", new_callable=AsyncMock)
async def test_create_ticket_high_confidence(mock_classify, client: AsyncClient):
    mock_classify.return_value = TicketClassification(
        id=1,
        department="Engineering",
        confidence=0.9,
        reasoning="Clear bug report."
    )
    
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
    assert data["status"] == "routed"
    assert data["department"] == "Engineering"
    assert data["confidence"] == 0.9
    assert data["created_at"] is not None

@patch("app.api.routes.classify_ticket", new_callable=AsyncMock)
async def test_create_ticket_low_confidence(mock_classify, client: AsyncClient):
    mock_classify.return_value = TicketClassification(
        id=2,
        department="Support",
        confidence=0.5,
        reasoning="Ambiguous."
    )
    
    ticket_payload = {
        "title": "Unclear issue",
        "description": "I need help."
    }
    response = await client.post("/tickets", json=ticket_payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == ticket_payload["title"]
    assert data["description"] == ticket_payload["description"]
    assert data["status"] == "pending_review"
    assert data["department"] is None
    assert data["confidence"] == 0.5
    assert data["created_at"] is not None

@patch("app.api.routes.classify_ticket", new_callable=AsyncMock)
async def test_create_ticket_falls_back_when_classification_fails(mock_classify, client: AsyncClient):
    mock_classify.side_effect = Exception("Classification failed")
    
    ticket_payload = {
        "title": "Error-causing ticket",
        "description": "This should fail classification."
    }
    response = await client.post("/tickets", json=ticket_payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == ticket_payload["title"]
    assert data["description"] == ticket_payload["description"]
    assert data["status"] == "pending_review"
    assert data["department"] is None
    assert data["created_at"] is not None
