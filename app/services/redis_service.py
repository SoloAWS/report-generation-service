from redis import Redis
from typing import Optional
import os
from ..errors.errors import ApiError

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