"""Security utilities: JWT, password hashing, OAuth."""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from passlib.context import CryptContext
from jose import jwt

from app.core.config import Settings, get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def generate_token(
    subject: str | Any,
    expires_delta: timedelta,
    secret_key: str | None = None,
) -> str:
    """Generate a JWT token."""
    _settings = get_settings()
    secret = secret_key or _settings.jwt_secret

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=_settings.jwt_algorithm)
    return encoded_jwt


def create_access_token(user_id: str) -> str:
    """Create an access token for a user."""
    return generate_token(
        subject=user_id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    """Create a refresh token for a user."""
    return generate_token(
        subject=user_id,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, secret_key: str | None = None) -> dict:
    """Decode and verify a JWT token."""
    _settings = get_settings()
    secret = secret_key or _settings.jwt_secret

    try:
        payload = jwt.decode(token, secret, algorithms=[_settings.jwt_algorithm])
        return payload
    except jwt.JWTError as e:
        raise ValueError(f"Invalid token: {e}")


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)