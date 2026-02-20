"""Intelligence layer schemas."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class TaskParseRequest(BaseModel):
    """Request schema for natural language task parsing."""

    text: str = Field(..., min_length=1)
    timezone: str = Field(default="UTC")
    today: str = Field(default_factory=lambda: datetime.utcnow().date().isoformat())


class TaskParseResponse(BaseModel):
    """Response schema for parsed task."""

    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: int = 2
    estimated_minutes: Optional[int] = None
    energy_level: Optional[int] = None
    category: Optional[str] = None


class SuggestionRequest(BaseModel):
    """Request schema for task ordering suggestions."""

    task_ids: List[str]
    user_timezone: str = "UTC"
    today: str = Field(default_factory=lambda: datetime.utcnow().date().isoformat())


class SuggestionReason(BaseModel):
    """Reason for a task ordering suggestion."""

    task_id: str
    reason: str


class SuggestionWarning(BaseModel):
    """Warning about a task ordering suggestion."""

    task_id: str
    message: str


class SuggestionResponse(BaseModel):
    """Response schema for task ordering suggestions."""

    task_order: List[str]
    reasoning: List[SuggestionReason]
    warnings: List[SuggestionWarning]


class InsightResponse(BaseModel):
    """Response schema for weekly insights."""

    period_start: datetime
    period_end: datetime
    total_tasks_completed: int
    average_completion_rate: float
    most_completed_category: Optional[str]
    peak_completion_hour: int
    average_estimation_accuracy: Optional[float]