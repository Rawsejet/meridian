"""Tests for authentication router."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text


@pytest.mark.asyncio
async def test_register_success(client, db_session):
    """Test successful user registration."""
    response = client.post(
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


@pytest.mark.asyncio
async def test_register_duplicate_email(client, db_session):
    """Test registration with existing email."""
    # Register first user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "display_name": "First User",
        },
    )

    # Try to register again
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password456",
            "display_name": "Second User",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "AUTH_EMAIL_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_register_weak_password(client, db_session):
    """Test registration with weak password."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",  # Too short
            "display_name": "Weak User",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client, db_session):
    """Test successful login."""
    # Register user first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "display_name": "Login User",
        },
    )

    # Login
    response = client.post(
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
async def test_login_invalid_credentials(client, db_session):
    """Test login with invalid credentials."""
    response = client.post(
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
async def test_get_current_user(client, db_session):
    """Test getting current user profile."""
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile@example.com",
            "password": "password123",
            "display_name": "Profile User",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "profile@example.com",
            "password": "password123",
        },
    )
    token = login_response.json()["access_token"]

    # Get user profile
    response = client.get(
        "/api/v1/auth/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@example.com"


@pytest.mark.asyncio
async def test_get_current_user_no_token(client, db_session):
    """Test getting user profile without token."""
    response = client.get("/api/v1/auth/users/me")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == "AUTH_TOKEN_REQUIRED"