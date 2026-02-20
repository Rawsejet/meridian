"""Task model."""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, JSON, SmallInteger, Boolean, Column, DateTime, String, Text, ForeignKey, Index, text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.daily_plan import TaskCompletion


class Priority(Enum):
    """Task priority levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """Task status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(Base):
    """Task model representing the tasks table."""

    __tablename__ = "tasks"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime(timezone=True))
    priority = Column(SmallInteger, nullable=False, default=Priority.MEDIUM.value)
    estimated_minutes = Column(Integer)
    energy_level = Column(SmallInteger)  # 1=low, 2=medium, 3=high
    category = Column(String(100))
    status = Column(String(20), nullable=False, default=TaskStatus.PENDING.value)
    recurring_rule = Column(JSONB)  # iCal RRULE or null
    completed_at = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    # Indexes
    __table_args__ = (
        Index("ix_tasks_user_id", "user_id"),
        Index("ix_tasks_due_date_status", "due_date", "status"),
        Index("ix_tasks_priority", "priority"),
    )

    # Relationships
    user = relationship("User", back_populates="tasks")
    task_completions = relationship("TaskCompletion", back_populates="task")

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"