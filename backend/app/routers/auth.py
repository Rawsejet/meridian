"""Authentication router."""
import secrets
import base64
import hashlib
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
from typing import Optional, AsyncGenerator

from app.core.database import get_session_factory
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.models.notification import NotificationPreference
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    TokenRefreshResponse,
    UserResponse,
    GoogleAuthUrlResponse,
    GoogleOAuthCallbackResponse,
)
from app.schemas.user import UserCreate, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        await session.close()


def create_oauth_state() -> str:
    """Generate a random state parameter for OAuth."""
    return secrets.token_urlsafe(32)


def generate_pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code verifier and code challenge pair."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


async def create_default_notification_preference(db: AsyncSession, user_id: str):
    """Create default notification preferences for a new user."""
    notification_pref = NotificationPreference(
        user_id=user_id,
        morning_briefing_enabled=True,
        morning_briefing_time=datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0).time(),
        midday_nudge_enabled=True,
        midday_nudge_time=datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0).time(),
        evening_reflection_enabled=True,
        evening_reflection_time=datetime.now(timezone.utc).replace(hour=20, minute=0, second=0, microsecond=0).time(),
        email_notifications=True,
        push_notifications=True,
    )
    db.add(notification_pref)
    await db.commit()


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user with email and password."""
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "AUTH_EMAIL_EXISTS",
                "message": "Email already registered",
                "field": "email",
            },
        )

    # Create user
    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        display_name=request.display_name,
        timezone="UTC",
    )

    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "AUTH_EMAIL_EXISTS",
                "message": "Email already registered",
                "field": "email",
            },
        )

    # Create default notification preferences
    await create_default_notification_preference(db, str(user.id))

    # Create tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return RegisterResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            created_at=user.created_at,
        ),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login user with email and password."""
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS",
                "message": "Invalid email or password",
                "field": "email",
            },
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS",
                "message": "Invalid email or password",
                "field": "password",
            },
        )

    # Create tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            created_at=user.created_at,
        ),
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    # Get refresh token from cookie or body
    refresh_token = None
    if "refresh_token" in request.cookies:
        refresh_token = request.cookies["refresh_token"]
    else:
        body = await request.json()
        refresh_token = body.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "AUTH_TOKEN_REQUIRED",
                "message": "Refresh token required",
                "field": "refresh_token",
            },
        )

    # Validate token
    try:
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "AUTH_INVALID_TOKEN",
                    "message": "Invalid token",
                    "field": "refresh_token",
                },
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_TOKEN",
                "message": str(e),
                "field": "refresh_token",
            },
        )

    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_USER_NOT_FOUND",
                "message": "User not found",
                "field": None,
            },
        )

    # Create new access token
    new_access_token = create_access_token(str(user.id))

    # Create new refresh token (rotation)
    new_refresh_token = create_refresh_token(str(user.id))

    return TokenRefreshResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.get("/google/url", response_model=GoogleAuthUrlResponse)
