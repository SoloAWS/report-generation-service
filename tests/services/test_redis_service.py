import pytest
from unittest.mock import patch, MagicMock
from app.services.redis_service import RedisService


@patch('os.getenv', return_value="redis://localhost:6379")
@patch('app.services.redis_service.Redis.from_url')
def test_get_instance(mock_redis_from_url, mock_getenv):
    """Simple test to cover get_instance."""
    mock_redis_from_url.return_value = MagicMock()
    instance = RedisService.get_instance()
    assert instance is not None


@patch('app.services.redis_service.Redis.from_url')
def test_set_json(mock_redis_from_url):
    """Simple test to cover set_json."""
    mock_redis_instance = MagicMock()
    mock_redis_from_url.return_value = mock_redis_instance
    result = RedisService.set_json("test_key", {"key": "value"})
    assert result is not None


@patch('app.services.redis_service.Redis.from_url')
def test_health_check(mock_redis_from_url):
    """Simple test to cover health_check."""
    mock_redis_instance = MagicMock()
    mock_redis_instance.ping.return_value = True
    mock_redis_from_url.return_value = mock_redis_instance
    result = RedisService.health_check()
    assert result["status"] == "healthy"
