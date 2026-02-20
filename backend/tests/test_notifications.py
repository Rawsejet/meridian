"""Tests for notifications router."""
import pytest


@pytest.mark.asyncio
async def test_get_notification_preferences(client, auth_headers):
    """Test getting notification preferences."""
    response = client.get(
        "/api/v1/notifications/preferences",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "morning_briefing_enabled" in data
    assert "midday_nudge_enabled" in data
    assert "evening_reflection_enabled" in data


@pytest.mark.asyncio
async def test_update_notification_preferences(client, auth_headers):
    """Test updating notification preferences."""
    response = client.patch(
        "/api/v1/notifications/preferences",
        json={
            "morning_briefing_enabled": False,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["morning_briefing_enabled"] is False


@pytest.mark.asyncio
async def test_create_push_subscription(client, auth_headers):
    """Test creating a push subscription."""
    response = client.post(
        "/api/v1/notifications/push-subscriptions",
        json={
            "endpoint": "https://example.com/push",
            "p256dh_key": "test-key",
            "auth_key": "test-auth",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_list_push_subscriptions(client, auth_headers):
    """Test listing push subscriptions."""
    response = client.get(
        "/api/v1/notifications/push-subscriptions",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)