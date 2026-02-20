"""User model."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, Column, DateTime, String, text
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.daily_plan import DailyPlan


class User(Base):
    """User model representing the users table."""

    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))  # NULL for OAuth-only users
    display_name = Column(String(100), nullable=False)
    google_id = Column(String(255), unique=True)  # NULL for email/password users
    avatar_url = Column(String)
    timezone = Column(String(50), nullable=False, default="UTC")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()"))

    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    daily_plans = relationship("DailyPlan", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship(
        "NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    push_subscriptions = relationship(
        "PushSubscription", back_populates="user", cascade="all, delete-orphan"
    )
    user_patterns = relationship("UserPattern", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"

    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        from app.core.security import verify_password

        return verify_password(password, self.password_hash) if self.password_hash else False