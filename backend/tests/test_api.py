
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas import PriceTick


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_invalid_price_tick_rejected():
    with pytest.raises(ValidationError):
        PriceTick(
            ticker="AAPL",
            price=-10.0,
            timestamp="2026-10-23T10:00:00Z",
            sent_at_ms=1729780321004,
        )
