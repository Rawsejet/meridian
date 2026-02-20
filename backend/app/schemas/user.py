"""User schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Request schema for user creation."""

    email: str
    password: str
    display_name: str


class UserUpdate(BaseModel):
    """Request schema for user update."""

    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None