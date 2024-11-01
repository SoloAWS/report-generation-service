from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class IncidentState(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    ESCALATED = "escalated"

class IncidentPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class IncidentChannel(str, Enum):
    PHONE = "phone"
    EMAIL = "email"
    CHAT = "chat"
    MOBILE = "mobile"

class IncidentResponse(BaseModel):
    id: UUID
    description: str
    state: IncidentState
    channel: IncidentChannel
    priority: IncidentPriority
    creation_date: datetime
    user_id: UUID
    company_id: UUID
    company_name: Optional[str] = None
    manager_id: Optional[UUID] = None

class DashboardStatsResponse(BaseModel):
    totalCalls: int
    averageHandlingTime: int
    customerSatisfaction: int
    openTickets: int

class TimeSeriesData(BaseModel):
    timestamp: datetime
    value: float

class CallVolumeData(BaseModel):
    labels: List[str]  # Time periods (e.g., days, hours)
    values: List[int]  # Number of calls
    trend: List[TimeSeriesData]
    total_calls: int
    peak_hour: str
    lowest_hour: str

class CustomerSatisfactionData(BaseModel):
    labels: List[str]  # Time periods
    values: List[float]  # Satisfaction scores
    trend: List[TimeSeriesData]
    average_score: float
    total_responses: int
    positive_feedback_percentage: float


class CallVolumeDataset(BaseModel):
    label: str
    data: List[int]
    backgroundColor: str

class CallVolumeResponse(BaseModel):
    labels: List[str]
    datasets: List[CallVolumeDataset]