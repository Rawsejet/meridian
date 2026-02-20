"""Notification schemas."""
from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, Field


class NotificationPreferenceCreate(BaseModel):
    """Request schema for notification preferences."""

    morning_briefing_enabled: bool = Field(default=True)
    morning_briefing_time: time = Field(default=time(8, 0))
    midday_nudge_enabled: bool = Field(default=True)
    midday_nudge_time: time = Field(default=time(12, 0))
    evening_reflection_enabled: bool = Field(default=True)
    evening_reflection_time: time = Field(default=time(20, 0))
    email_notifications: bool = Field(default=True)
    push_notifications: bool = Field(default=True)
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None


class NotificationPreferenceResponse(BaseModel):
    """Response schema for notification preferences."""

    id: str
    user_id: str
    morning_briefing_enabled: bool
    morning_briefing_time: time
    midday_nudge_enabled: bool
    midday_nudge_time: time
    evening_reflection_enabled: bool
    evening_reflection_time: time
    email_notifications: bool
    push_notifications: bool
    quiet_hours_start: Optional[time]
    quiet_hours_end: Optional[time]

    model_config = {"from_attributes": True}


class PushSubscriptionCreate(BaseModel):
    """Request schema for push subscription."""

    endpoint: str = Field(..., min_length=1)
    p256dh_key: str = Field(..., min_length=1)
    auth_key: str = Field(..., min_length=1)
    user_agent: Optional[str] = None


class PushSubscriptionResponse(BaseModel):
    """Response schema for push subscription."""

    id: str
    user_id: str
    endpoint: str
    created_at: datetime

    model_config = {"from_attributes": True}