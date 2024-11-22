import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.routes.health import router
from fastapi import FastAPI

# Setup test app
app = FastAPI()
app.include_router(router)


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@patch("app.services.redis_service.RedisService.health_check", return_value={"status": "healthy", "message": "Redis connection successful"})
def test_health_check_healthy(mock_health_check, client):
    """Test health check endpoint when Redis is healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"
    assert response.json()["components"]["redis"]["status"] == "healthy"
    assert response.json()["components"]["redis"]["message"] == "Redis connection successful"


@patch("app.services.redis_service.RedisService.health_check", return_value={"status": "unhealthy", "message": "Redis connection failed"})
def test_health_check_degraded(mock_health_check, client):
    """Test health check endpoint when Redis is unhealthy."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "Degraded"
    assert response.json()["components"]["redis"]["status"] == "unhealthy"
    assert response.json()["components"]["redis"]["message"] == "Redis connection failed"
