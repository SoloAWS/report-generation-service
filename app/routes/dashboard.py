from fastapi import APIRouter, Depends, Header, HTTPException
from typing import List
import os
import jwt
import httpx
from ..services.redis_service import RedisService
from ..models.dashboard import (
    DashboardStatsResponse,
    CallVolumeData,
    CustomerSatisfactionData,
    IncidentResponse
)

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

# Environment variables
INCIDENT_QUERY_URL = os.getenv("INCIDENT_QUERY_URL", "http://localhost:8006/incident-query")
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'secret_key')
ALGORITHM = "HS256"
CACHE_EXPIRATION = int(os.getenv('CACHE_EXPIRATION_SECONDS', 300))  # 5 minutes default

# Create a shared httpx client for reuse
async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client

def get_current_user(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        token = authorization.replace('Bearer ', '') if authorization.startswith('Bearer ') else authorization
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Get dashboard statistics"""
    try:
        headers = {"Authorization": f"Bearer {jwt.encode(current_user, SECRET_KEY, algorithm=ALGORITHM)}"}
        response = await client.get(f"{INCIDENT_QUERY_URL}/dashboard-stats", headers=headers)
        response.raise_for_status()
        
        stats = response.json()
        
        return DashboardStatsResponse(
            totalCalls=stats['total_calls'],
            averageHandlingTime=0,
            customerSatisfaction=0,
            openTickets=stats['open_tickets']
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

@router.get("/recent-incidents", response_model=List[IncidentResponse])
async def get_recent_incidents(
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Get list of recent incidents for company users only"""
    if current_user.get('user_type') != 'company':
        raise HTTPException(
            status_code=403,
            detail="Only company users can access this endpoint"
        )

    cached_incidents = RedisService.get_recent_incidents(current_user['sub'])
    if cached_incidents:
        return [IncidentResponse(**incident) for incident in cached_incidents]

    try:
        headers = {"Authorization": f"Bearer {jwt.encode(current_user, SECRET_KEY, algorithm=ALGORITHM)}"}
        response = await client.get(f"{INCIDENT_QUERY_URL}/company-incidents", headers=headers)
        response.raise_for_status()
        
        incidents_data = response.json()
        incidents = [IncidentResponse(**incident) for incident in incidents_data]
        RedisService.cache_recent_incidents(current_user['sub'], incidents, CACHE_EXPIRATION) 
        return incidents
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to incident service: {str(e)}")

@router.get("/call-volume", response_model=CallVolumeData)
async def get_call_volume_data(
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Get call volume trends"""
    cached_data = RedisService.get_call_volume(current_user['sub'])
    if cached_data:
        return CallVolumeData(**cached_data)

    try:
        # Mock data for now
        data = CallVolumeData(
            labels=["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
            values=[10, 5, 35, 45, 40, 20],
            trend=[],
            total_calls=155,
            peak_hour="12:00",
            lowest_hour="04:00"
        )
        RedisService.cache_call_volume(current_user['sub'], data, CACHE_EXPIRATION) 
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching call volume data: {str(e)}")

@router.get("/satisfaction", response_model=CustomerSatisfactionData)
async def get_customer_satisfaction_data(
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Get customer satisfaction metrics"""
    cached_data = RedisService.get_satisfaction_data(current_user['sub'])
    if cached_data:
        return CustomerSatisfactionData(**cached_data)

    try:
        # Mock data for now
        data = CustomerSatisfactionData(
            labels=["Mon", "Tue", "Wed", "Thu", "Fri"],
            values=[85, 88, 82, 89, 90],
            trend=[],
            average_score=86.8,
            total_responses=500,
            positive_feedback_percentage=88.5
        )
        RedisService.cache_satisfaction_data(current_user['sub'], data, CACHE_EXPIRATION) 
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching satisfaction data: {str(e)}")

@router.delete("/cache")
async def clear_user_cache(
    current_user: dict = Depends(get_current_user)
):
    """Clear all cached dashboard data for the current user"""
    success = RedisService.flush_user_cache(current_user['sub'])
    if success:
        return {"message": "Cache cleared successfully"}
    raise HTTPException(status_code=500, detail="Failed to clear cache")
