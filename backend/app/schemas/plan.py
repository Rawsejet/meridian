"""Daily plan schemas."""
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field


class DailyPlanCreate(BaseModel):
    """Request schema for creating/updating a daily plan."""

    task_order: list[str] = Field(default=[])  # list of task IDs
    notes: Optional[str] = None
    mood: Optional[int] = Field(default=None, ge=1, le=5)


class DailyPlanUpdate(BaseModel):
    """Request schema for updating a daily plan."""

    task_order: Optional[list[str]] = Field(default=None)
    notes: Optional[str] = None
    mood: Optional[int] = Field(default=None, ge=1, le=5)


class DailyPlanResponse(BaseModel):
    """Response schema for a daily plan."""

    id: str
    user_id: str
    plan_date: date
    task_order: list[str]  # list of task IDs
    notes: Optional[str]
    mood: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DailyPlanListResponse(BaseModel):
    """Response schema for daily plan list."""

    plans: List[DailyPlanResponse]


class ReorderTasksRequest(BaseModel):
    """Request schema for reordering tasks in a plan."""

    task_order: list[str] = Field(..., min_length=1)


class CompletePlanRequest(BaseModel):
    """Request schema for completing a daily plan."""

    task_completions: dict[str, bool] = Field(
        ..., description="Map of task_id -> completed status"
    )
    notes: Optional[str] = None
    mood: Optional[int] = Field(default=None, ge=1, le=5)


class ReflectionResponse(BaseModel):
    """Response schema for daily plan reflection/stats."""

    plan_date: date
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    total_planned_minutes: Optional[int]
    total_actual_minutes: Optional[int]
    mood: Optional[int]