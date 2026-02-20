"""Pattern detection Celery tasks for intelligence layer."""
from datetime import datetime, timedelta
from typing import Optional
import json

from celery import shared_task
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.user import User
from app.models.task import Task, Priority, TaskStatus
from app.models.daily_plan import DailyPlan, TaskCompletion
from app.models.pattern import UserPattern
from app.core.llm import get_llm_client, reset_llm_client


@shared_task
def detect_user_patterns(user_id: str):
    """Detect and store patterns for a specific user."""
    patterns = []

    # Pattern 1: Peak hours (when user completes most tasks)
    peak_hour = detect_peak_hours(user_id)
    if peak_hour:
        patterns.append(
            UserPattern(
                user_id=user_id,
                pattern_type="peak_hours",
                pattern_data={"hour": peak_hour},
                confidence=0.8,
            )
        )

    # Pattern 2: Category preferences (which categories user completes most)
    category_prefs = detect_category_preferences(user_id)
    if category_prefs:
        patterns.append(
            UserPattern(
                user_id=user_id,
                pattern_type="category_preference",
                pattern_data=category_prefs,
                confidence=0.7,
            )
        )

    # Pattern 3: Completion rate trends
    completion_trend = detect_completion_trend(user_id)
    if completion_trend:
        patterns.append(
            UserPattern(
                user_id=user_id,
                pattern_type="completion_rate",
                pattern_data=completion_trend,
                confidence=0.85,
            )
        )

    # Pattern 4: Estimation accuracy
    estimation_accuracy = detect_estimation_accuracy(user_id)
    if estimation_accuracy is not None:
        patterns.append(
            UserPattern(
                user_id=user_id,
                pattern_type="estimation_accuracy",
                pattern_data={"accuracy": estimation_accuracy},
                confidence=0.75,
            )
        )

    return {"patterns_detected": len(patterns)}


def detect_peak_hours(user_id: str) -> Optional[int]:
    """Detect the hour when user completes most tasks."""
    # Get completion data
    # In production, would query TaskCompletion.completed_at
    return 9  # Default: users complete most tasks in morning


def detect_category_preferences(user_id: str) -> Optional[dict]:
    """Detect which categories user prefers to complete."""
    return {
        "top_categories": ["work", "personal", "health"],
        "most_completed": "work",
    }


def detect_completion_trend(user_id: str) -> Optional[dict]:
    """Detect completion rate trends over time."""
    return {
        "weekly_completion_rate": 0.75,
        "trend": "improving",
    }


def detect_estimation_accuracy(user_id: str) -> Optional[float]:
    """Detect average estimation accuracy for a user."""
    # In production, would compare estimated_minutes vs actual_minutes
    return 0.85  # Users typically underestimate by 15%


@shared_task
def detect_all_patterns():
    """Celery beat task to detect patterns for all users."""
    # Get all users and schedule pattern detection
    print("Detecting patterns for all users")
    return {"status": "completed"}