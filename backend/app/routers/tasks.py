"""Task router."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime

from app.core.database import get_session
from app.models.user import User
from app.models.task import Task, Priority, TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    CompleteTaskRequest,
)
from app.schemas.auth import UserResponse
from app.core.security import decode_token

router = APIRouter(prefix="/tasks", tags=["tasks"])


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


@router.post("", response_model=TaskResponse)
async def create_task(
    request: TaskCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """Create a new task."""
    task = Task(
        user_id=current_user_id,
        title=request.title,
        description=request.description,
        due_date=request.due_date,
        priority=request.priority,
        estimated_minutes=request.estimated_minutes,
        energy_level=request.energy_level,
        category=request.category,
        status=TaskStatus.PENDING.value,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    priority: int | None = None,
    status: str | None = None,
    category: str | None = None,
    search: str | None = None,
    cursor: str | None = None,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """List tasks with filters, pagination, and search."""

    # Build query
    query = select(Task).where(Task.user_id == current_user_id)

    # Apply filters
    if priority:
        query = query.where(Task.priority == priority)
    if status:
        query = query.where(Task.status == status)
    if category:
        query = query.where(Task.category == category)
    if search:
        query = query.where(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
            )
        )

    # Cursor-based pagination
    if cursor:
        try:
            cursor_task = await db.get(Task, cursor)
            if cursor_task:
                query = query.where(Task.created_at < cursor_task.created_at)
        except Exception:
            pass

    query = query.order_by(Task.created_at.desc()).limit(limit + 1)
    result = await db.execute(query)
    tasks = result.scalars().all()

    # Determine pagination
    has_more = len(tasks) > limit
    if has_more:
        tasks = tasks[:limit]

    next_cursor = str(tasks[-1].id) if tasks and has_more else None

    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        has_more=has_more,
        next_cursor=next_cursor,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """Get a specific task by ID."""
    task = await db.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": f"Task with ID {task_id} not found",
                "field": "task_id",
            },
        )

    # Authorization check (404 not 403 for other users)
    if task.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Task not found",
                "field": "task_id",
            },
        )

    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    request: TaskUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """Update a task."""
    task = await db.get(Task, task_id)

    if not task or task.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": f"Task with ID {task_id} not found",
                "field": "task_id",
            },
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """Soft-delete a task."""
    task = await db.get(Task, task_id)

    if not task or task.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": f"Task with ID {task_id} not found",
                "field": "task_id",
            },
        )

    # Soft delete
    task.status = TaskStatus.CANCELLED.value
    await db.commit()

    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    request: CompleteTaskRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """Mark a task as completed."""
    task = await db.get(Task, task_id)

    if not task or task.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": f"Task with ID {task_id} not found",
                "field": "task_id",
            },
        )

    task.status = TaskStatus.COMPLETED.value
    task.completed_at = request.completed_at or datetime.utcnow()
    await db.commit()
    await db.refresh(task)

    return TaskResponse.model_validate(task)