async def get_google_auth_url(response: Response):
    """Get Google OAuth URL with PKCE."""
    state = create_oauth_state()
    code_verifier, code_challenge = generate_pkce_pair()

    # Store PKCE values in secure cookie
    response.set_cookie(
        "oauth_state",
        state,
        max_age=300,  # 5 minutes
        httponly=True,
        secure=True,
        samesite="lax",
    )
    response.set_cookie(
        "pkce_verifier",
        code_verifier,
        max_age=300,
        httponly=True,
        secure=True,
        samesite="lax",
    )

    params = {
        "client_id": "YOUR_GOOGLE_CLIENT_ID",
        "redirect_uri": "http://localhost:8000/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid profile email",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return GoogleAuthUrlResponse(auth_url=auth_url, state=state)


@router.get("/google")
async def google_login(response: Response):
    """Initiate Google OAuth flow - redirects to Google."""
    state = create_oauth_state()
    code_verifier, code_challenge = generate_pkce_pair()

    # Store PKCE values in secure cookie
    response.set_cookie(
        "oauth_state",
        state,
        max_age=300,  # 5 minutes
        httponly=True,
        secure=True,
        samesite="lax",
    )
    response.set_cookie(
        "pkce_verifier",
        code_verifier,
        max_age=300,
        httponly=True,
        secure=True,
        samesite="lax",
    )

    params = {
        "client_id": "YOUR_GOOGLE_CLIENT_ID",
        "redirect_uri": "http://localhost:8000/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid profile email",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/google/callback", response_model=GoogleOAuthCallbackResponse)
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle Google OAuth callback."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "GOOGLE_OAUTH_ERROR", "message": error},
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "GOOGLE_OAUTH_NO_CODE", "message": "No code received"},
        )

    # Retrieve stored state and verifier
    stored_state = request.cookies.get("oauth_state")
    stored_verifier = request.cookies.get("pkce_verifier")

    if not stored_state or not stored_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "GOOGLE_OAUTH_STATE_EXPIRED", "message": "State expired"},
        )

    if state != stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "GOOGLE_OAUTH_STATE_MISMATCH", "message": "Invalid state"},
        )

    # Exchange code for tokens
    try:
        token_data = await exchange_code_for_token(code)
    except HTTPException:
        raise

    # Get user info from Google
    try:
        user_info = await get_google_user_info(token_data["access_token"])
    except HTTPException:
        raise

    # Find or create user by google_id first, then by email
    google_id = user_info.get("id")
    result = await db.execute(
        select(User).where(User.google_id == google_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Check if a user with this email exists (email/password user)
        result = await db.execute(
            select(User).where(User.email == user_info["email"])
        )
        existing_email_user = result.scalar_one_or_none()

        if existing_email_user:
            # Email collision: existing user has email/password, new user has Google
            if existing_email_user.password_hash:
                # Existing user has password - don't merge
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "AUTH_EMAIL_COLLISION",
                        "message": "Email already registered with password. Please link accounts.",
                        "field": "email",
                    },
                )
            else:
                # Existing user is already a Google OAuth user - update them
                user = existing_email_user
        else:
            # Create new user from Google info
            user = User(
                email=user_info["email"],
                display_name=user_info.get("name", user_info["email"].split("@")[0]),
                password_hash=None,  # No password for OAuth users
                google_id=google_id,
                avatar_url=user_info.get("picture"),
                timezone=user_info.get("locale", "UTC"),
            )
            db.add(user)
            try:
                await db.commit()
                await db.refresh(user)
            except IntegrityError:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"code": "DB_ERROR", "message": "Failed to create user"},
                )

    # Update user info if needed
    if user:
        if user_info.get("email") and user_info.get("email") != user.email:
            user.email = user_info.get("email")
        if user_info.get("name") and user_info.get("name") != user.display_name:
            user.display_name = user_info.get("name")
        if user_info.get("picture") and user_info.get("picture") != user.avatar_url:
            user.avatar_url = user_info.get("picture")
        if user_info.get("locale") and user_info.get("locale") != user.timezone:
            user.timezone = user_info.get("locale")

        # Set google_id if not already set
        if google_id and not user.google_id:
            user.google_id = google_id

        await db.commit()
        await db.refresh(user)

    # Create tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return GoogleOAuthCallbackResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            created_at=user.created_at,
        ),
    )


async def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token."""
    import httpx

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": "YOUR_GOOGLE_CLIENT_ID",
        "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
        "code": code,
        "redirect_uri": "http://localhost:8000/api/v1/auth/google/callback",
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "GOOGLE_TOKEN_EXCHANGE_FAILED", "message": "Failed to exchange code"},
        )

    return response.json()


async def get_google_user_info(access_token: str) -> dict:
    """Get user info from Google API."""
    import httpx

    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(userinfo_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "GOOGLE_USERINFO_FAILED", "message": "Failed to get user info"},
        )

    return response.json()


@router.get("/users/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get current user profile."""
    # Extract user from JWT token
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

    token = auth_header[7:]  # Remove "Bearer " prefix

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_TOKEN",
                "message": str(e),
                "field": "Authorization",
            },
        )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_USER_NOT_FOUND",
                "message": "User not found",
                "field": None,
            },
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        timezone=user.timezone,
        created_at=user.created_at,
    )


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth"}