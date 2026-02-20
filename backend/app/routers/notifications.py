"""Notification router."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.database import get_session
from app.models.user import User
from app.models.notification import NotificationPreference, PushSubscription
from app.schemas.notification import (
    NotificationPreferenceCreate,
    NotificationPreferenceResponse,
    PushSubscriptionCreate,
    PushSubscriptionResponse,
)
from app.core.security import decode_token
from sqlalchemy import and_

router = APIRouter(prefix="/notifications", tags=["notifications"])


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


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """Get notification preferences for current user."""

    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == current_user_id
        )
    )
    preference = result.scalar_one_or_none()

    if not preference:
        # Return defaults
        return NotificationPreferenceResponse(
            id="",
            user_id=current_user_id,
            morning_briefing_enabled=True,
            morning_briefing_time=datetime.strptime("08:00", "%H:%M").time(),
            midday_nudge_enabled=True,
            midday_nudge_time=datetime.strptime("12:00", "%H:%M").time(),
            evening_reflection_enabled=True,
            evening_reflection_time=datetime.strptime("20:00", "%H:%M").time(),
            email_notifications=True,
            push_notifications=True,
            quiet_hours_start=None,
            quiet_hours_end=None,
        )

    return NotificationPreferenceResponse.model_validate(preference)


@router.patch("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    request: NotificationPreferenceCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """Update notification preferences for current user."""

    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == current_user_id
        )
    )
    preference = result.scalar_one_or_none()

    if not preference:
        # Create new preference
        preference = NotificationPreference(
            user_id=current_user_id,
            **request.model_dump(),
        )
        db.add(preference)
    else:
        # Update existing
        for key, value in request.model_dump(exclude_unset=True).items():
            setattr(preference, key, value)

    await db.commit()
    await db.refresh(preference)

    return NotificationPreferenceResponse.model_validate(preference)


@router.post("/push-subscriptions", response_model=PushSubscriptionResponse)
async def create_push_subscription(
    request: PushSubscriptionCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """Create or update a push subscription."""

    # Check if subscription exists
    result = await db.execute(
        select(PushSubscription).where(
            and_(
                PushSubscription.user_id == current_user_id,
                PushSubscription.endpoint == request.endpoint,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        for key, value in request.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return PushSubscriptionResponse.model_validate(existing)

    # Create new subscription
    subscription = PushSubscription(
        user_id=current_user_id,
        **request.model_dump(),
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    return PushSubscriptionResponse.model_validate(subscription)


@router.delete("/push-subscriptions/{subscription_id}")
async def delete_push_subscription(
    subscription_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """Delete a push subscription."""

    subscription = await db.get(PushSubscription, subscription_id)

    if not subscription or subscription.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PUSH_SUBSCRIPTION_NOT_FOUND",
                "message": "Push subscription not found",
                "field": "subscription_id",
            },
        )

    await db.delete(subscription)
    await db.commit()

    return {"message": "Push subscription deleted successfully"}


@router.get("/push-subscriptions", response_model=list[PushSubscriptionResponse])
async def list_push_subscriptions(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """List all push subscriptions for current user."""

    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == current_user_id
        )
    )
    subscriptions = result.scalars().all()

    return [
        PushSubscriptionResponse.model_validate(s) for s in subscriptions
    ]