from redis import Redis
from typing import Optional, Any, Dict, List
import json
import os
from datetime import datetime
from ..errors.errors import ApiError
from ..models.dashboard import (
    DashboardStatsResponse,
    CallVolumeData,
    CustomerSatisfactionData,
    IncidentResponse
)

class RedisService:
    _instance: Optional[Redis] = None
    
    @classmethod
    def get_instance(cls) -> Redis:
        """
        Get or create Redis connection instance using singleton pattern
        """
        if cls._instance is None:
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                raise ApiError(500, "REDIS_URL environment variable is not set")
            
            try:
                cls._instance = Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=5
                )
            except Exception as e:
                raise ApiError(500, f"Failed to connect to Redis: {str(e)}")
                
        return cls._instance

    @classmethod
    def set_json(cls, key: str, value: Any, expiration: int = 300) -> bool:
        """
        Store JSON serializable data in Redis with expiration
        """
        try:
            redis = cls.get_instance()
            return redis.setex(
                key,
                expiration,
                json.dumps(value, default=str)
            )
        except Exception as e:
            print(f"Redis set error: {str(e)}")
            return False

    @classmethod
    def get_json(cls, key: str) -> Optional[Any]:
        """
        Retrieve and deserialize JSON data from Redis
        """
        try:
            redis = cls.get_instance()
            data = redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Redis get error: {str(e)}")
            return None

    @classmethod
    def cache_dashboard_stats(cls, user_id: str, stats: DashboardStatsResponse, expiration: int) -> bool:
        """
        Cache dashboard stats for a specific user
        """
        key = f"dashboard:stats:{user_id}"
        return cls.set_json(key, stats.dict(), expiration)

    @classmethod
    def get_dashboard_stats(cls, user_id: str) -> Optional[Dict]:
        """
        Retrieve cached dashboard stats for a specific user
        """
        key = f"dashboard:stats:{user_id}"
        return cls.get_json(key)

    @classmethod
    def cache_recent_incidents(cls, user_id: str, incidents: List[IncidentResponse], expiration: int) -> bool:
        """
        Cache recent incidents for a specific user
        """
        key = f"dashboard:incidents:{user_id}"
        incident_data = [incident.dict() for incident in incidents]
        return cls.set_json(key, incident_data, expiration)

    @classmethod
    def get_recent_incidents(cls, user_id: str) -> Optional[List[Dict]]:
        """
        Retrieve cached recent incidents for a specific user
        """
        key = f"dashboard:incidents:{user_id}"
        return cls.get_json(key)

    @classmethod
    def cache_call_volume(cls, user_id: str, call_volume: CallVolumeData, expiration: int) -> bool:
        """
        Cache call volume data for a specific user
        """
        key = f"dashboard:call_volume:{user_id}"
        return cls.set_json(key, call_volume.dict(), expiration)

    @classmethod
    def get_call_volume(cls, user_id: str) -> Optional[Dict]:
        """
        Retrieve cached call volume data for a specific user
        """
        key = f"dashboard:call_volume:{user_id}"
        return cls.get_json(key)

    @classmethod
    def cache_satisfaction_data(cls, user_id: str, satisfaction: CustomerSatisfactionData, expiration: int) -> bool:
        """
        Cache satisfaction data for a specific user
        """
        key = f"dashboard:satisfaction:{user_id}"
        return cls.set_json(key, satisfaction.dict(), expiration)

    @classmethod
    def get_satisfaction_data(cls, user_id: str) -> Optional[Dict]:
        """
        Retrieve cached satisfaction data for a specific user
        """
        key = f"dashboard:satisfaction:{user_id}"
        return cls.get_json(key)

    @classmethod
    def flush_user_cache(cls, user_id: str) -> bool:
        """
        Clear all cached data for a specific user
        """
        try:
            redis = cls.get_instance()
            pattern = f"dashboard:*:{user_id}"
            keys = redis.keys(pattern)
            if keys:
                redis.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis flush error: {str(e)}")
            return False

    @classmethod
    def health_check(cls) -> dict:
        """
        Check Redis connection health
        """
        try:
            redis = cls.get_instance()
            redis.ping()
            return {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e)
            }