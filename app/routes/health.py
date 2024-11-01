from fastapi import APIRouter
from ..services.redis_service import RedisService

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    """
    Comprehensive health check endpoint that checks all system components
    """
    redis_health = RedisService.health_check()
    
    return {
        "service": "Report Generation",
        "status": "OK" if redis_health["status"] == "healthy" else "Degraded",
        "components": {
            "api": {
                "status": "OK",
                "message": "API is responding"
            },
            "redis": {
                "status": redis_health["status"],
                "message": redis_health["message"]
            }
        },
        "version": "1.0"
    }