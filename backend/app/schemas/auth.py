"""Authentication schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr
    password: str
    display_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class RegisterResponse(BaseModel):
    """Response schema for user registration."""

    id: str
    email: str
    display_name: str
    created_at: datetime


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response schema for user login."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user: "UserResponse"


class TokenRefreshResponse(BaseModel):
    """Response schema for token refresh."""

    access_token: str
    token_type: str = "Bearer"


class UserResponse(BaseModel):
    """Response schema for user profile."""

    id: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    created_at: datetime

    model_config = {"from_attributes": True}


class GoogleAuthUrlResponse(BaseModel):
    """Response schema for Google OAuth URL."""

    auth_url: str
    state: str


class GoogleOAuthCallbackResponse(BaseModel):
    """Response schema for Google OAuth callback."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user: "UserResponse"