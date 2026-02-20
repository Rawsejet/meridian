"""Tests for Google OAuth - Scenario 02: User Logs In with Google OAuth."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.user import User
from unittest.mock import AsyncMock, Mock, patch


@pytest.mark.asyncio
async def test_google_oauth_url_endpoint(client: AsyncClient):
    """Test that Google OAuth URL endpoint returns proper response."""
    response = await client.get("/api/v1/auth/google/url")
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert "state" in data
    assert "accounts.google.com" in data["auth_url"]


@pytest.mark.asyncio
async def test_google_oauth_redirect_endpoint(client: AsyncClient):
    """Test that Google OAuth redirect endpoint redirects to Google."""
    response = await client.get("/api/v1/auth/google", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert "accounts.google.com" in response.headers["location"]


@pytest.mark.asyncio
async def test_google_oauth_first_time_user(client: AsyncClient, db_session):
    """Test Google OAuth flow for a first-time user."""
    # Mock the internal functions
    with patch('app.routers.auth.exchange_code_for_token') as mock_exchange, \
         patch('app.routers.auth.get_google_user_info') as mock_user_info:

        mock_exchange.return_value = {
            "access_token": "mock_access_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        mock_user_info.return_value = {
            "id": "123456789",
            "email": "googleuser@example.com",
            "name": "Google User",
            "picture": "https://example.com/avatar.jpg",
            "locale": "en-US",
        }

        # Simulate callback with code
        response = await client.get(
            "/api/v1/auth/google/callback",
            params={
                "code": "mock_auth_code",
                "state": "mock_state",
            },
            cookies={
                "oauth_state": "mock_state",
                "pkce_verifier": "mock_verifier",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "googleuser@example.com"
        assert data["user"]["display_name"] == "Google User"
        assert data["user"]["avatar_url"] == "https://example.com/avatar.jpg"

        # Verify user was created with google_id
        result = await db_session.execute(
            select(User).where(User.email == "googleuser@example.com")
        )
        user = result.scalar_one()
        assert user.google_id == "123456789"
        assert user.password_hash is None


@pytest.mark.asyncio
async def test_google_oauth_returning_user(client: AsyncClient, db_session):
    """Test Google OAuth flow for a returning user."""
    # Create a user with google_id first
    existing_user = User(
        email="returning@example.com",
        display_name="Returning User",
        password_hash=None,
        google_id="987654321",
        avatar_url="https://example.com/old_avatar.jpg",
    )
    db_session.add(existing_user)
    await db_session.commit()
    await db_session.refresh(existing_user)

    # Mock the internal functions
    with patch('app.routers.auth.exchange_code_for_token') as mock_exchange, \
         patch('app.routers.auth.get_google_user_info') as mock_user_info:

        mock_exchange.return_value = {
            "access_token": "mock_access_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        mock_user_info.return_value = {
            "id": "987654321",
            "email": "returning@example.com",
            "name": "Returning User",
            "picture": "https://example.com/new_avatar.jpg",
            "locale": "en-US",
        }

        # Simulate callback
        response = await client.get(
            "/api/v1/auth/google/callback",
            params={
                "code": "mock_auth_code",
                "state": "mock_state",
            },
            cookies={
                "oauth_state": "mock_state",
                "pkce_verifier": "mock_verifier",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "returning@example.com"
        assert data["user"]["avatar_url"] == "https://example.com/new_avatar.jpg"

        # Verify user still has the same google_id
        result = await db_session.execute(
            select(User).where(User.email == "returning@example.com")
        )
        user = result.scalar_one()
        assert user.google_id == "987654321"


@pytest.mark.asyncio
async def test_google_oauth_missing_state(client: AsyncClient):
    """Test Google OAuth callback without state parameter."""
    response = await client.get(
        "/api/v1/auth/google/callback",
        params={"code": "mock_code"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "GOOGLE_OAUTH_STATE_EXPIRED"


@pytest.mark.asyncio
async def test_google_oauth_invalid_state(client: AsyncClient):
    """Test Google OAuth callback with mismatched state."""
    response = await client.get(
        "/api/v1/auth/google/callback",
        params={
            "code": "mock_code",
            "state": "wrong_state",
        },
        cookies={
            "oauth_state": "correct_state",
            "pkce_verifier": "mock_verifier",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "GOOGLE_OAUTH_STATE_MISMATCH"


@pytest.mark.asyncio
async def test_google_oauth_missing_code(client: AsyncClient):
    """Test Google OAuth callback without code parameter."""
    response = await client.get(
        "/api/v1/auth/google/callback",
        params={"state": "mock_state"},
        cookies={
            "oauth_state": "mock_state",
            "pkce_verifier": "mock_verifier",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "GOOGLE_OAUTH_NO_CODE"


@pytest.mark.asyncio
async def test_google_oauth_email_collision_with_password_user(client: AsyncClient, db_session):
    """Test that Google OAuth doesn't silently merge with email/password users."""
    # Create a user with email/password first
    existing_user = User(
        email="collision@example.com",
        display_name="Collision User",
        password_hash="$2b$12$hashedpassword",
        google_id=None,
    )
    db_session.add(existing_user)
    await db_session.commit()
    await db_session.refresh(existing_user)

    # Mock the internal functions
    with patch('app.routers.auth.exchange_code_for_token') as mock_exchange, \
         patch('app.routers.auth.get_google_user_info') as mock_user_info:

        mock_exchange.return_value = {
            "access_token": "mock_access_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        mock_user_info.return_value = {
            "id": "123456789",
            "email": "collision@example.com",
            "name": "Google Collision User",
            "picture": "https://example.com/avatar.jpg",
            "locale": "en-US",
        }

        # Simulate callback - this should fail or handle the collision
        response = await client.get(
            "/api/v1/auth/google/callback",
            params={
                "code": "mock_auth_code",
                "state": "mock_state",
            },
            cookies={
                "oauth_state": "mock_state",
                "pkce_verifier": "mock_verifier",
            },
        )

        # Should return an error about email collision
        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["code"] == "AUTH_EMAIL_COLLISION"

        # Verify the user still has a password_hash (not merged)
        result = await db_session.execute(
            select(User).where(User.email == "collision@example.com")
        )
        user = result.scalar_one()
        assert user.password_hash is not None  # Should still have password
        assert user.google_id is None  # Should not have google_id
