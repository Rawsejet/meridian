"""Task router."""
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timezone

from app.core.database import get_session_factory
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


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        await session.close()


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
    db: AsyncSession = Depends(get_db),
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
    due_after: str | None = None,
    due_before: str | None = None,
    include_cancelled: bool = False,
    cursor: str | None = None,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List tasks with filters, pagination, and search."""

    # Validate limit parameter
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "TASK_INVALID_LIMIT",
                "message": "Limit must be positive",
                "field": "limit",
            },
        )
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "TASK_INVALID_LIMIT",
                "message": "Limit cannot exceed 100",
                "field": "limit",
            },
        )

    # Build query
    query = select(Task).where(Task.user_id == current_user_id)

    # Exclude cancelled tasks by default
    if not include_cancelled and status is None:
        query = query.where(Task.status != TaskStatus.CANCELLED.value)

    # Apply filters
    if priority:
        query = query.where(Task.priority == priority)
    if status:
        query = query.where(Task.status == status)
    if category:
        query = query.where(Task.category == category)

    # Apply date range filters
    if due_after:
        try:
            due_after_dt = datetime.fromisoformat(due_after.replace("Z", "+00:00"))
            query = query.where(Task.due_date >= due_after_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "TASK_INVALID_DUE_DATE",
                    "message": "Invalid due_after date format",
                    "field": "due_after",
                },
            )

    if due_before:
        try:
            due_before_dt = datetime.fromisoformat(due_before.replace("Z", "+00:00"))
            query = query.where(Task.due_date <= due_before_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "TASK_INVALID_DUE_DATE",
                    "message": "Invalid due_before date format",
                    "field": "due_before",
                },
            )

    # Apply search
    if search:
        query = query.where(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
            )
        )

    # Cursor-based pagination with proper stability
    if cursor:
        try:
            cursor_task = await db.get(Task, cursor)
            if not cursor_task or str(cursor_task.user_id) != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "TASK_INVALID_CURSOR",
                        "message": "Invalid cursor provided",
                        "field": "cursor",
                    },
                )
            # Use a more stable cursor approach by including created_at in the ordering
            query = query.where(
                or_(
                    Task.created_at < cursor_task.created_at,
                    and_(
                        Task.created_at == cursor_task.created_at,
                        Task.id < cursor_task.id
                    )
                )
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "TASK_INVALID_CURSOR",
                    "message": "Invalid cursor provided",
                    "field": "cursor",
                },
            )

    # Order by created_at DESC, then by id DESC for stability
    query = query.order_by(Task.created_at.desc(), Task.id.desc()).limit(limit + 1)
    result = await db.execute(query)
    tasks = result.scalars().all()

    # Determine pagination
    has_more = len(tasks) > limit
    if has_more:
        tasks = tasks[:limit]

    # Generate next cursor from the last task in the current page
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
    db: AsyncSession = Depends(get_db),
):
    """Get a specific task by ID."""
    task = await db.get(Task, task_id)

    if not task or str(task.user_id) != current_user_id:
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
    db: AsyncSession = Depends(get_db),
):
    """Update a task."""
    task = await db.get(Task, task_id)

    if not task or str(task.user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Task not found",
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


@router.delete("/{task_id}", response_model=TaskResponse)
async def delete_task(
    task_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a task (sets status to cancelled)."""
    task = await db.get(Task, task_id)

    if not task or str(task.user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Task not found",
                "field": "task_id",
            },
        )

    # Soft delete
    task.status = TaskStatus.CANCELLED.value
    await db.commit()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    request: CompleteTaskRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Mark a task as completed."""
    task = await db.get(Task, task_id)

    if not task or str(task.user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Task not found",
                "field": "task_id",
            },
        )

    task.status = TaskStatus.COMPLETED.value
    task.completed_at = request.completed_at or datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)

    return TaskResponse.model_validate(task)