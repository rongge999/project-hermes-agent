"""Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ProjectCreate(BaseModel):
    topic_id: str = Field(..., description="话题编号如 #001")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    tech_stack: Optional[list[str]] = None
    repo_path: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[list[str]] = None
    repo_path: Optional[str] = None
    status: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    topic_id: str
    name: str
    description: Optional[str] = None
    tech_stack: Optional[list] = None
    repo_path: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    project_id: str
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    source: str = "manual"
    priority: str = "P2"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None


class TaskStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(todo|in_progress|done)$")


class TaskOut(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    source: str
    status: str
    priority: str
    feishu_record_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CapabilityCreate(BaseModel):
    cap_id: str = Field(..., description="CAP-001")
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    call_type: str = "snippet"
    call_definition: Optional[str] = None
    source_project_id: Optional[str] = None


class CapabilityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    call_definition: Optional[str] = None
    status: Optional[str] = None


class CapabilityOut(BaseModel):
    id: str
    cap_id: str
    name: str
    description: Optional[str] = None
    call_type: str
    call_definition: Optional[str] = None
    source_project_id: Optional[str] = None
    status: str
    version: int
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    project_id: Optional[str] = None
    context: Optional[str] = None
    feedback: str = Field(..., pattern="^(useful|useless)$")
