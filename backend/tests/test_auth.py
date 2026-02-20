"""Tests for authentication router — Scenario 01: Register with email/password."""
import pytest
from jose import jwt
from httpx import AsyncClient
from sqlalchemy import select


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, db_session):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, db_session):
    """Test registration with existing email."""
    # Register first user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "display_name": "First User",
        },
    )

    # Try to register again
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password456",
            "display_name": "Second User",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["code"] == "AUTH_EMAIL_EXISTS"


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient, db_session):
    """Test registration with weak password."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",  # Too short
            "display_name": "Weak User",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session):
    """Test successful login."""
    # Register user first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "display_name": "Login User",
        },
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, db_session):
    """Test login with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == "AUTH_INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, db_session):
    """Test getting current user profile."""
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile@example.com",
            "password": "password123",
            "display_name": "Profile User",
        },
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "profile@example.com",
            "password": "password123",
        },
    )
    token = login_response.json()["access_token"]

    # Get user profile
    response = await client.get(
        "/api/v1/auth/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@example.com"


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient, db_session):
    """Test getting user profile without token."""
    response = await client.get("/api/v1/auth/users/me")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == "AUTH_TOKEN_REQUIRED"


# --- Scenario 01 satisfaction criteria tests ---


@pytest.mark.asyncio
async def test_register_password_is_bcrypt_hashed(client: AsyncClient, db_session):
    """Verify password_hash is bcrypt, not plaintext."""
    from app.models.user import User

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "password": "Str0ng!Pass#2025",
            "display_name": "Alice",
        },
    )
    assert response.status_code == 200

    # Query the user directly from DB
    result = await db_session.execute(select(User).where(User.email == "alice@example.com"))
    user = result.scalar_one()
    assert user.password_hash is not None
    assert user.password_hash.startswith("$2b$"), "Password hash should be bcrypt"
    assert user.password_hash != "Str0ng!Pass#2025", "Password must not be stored as plaintext"


@pytest.mark.asyncio
async def test_register_jwt_contains_user_id_and_exp(client: AsyncClient, db_session):
    """Verify access token is a valid JWT with user_id (sub) and exp."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "jwtcheck@example.com",
            "password": "Str0ng!Pass#2025",
            "display_name": "JWT User",
        },
    )
    assert response.status_code == 200
    data = response.json()

    from app.core.config import get_settings
    secret = get_settings().jwt_secret

    access_payload = jwt.decode(data["access_token"], secret, algorithms=["HS256"])
    assert "sub" in access_payload, "JWT must contain 'sub' (user_id)"
    assert "exp" in access_payload, "JWT must contain 'exp' (expiry)"
    assert access_payload["sub"] == data["id"]

    refresh_payload = jwt.decode(data["refresh_token"], secret, algorithms=["HS256"])
    assert "sub" in refresh_payload
    assert "exp" in refresh_payload


@pytest.mark.asyncio
async def test_register_creates_notification_preferences(client: AsyncClient, db_session):
    """Verify notification_preferences record is created with defaults."""
    from app.models.notification import NotificationPreference
    from datetime import time

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "notifcheck@example.com",
            "password": "Str0ng!Pass#2025",
            "display_name": "Notif User",
        },
    )
    assert response.status_code == 200
    user_id = response.json()["id"]

    result = await db_session.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    pref = result.scalar_one_or_none()
    assert pref is not None, "Notification preferences should be created on registration"
    assert pref.morning_briefing_enabled is True
    assert pref.morning_briefing_time == time(8, 0)
    assert pref.midday_nudge_enabled is True
    assert pref.midday_nudge_time == time(12, 0)
    assert pref.evening_reflection_enabled is True
    assert pref.evening_reflection_time == time(20, 0)


@pytest.mark.asyncio
async def test_register_display_name_in_response(client: AsyncClient, db_session):
    """Verify the response includes the authenticated user's display name."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "displayname@example.com",
            "password": "Str0ng!Pass#2025",
            "display_name": "Alice",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Alice"
    assert data["user"]["display_name"] == "Alice"


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient, db_session):
    """Verify invalid email format returns 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "Str0ng!Pass#2025",
            "display_name": "Bad Email",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_display_name(client: AsyncClient, db_session):
    """Verify missing display_name returns 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "noname@example.com",
            "password": "Str0ng!Pass#2025",
        },
    )
    assert response.status_code == 422
