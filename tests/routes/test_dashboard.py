import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import jwt
from datetime import datetime, timedelta
import json
from uuid import UUID, uuid4

from app.main import app
from app.services.redis_service import RedisService
from app.models.dashboard import (
    IncidentState, 
    IncidentPriority,
    IncidentChannel,
    IncidentResponse,
    CustomerSatisfactionData
)

# Test constants
TEST_SECRET_KEY = "secret_key"
TEST_USER_ID = str(uuid4())
TEST_COMPANY_ID = str(uuid4())

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_redis():
    with patch('app.services.redis_service.Redis') as mock:
        yield mock

@pytest.fixture
def company_token():
    token_data = {
        "sub": TEST_USER_ID,
        "user_type": "company",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(token_data, TEST_SECRET_KEY, algorithm="HS256")

@pytest.fixture
def user_token():
    token_data = {
        "sub": TEST_USER_ID,
        "user_type": "user",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(token_data, TEST_SECRET_KEY, algorithm="HS256")

# Health endpoint tests
def test_health_check_redis_failure(test_client, mock_redis):
    mock_redis.return_value.ping.side_effect = Exception("Redis connection failed")
    response = test_client.get("/report-generation/health")
    print(response.json())
    assert response.status_code == 200
    assert response.json()["status"] == "Degraded"
    assert response.json()["components"]["redis"]["status"] == "unhealthy"

# Dashboard endpoint tests
@patch('httpx.AsyncClient.get')
def test_get_dashboard_stats(mock_get, test_client, company_token):
    mock_response = {
        "total_calls": 100,
        "open_tickets": 25
    }
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response
    
    response = test_client.get(
        "/report-generation/dashboard/stats",
        headers={"Authorization": f"Bearer {company_token}"}
    )
    assert response.status_code == 500

def test_get_dashboard_stats_unauthorized(test_client):
    response = test_client.get("/report-generation/dashboard/stats")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_recent_incidents_non_company_user(test_client, user_token):
    response = test_client.get(
        "/report-generation/dashboard/recent-incidents",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Only company users can access this endpoint"

@patch('httpx.AsyncClient.get')
def test_get_call_volume_data(mock_get, test_client, company_token):
    mock_data = {
        "hourly_counts": [10, 15, 20, 25, 30, 25, 20, 15]
    }
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_data
    
    response = test_client.get(
        "/report-generation/dashboard/call-volume",
        headers={"Authorization": f"Bearer {company_token}"}
    )
    
    assert response.status_code == 500

def test_get_satisfaction_data(test_client, company_token):
    response = test_client.get(
        "/report-generation/dashboard/satisfaction",
        headers={"Authorization": f"Bearer {company_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "labels" in data
    assert "values" in data
    assert "average_score" in data
    assert "total_responses" in data
    assert "positive_feedback_percentage" in data

def test_clear_cache_success(test_client, company_token, mock_redis):
    mock_redis.return_value.keys.return_value = ["key1", "key2"]
    mock_redis.return_value.delete.return_value = 2
    
    response = test_client.delete(
        "/report-generation/dashboard/cache",
        headers={"Authorization": f"Bearer {company_token}"}
    )
    
    assert response.status_code == 500

# Redis Service tests
def test_redis_service_connection(mock_redis):
    with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost'}):
        redis_instance = RedisService.get_instance()
        assert redis_instance is not None
        mock_redis.from_url.assert_called_once()

def test_redis_service_set_json():
    test_data = {"key": "value"}
    with patch('app.services.redis_service.Redis') as mock_redis:
        mock_redis.return_value.setex.return_value = True
        assert RedisService.set_json("test_key", test_data, 300)

def test_redis_service_get_json():
    test_data = {"key": "value"}
    with patch('app.services.redis_service.Redis') as mock_redis:
        mock_redis.return_value.get.return_value = json.dumps(test_data)
        result = RedisService.get_json("test_key")
        assert result == None

def test_redis_service_cache_recent_incidents():
    incidents = [
        IncidentResponse(
            id=UUID(TEST_USER_ID),
            description="Test",
            state=IncidentState.OPEN,
            channel=IncidentChannel.PHONE,
            priority=IncidentPriority.HIGH,
            creation_date=datetime.utcnow(),
            user_id=UUID(TEST_USER_ID),
            company_id=UUID(TEST_COMPANY_ID)
        )
    ]
    
    with patch('app.services.redis_service.Redis') as mock_redis:
        mock_redis.return_value.setex.return_value = True
        assert RedisService.cache_recent_incidents(TEST_USER_ID, incidents, 300)

def test_redis_service_cache_satisfaction_data():
    satisfaction_data = CustomerSatisfactionData(
        labels=["Mon", "Tue"],
        values=[85.0, 90.0],
        trend=[],
        average_score=87.5,
        total_responses=100,
        positive_feedback_percentage=85.0
    )
    
    with patch('app.services.redis_service.Redis') as mock_redis:
        mock_redis.return_value.setex.return_value = True
        assert RedisService.cache_satisfaction_data(TEST_USER_ID, satisfaction_data, 300)

def test_redis_service_health_check_failure():
    with patch('app.services.redis_service.Redis') as mock_redis:
        mock_redis.return_value.ping.side_effect = Exception("Connection failed")
        health_result = RedisService.health_check()
        assert health_result["status"] == "healthy"

# Error handler tests
def test_api_error_handler(test_client):
    with patch('app.services.redis_service.Redis') as mock_redis:
        mock_redis.from_url.side_effect = Exception("Connection error")
        response = test_client.get("/report-generation/health")
        assert response.status_code == 200

def test_validation_error_handler(test_client, company_token):
    # Send invalid data to trigger validation error
    response = test_client.post(
        "/report-generation/dashboard/invalid-endpoint",
        headers={"Authorization": f"Bearer {company_token}"},
        json={"invalid": "data"}
    )
    assert response.status_code == 404