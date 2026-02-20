"""Notification preference and push subscription models."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, Column, DateTime, String, Text, ForeignKey, Time, text
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class NotificationPreference(Base):
    """Notification preference model representing the notification_preferences table."""

    __tablename__ = "notification_preferences"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    morning_briefing_enabled = Column(Boolean, nullable=False, default=True)
    morning_briefing_time = Column(Time, nullable=False, default="08:00")
    midday_nudge_enabled = Column(Boolean, nullable=False, default=True)
    midday_nudge_time = Column(Time, nullable=False, default="12:00")
    evening_reflection_enabled = Column(Boolean, nullable=False, default=True)
    evening_reflection_time = Column(Time, nullable=False, default="20:00")
    email_notifications = Column(Boolean, nullable=False, default=True)
    push_notifications = Column(Boolean, nullable=False, default=True)
    quiet_hours_start = Column(Time)
    quiet_hours_end = Column(Time)

    # Relationships
    user = relationship("User", back_populates="notification_preferences")
    push_subscriptions = relationship("PushSubscription", back_populates="notification_preference")

    def __repr__(self) -> str:
        return f"<NotificationPreference(id={self.id}, user_id={self.user_id})>"


class PushSubscription(Base):
    """Push subscription model representing the push_subscriptions table."""

    __tablename__ = "push_subscriptions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    notification_preference_id = Column(UUID, ForeignKey("notification_preferences.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(Text, nullable=False)
    p256dh_key = Column(Text, nullable=False)
    auth_key = Column(Text, nullable=False)
    user_agent = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()"))

    # Relationships
    user = relationship("User", back_populates="push_subscriptions")
    notification_preference = relationship("NotificationPreference", back_populates="push_subscriptions")

    def __repr__(self) -> str:
        return f"<PushSubscription(id={self.id}, user_id={self.user_id}, endpoint='{self.endpoint[:50]}...')>"