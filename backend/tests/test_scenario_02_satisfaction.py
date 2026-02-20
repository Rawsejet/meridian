"""Satisfaction criteria tests for Scenario 02: User Logs In with Google OAuth."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.user import User
from unittest.mock import patch


@pytest.mark.asyncio
async def test_scenario_02_satisfaction_criteria(client: AsyncClient, db_session):
    """
    Test all satisfaction criteria for Scenario 02:

    - **1.0**: Both first-time and returning flows work, CSRF protection present, email collision handled
    """

    # Mock the internal functions
    with patch('app.routers.auth.exchange_code_for_token') as mock_exchange, \
         patch('app.routers.auth.get_google_user_info') as mock_user_info:

        # Test 1: First-time user flow
        mock_exchange.return_value = {
            "access_token": "mock_access_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        mock_user_info.return_value = {
            "id": "123456789",
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://example.com/avatar.jpg",
            "locale": "en-US",
        }

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
        assert data["user"]["email"] == "newuser@example.com"

        # Verify user was created with google_id and no password
        result = await db_session.execute(
            select(User).where(User.email == "newuser@example.com")
        )
        user = result.scalar_one()
        assert user.google_id == "123456789"
        assert user.password_hash is None

        # Test 2: Returning user flow
        response = await client.get(
            "/api/v1/auth/google/callback",
            params={
                "code": "mock_auth_code_2",
                "state": "mock_state_2",
            },
            cookies={
                "oauth_state": "mock_state_2",
                "pkce_verifier": "mock_verifier_2",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["display_name"] == "New User"

        # Verify user still has the same google_id
        result = await db_session.execute(
            select(User).where(User.email == "newuser@example.com")
        )
        user = result.scalar_one()
        assert user.google_id == "123456789"

        # Test 3: CSRF protection (state parameter)
        response = await client.get(
            "/api/v1/auth/google/callback",
            params={
                "code": "mock_auth_code",
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

        # Test 4: Email collision handling
        # Create a user with email/password first
        email_password_user = User(
            email="collision@example.com",
            display_name="Collision User",
            password_hash="$2b$12$hashedpassword",
            google_id=None,
        )
        db_session.add(email_password_user)
        await db_session.commit()

        mock_user_info.return_value = {
            "id": "987654321",
            "email": "collision@example.com",
            "name": "Google Collision User",
            "picture": "https://example.com/avatar.jpg",
            "locale": "en-US",
        }

        response = await client.get(
            "/api/v1/auth/google/callback",
            params={
                "code": "mock_auth_code_3",
                "state": "mock_state_3",
            },
            cookies={
                "oauth_state": "mock_state_3",
                "pkce_verifier": "mock_verifier_3",
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
        assert user.password_hash is not None
        assert user.google_id is None

        # Test 5: Tokens are in the same format as email/password login
        # This is already verified by the response model (GoogleOAuthCallbackResponse)
        # which has the same structure as LoginResponse


@pytest.mark.asyncio
async def test_scenario_02_google_id_matching(client: AsyncClient, db_session):
    """
    Verify that users are matched by google_id, not email.

    This handles the case where a user changes their email in Google.
    """
    # Create a user with google_id
    existing_user = User(
        email="oldemail@example.com",
        display_name="User",
        password_hash=None,
        google_id="987654321",
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

        # Google returns the same google_id but different email
        mock_user_info.return_value = {
            "id": "987654321",  # Same google_id
            "email": "newemail@example.com",  # Different email
            "name": "User",
            "picture": "https://example.com/avatar.jpg",
            "locale": "en-US",
        }

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
        # Should return the existing user with updated email
        assert data["user"]["email"] == "newemail@example.com"

        # Verify user still has the same google_id
        result = await db_session.execute(
            select(User).where(User.google_id == "987654321")
        )
        user = result.scalar_one()
        # Refresh to get the latest data from the database
        await db_session.refresh(user)
        assert user.google_id == "987654321"
        assert user.email == "newemail@example.com"


@pytest.mark.asyncio
async def test_scenario_02_oauth_user_cannot_login_with_password(client: AsyncClient, db_session):
    """
    Verify that a user who only has a Google account cannot log in with email/password.
    """
    # Create a user with Google OAuth (no password)
    oauth_user = User(
        email="oauthonly@example.com",
        display_name="OAuth User",
        password_hash=None,
        google_id="123456789",
    )
    db_session.add(oauth_user)
    await db_session.commit()

    # Try to login with email/password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "oauthonly@example.com",
            "password": "any_password",
        },
    )

    # Should fail because user has no password
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == "AUTH_INVALID_CREDENTIALS"
