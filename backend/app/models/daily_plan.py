"""Daily plan and task completion models."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, SmallInteger, Boolean, Column, DateTime, String, ForeignKey, UniqueConstraint, ARRAY, text, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class DailyPlan(Base):
    """Daily plan model representing the daily_plans table."""

    __tablename__ = "daily_plans"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_date = Column(DateTime, nullable=False)
    task_order = Column(ARRAY(PGUUID), nullable=False, default=[])  # ordered array of task IDs
    notes = Column(String)
    mood = Column(SmallInteger)  # 1-5 scale

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()"))

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "plan_date", name="uq_daily_plan_user_date"),
    )

    # Relationships
    user = relationship("User", back_populates="daily_plans")
    task_completions = relationship("TaskCompletion", back_populates="daily_plan")

    def __repr__(self) -> str:
        return f"<DailyPlan(id={self.id}, user_id={self.user_id}, plan_date='{self.plan_date}')>"


class TaskCompletion(Base):
    """Task completion model representing the task_completions table."""

    __tablename__ = "task_completions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    task_id = Column(UUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    daily_plan_id = Column(UUID, ForeignKey("daily_plans.id", ondelete="CASCADE"), nullable=False)
    planned_position = Column(SmallInteger, nullable=False)
    actual_completed = Column(Boolean, nullable=False, default=False)
    actual_minutes = Column(Integer)
    completed_at = Column(DateTime)
    skipped_reason = Column(String(255))

    # Relationships
    task = relationship("Task", back_populates="task_completions")
    daily_plan = relationship("DailyPlan", back_populates="task_completions")

    def __repr__(self) -> str:
        return f"<TaskCompletion(id={self.id}, task_id={self.task_id}, completed={self.actual_completed})>"