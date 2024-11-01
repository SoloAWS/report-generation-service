from fastapi import APIRouter, Depends, Header, HTTPException
from typing import List, Optional, Dict
import os
import jwt
import httpx
import json
from ..services.redis_service import RedisService
from ..models.dashboard import (
    DashboardStatsResponse,
    CallVolumeData,
    CustomerSatisfactionData,
    IncidentResponse,
    PriorityDistribution,
    ChannelDistribution
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
    """Get key dashboard statistics"""
    cached_stats = RedisService.get_dashboard_stats(current_user['sub'])
    if cached_stats:
        return DashboardStatsResponse(**cached_stats)

    try:
        incidents = await get_recent_incidents(current_user, client)
        stats = calculate_incident_stats(incidents)
        RedisService.cache_dashboard_stats(current_user['sub'], stats, CACHE_EXPIRATION) 
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@router.get("/recent-incidents", response_model=List[IncidentResponse])
async def get_recent_incidents(
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Get list of recent incidents"""
    cached_incidents = RedisService.get_recent_incidents(current_user['sub'])
    if cached_incidents:
        return [IncidentResponse(**incident) for incident in cached_incidents]

    try:
        headers = {"Authorization": f"Bearer {jwt.encode(current_user, SECRET_KEY, algorithm=ALGORITHM)}"}
        response = await client.get(f"{INCIDENT_QUERY_URL}/all-incidents", headers=headers)
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

# Helper functions for calculations
def calculate_incident_stats(incidents: List[IncidentResponse]) -> DashboardStatsResponse:
    """Calculate statistics from incidents data"""
    total = len(incidents)
    states = {"open": 0, "in_progress": 0, "closed": 0, "escalated": 0}
    
    for incident in incidents:
        states[incident.state] += 1
    
    # This would need to be calculated from actual response time data
    avg_response_time = 25.5  # Mock average response time in minutes
    satisfaction_rate = 88.5  # Mock satisfaction rate
    
    return DashboardStatsResponse(
        total_incidents=total,
        open_incidents=states["open"],
        in_progress_incidents=states["in_progress"],
        closed_incidents=states["closed"],
        escalated_incidents=states["escalated"],
        satisfaction_rate=satisfaction_rate,
        average_response_time=avg_response_time
    )

def calculate_priority_distribution(incidents: List[IncidentResponse]) -> PriorityDistribution:
    """Calculate priority distribution from incidents"""
    priorities = {"low": 0, "medium": 0, "high": 0}
    
    for incident in incidents:
        priorities[incident.priority] += 1
    
    return PriorityDistribution(
        low=priorities["low"],
        medium=priorities["medium"],
        high=priorities["high"],
        total=len(incidents)
    )

def calculate_channel_distribution(incidents: List[IncidentResponse]) -> ChannelDistribution:
    """Calculate channel distribution from incidents"""
    channels = {"phone": 0, "email": 0, "chat": 0, "mobile": 0}
    
    for incident in incidents:
        channels[incident.channel] += 1
    
    return ChannelDistribution(
        phone=channels["phone"],
        email=channels["email"],
        chat=channels["chat"],
        mobile=channels["mobile"],
        total=len(incidents)
    )