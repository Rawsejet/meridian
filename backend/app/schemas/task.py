"""Task schemas."""
from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class TaskCreate(BaseModel):
    """Request schema for creating a task."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: int = Field(default=2, ge=1, le=4)  # 1=low, 2=medium, 3=high, 4=urgent
    estimated_minutes: Optional[int] = Field(default=None, ge=1)
    energy_level: Optional[int] = Field(default=None, ge=1, le=3)
    category: Optional[str] = None


class TaskUpdate(BaseModel):
    """Request schema for updating a task."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = Field(default=None, ge=1, le=4)
    estimated_minutes: Optional[int] = Field(default=None, ge=1)
    energy_level: Optional[int] = Field(default=None, ge=1, le=3)
    category: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(BaseModel):
    """Response schema for a task."""

    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    priority: int
    estimated_minutes: Optional[int]
    energy_level: Optional[int]
    category: Optional[str]
    status: str
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "user_id")
    def serialize_uuid(self, v: UUID) -> str:
        return str(v)


class TaskListResponse(BaseModel):
    """Response schema for task list."""

    tasks: list[TaskResponse]
    has_more: bool
    next_cursor: Optional[str] = None


class CompleteTaskRequest(BaseModel):
    """Request schema for completing a task."""

    completed_at: Optional[datetime] = None