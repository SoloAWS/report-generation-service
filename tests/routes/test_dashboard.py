import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.routes.dashboard import router
from app.services.redis_service import RedisService
from fastapi import FastAPI

# Setup test app
app = FastAPI()
app.include_router(router)


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@patch("app.routes.dashboard.jwt.decode", return_value={"sub": "user123", "user_type": "company"})
@patch("app.routes.dashboard.RedisService.flush_user_cache", return_value=True)
def test_clear_user_cache(mock_flush_cache, mock_jwt, client):
    """Test clearing the user cache."""
    response = client.delete(
        "/dashboard/cache",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Cache cleared successfully"


@pytest.mark.asyncio
@patch("app.routes.dashboard.jwt.decode", return_value={"sub": "user123", "user_type": "company"})
@patch("app.routes.dashboard.RedisService.get_satisfaction_data", return_value=None)
@patch("app.routes.dashboard.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_get_customer_satisfaction(mock_http_get, mock_redis, mock_jwt, client):
    """Test the customer satisfaction endpoint."""
    response = client.get(
        "/dashboard/satisfaction",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 200
    assert "labels" in response.json()


@patch("app.routes.dashboard.jwt.decode", return_value={"sub": "user123", "user_type": "user"})
def test_get_recent_incidents_forbidden(mock_jwt, client):
    """Test recent incidents endpoint for non-company user."""
    response = client.get(
        "/dashboard/recent-incidents",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Only company users can access this endpoint"

@pytest.mark.asyncio
@patch("app.routes.dashboard.jwt.decode", return_value={"sub": "user123", "user_type": "company"})
@patch("app.routes.dashboard.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_call_volume_service_error(mock_http_get, mock_jwt, client):
    """Test call volume endpoint with a service error."""
    mock_http_get.return_value.status_code = 500
    mock_http_get.return_value.text = "Service Error"

    response = client.get(
        "/dashboard/call-volume",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 500
    assert "Error from incident service" in response.json()["detail"]


@patch("app.routes.dashboard.jwt.decode", return_value={"sub": "user123", "user_type": "company"})
@patch("app.routes.dashboard.RedisService.flush_user_cache", return_value=False)
def test_clear_user_cache_failure(mock_flush_cache, mock_jwt, client):
    """Test clearing the user cache when Redis service fails."""
    response = client.delete(
        "/dashboard/cache",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to clear cache"


@pytest.mark.asyncio
@patch("app.routes.dashboard.jwt.decode", return_value={"sub": "user123", "user_type": "company"})
@patch("app.routes.dashboard.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_get_dashboard_stats_http_error(mock_http_get, mock_jwt, client):
    """Test dashboard stats endpoint with an HTTP error."""
    mock_http_get.return_value.status_code = 500
    mock_http_get.return_value.text = "Internal Server Error"

    response = client.get(
        "/dashboard/stats",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 500
    assert "Error fetching dashboard stats" in response.json()["detail"]


@patch("app.routes.dashboard.jwt.decode", return_value={"sub": "user123", "user_type": "company"})
@patch("app.routes.dashboard.RedisService.get_satisfaction_data", return_value=None)
def test_get_customer_satisfaction_cache_miss(mock_redis, mock_jwt, client):
    """Test the customer satisfaction endpoint when cache misses."""
    response = client.get(
        "/dashboard/satisfaction",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 200
    assert "labels" in response.json()
    assert response.json()["average_score"] == 86.8


@patch("app.routes.dashboard.jwt.decode", return_value={"sub": "user123", "user_type": "company"})
def test_clear_user_cache_success(mock_jwt, client):
    """Test clearing the user cache when successful."""
    with patch("app.routes.dashboard.RedisService.flush_user_cache", return_value=True):
        response = client.delete(
            "/dashboard/cache",
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Cache cleared successfully"

