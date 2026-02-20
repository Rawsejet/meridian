"""Intelligence router - LLM-powered features."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import json

from app.core.database import get_session
from app.models.user import User
from app.models.task import Task
from app.models.daily_plan import DailyPlan, TaskCompletion
from app.models.pattern import UserPattern
from app.core.llm import get_llm_client, reset_llm_client
from app.schemas.intelligence import (
    TaskParseRequest,
    TaskParseResponse,
    SuggestionRequest,
    SuggestionResponse,
    SuggestionReason,
    SuggestionWarning,
    InsightResponse,
)
from app.core.security import decode_token

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


async def get_current_user_id(request: Request) -> str:
    """Extract and validate current user from JWT token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_TOKEN_REQUIRED",
                "message": "Authorization token required",
                "field": "Authorization",
            },
        )

    token = auth_header[7:]
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "AUTH_INVALID_TOKEN",
                    "message": "Invalid token",
                    "field": "Authorization",
                },
            )
        return user_id
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_TOKEN",
                "message": str(e),
                "field": "Authorization",
            },
        )


TASK_PARSE_PROMPT = """You are a task parser for a daily planner app.
User timezone: {timezone} | Today: {today}

Extract structured fields from natural language input.
Return ONLY a JSON object:
- title (string, required)
- description (string or null)
- due_date (string YYYY-MM-DD or null, resolve relative dates from today)
- priority (integer 1-4, default 2)
- estimated_minutes (integer or null)
- energy_level (integer 1-3 or null)
- category (string or null)

No explanation, no markdown, just JSON."""


@router.post("/tasks/parse", response_model=TaskParseResponse)
async def parse_task(
    request: TaskParseRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    """Parse natural language into structured task data using LLM."""
    llm = get_llm_client()

    messages = [
        {
            "role": "system",
            "content": TASK_PARSE_PROMPT.format(
                timezone=request.timezone, today=request.today
            ),
        },
        {"role": "user", "content": request.text},
    ]

    try:
        result = await llm.complete_json(messages, temperature=0.0)
        return TaskParseResponse(**result)
    except Exception as e:
        # Fallback: treat entire text as title
        return TaskParseResponse(
            title=request.text[:500],
            description=None,
            due_date=None,
            priority=2,
            estimated_minutes=None,
            energy_level=None,
            category=None,
        )


SUGGESTION_PROMPT = """Given tasks and user productivity patterns, suggest optimal order for today.
Return ONLY JSON:
{
    "task_order": ["id1", "id2", ...],
    "reasoning": [{"task_id": "...", "reason": "..."}],
    "warnings": [{"task_id": "...", "message": "..."}]
}"""


@router.post("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    request: SuggestionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db=None,
):
    """Get AI-powered task ordering suggestions."""
    from app.core.database import get_session

    if db is None:
        db = await get_session().__anext__()

    # Get user's patterns for context
    result = await db.execute(
        select(UserPattern).where(
            UserPattern.user_id == current_user_id
        ).order_by(UserPattern.computed_at.desc()).limit(10)
    )
    patterns = result.scalars().all()

    # Get task details
    result = await db.execute(
        select(Task).where(
            and_(
                Task.id.in_(request.task_ids),
                Task.user_id == current_user_id,
            )
        )
    )
    tasks = result.scalars().all()
    task_map = {str(t.id): t for t in tasks}

    # Build messages for LLM
    task_data = []
    for tid in request.task_ids:
        if tid in task_map:
            t = task_map[tid]
            task_data.append({
                "id": tid,
                "title": t.title,
                "priority": t.priority,
                "due_date": str(t.due_date) if t.due_date else None,
                "category": t.category,
                "estimated_minutes": t.estimated_minutes,
            })

    pattern_data = [
        {"type": p.pattern_type, "data": p.pattern_data}
        for p in patterns
    ]

    llm = get_llm_client()
    messages = [
        {"role": "system", "content": SUGGESTION_PROMPT},
        {
            "role": "user",
            "content": json.dumps({
                "tasks": task_data,
                "patterns": pattern_data,
                "user_timezone": request.user_timezone,
                "today": request.today,
            }),
        },
    ]

    try:
        result = await llm.complete_json(messages, temperature=0.0)
        return SuggestionResponse(
            task_order=result.get("task_order", request.task_ids),
            reasoning=[
                SuggestionReason(**r) for r in result.get("reasoning", [])
            ],
            warnings=[
                SuggestionWarning(**w) for w in result.get("warnings", [])
            ],
        )
    except Exception:
        # Fallback: rule-based ordering (priority desc, then due date asc)
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                -t.priority,
                str(t.due_date or "9999-12-31"),
            ),
        )
        return SuggestionResponse(
            task_order=[str(t.id) for t in sorted_tasks],
            reasoning=[],
            warnings=[],
        )


@router.get("/insights", response_model=InsightResponse)
async def get_insights(
    days: int = 7,
    current_user_id: str = Depends(get_current_user_id),
    db=None,
):
    """Get weekly insights about user's productivity patterns."""
    from app.core.database import get_session

    if db is None:
        db = await get_session().__anext__()

    start_date = datetime.utcnow() - timedelta(days=days)

    # Get task completions for the period
    result = await db.execute(
        select(TaskCompletion, Task).join(Task).where(
            and_(
                Task.user_id == current_user_id,
                TaskCompletion.completed_at >= start_date,
            )
        ).order_by(TaskCompletion.completed_at.desc())
    )
    completions = result.all()

    if not completions:
        return InsightResponse(
            period_start=start_date,
            period_end=datetime.utcnow(),
            total_tasks_completed=0,
            average_completion_rate=0.0,
            most_completed_category=None,
            peak_completion_hour=0,
            average_estimation_accuracy=None,
        )

    total_completed = len(completions)
    categories = {}
    hours = []
    estimation_errors = []

    for completion, task in completions:
        # Count by category
        cat = task.category or "uncategorized"
        categories[cat] = categories.get(cat, 0) + 1

        # Track completion hour
        if completion.completed_at:
            hours.append(completion.completed_at.hour)

        # Track estimation accuracy (if applicable)
        if task.estimated_minutes and completion.actual_minutes:
            error = abs(
                task.estimated_minutes - completion.actual_minutes
            ) / task.estimated_minutes
            estimation_errors.append(error)

    # Find most completed category
    most_completed_category = max(categories, key=categories.get) if categories else None

    # Find peak completion hour
    peak_completion_hour = (
        max(set(hours), key=hours.count) if hours else 0
    )

    # Calculate average estimation accuracy
    avg_estimation_accuracy = (
        sum(estimation_errors) / len(estimation_errors)
        if estimation_errors
        else None
    )

    return InsightResponse(
        period_start=start_date,
        period_end=datetime.utcnow(),
        total_tasks_completed=total_completed,
        average_completion_rate=total_completed
        / len(completions),  # Simplified
        most_completed_category=most_completed_category,
        peak_completion_hour=peak_completion_hour,
        average_estimation_accuracy=avg_estimation_accuracy,
    )


@router.get("/patterns")
async def get_user_patterns(
    pattern_type: str | None = None,
    current_user_id: str = Depends(get_current_user_id),
    db=None,
):
    """Get user's computed patterns."""
    from app.core.database import get_session

    if db is None:
        db = await get_session().__anext__()

    query = select(UserPattern).where(
        UserPattern.user_id == current_user_id
    )

    if pattern_type:
        query = query.where(UserPattern.pattern_type == pattern_type)

    query = query.order_by(UserPattern.computed_at.desc())

    result = await db.execute(query)
    patterns = result.scalars().all()

    return {"patterns": [p.pattern_data for p in patterns]}