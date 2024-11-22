import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.services.redis_service.RedisService.health_check", return_value={"status": "healthy", "message": "Redis is healthy"})
def test_app_startup(mock_redis_health):
    """Simple test to cover application startup."""
    response = client.get("/report-generation/health")
    assert response.status_code == 200


@patch("app.routes.dashboard.jwt.decode", return_value={"sub": "user123", "user_type": "company"})
def test_validation_exception_handler(mock_jwt):
    """Simple test to cover validation exception."""
    response = client.get("/report-generation/dashboard/stats", headers={})
    assert response.status_code == 401  # No Authorization header
