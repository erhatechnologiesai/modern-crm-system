from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Auth Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: Optional[str] = "sales_rep"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: int
    created_at: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Company Schemas
class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    industry: Optional[str] = None
    website: Optional[str] = None
    size: Optional[str] = None
    annual_revenue: Optional[float] = 0.0
    city: Optional[str] = None
    country: Optional[str] = None

class CompanyResponse(CompanyCreate):
    id: int
    created_at: Optional[str] = None

# Contact Schemas
class ContactCreate(BaseModel):
    company_id: Optional[int] = None
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    phone: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = "lead"
    lead_source: Optional[str] = None

class ContactResponse(ContactCreate):
    id: int
    created_at: Optional[str] = None
    company_name: Optional[str] = None

# Lead Schemas
class LeadCreate(BaseModel):
    title: str = Field(..., min_length=1)
    contact_id: Optional[int] = None
    company_id: Optional[int] = None
    value: Optional[float] = 0.0
    status: Optional[str] = "new"
    source: Optional[str] = None
    notes: Optional[str] = None

class LeadResponse(LeadCreate):
    id: int
    created_at: Optional[str] = None
    contact_name: Optional[str] = None
    company_name: Optional[str] = None

# Deal Schemas
class DealCreate(BaseModel):
    title: str = Field(..., min_length=1)
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    amount: float = Field(..., ge=0)
    stage: Optional[str] = "prospect"
    probability: Optional[int] = 20
    expected_close_date: Optional[str] = None

class DealResponse(DealCreate):
    id: int
    created_at: Optional[str] = None
    company_name: Optional[str] = None
    contact_name: Optional[str] = None

# Task Schemas
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "pending"
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None

class TaskResponse(TaskCreate):
    id: int
    created_at: Optional[str] = None

# Note Schemas
class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1)
    entity_type: str
    entity_id: int

class NoteResponse(NoteCreate):
    id: int
    author_id: Optional[int] = None
    created_at: Optional[str] = None

# Activity Log Schema
class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    created_at: Optional[str] = None

# Analytics Summary Schema
class DashboardMetrics(BaseModel):
    total_revenue_won: float
    pipeline_total_value: float
    total_contacts: int
    total_companies: int
    total_deals: int
    total_leads: int
    active_tasks: int
    deals_by_stage: dict
    recent_activities: List[ActivityLogResponse]
