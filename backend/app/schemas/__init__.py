"""Pydantic schemas for API requests and responses."""
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    TokenRefreshResponse,
    UserResponse,
    GoogleAuthUrlResponse,
)
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    CompleteTaskRequest,
)
from app.schemas.plan import (
    DailyPlanCreate,
    DailyPlanUpdate,
    DailyPlanResponse,
    DailyPlanListResponse,
    ReorderTasksRequest,
    CompletePlanRequest,
    ReflectionResponse,
)
from app.schemas.notification import (
    NotificationPreferenceCreate,
    NotificationPreferenceResponse,
    PushSubscriptionCreate,
    PushSubscriptionResponse,
)
from app.schemas.intelligence import (
    TaskParseRequest,
    TaskParseResponse,
    SuggestionRequest,
    SuggestionResponse,
    InsightResponse,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest",
    "LoginResponse",
    "TokenRefreshResponse",
    "UserResponse",
    "GoogleAuthUrlResponse",
    # Task
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskListResponse",
    "CompleteTaskRequest",
    # Plan
    "DailyPlanCreate",
    "DailyPlanUpdate",
    "DailyPlanResponse",
    "DailyPlanListResponse",
    "ReorderTasksRequest",
    "CompletePlanRequest",
    "ReflectionResponse",
    # Notification
    "NotificationPreferenceCreate",
    "NotificationPreferenceResponse",
    "PushSubscriptionCreate",
    "PushSubscriptionResponse",
    # Intelligence
    "TaskParseRequest",
    "TaskParseResponse",
    "SuggestionRequest",
    "SuggestionResponse",
    "InsightResponse",
]