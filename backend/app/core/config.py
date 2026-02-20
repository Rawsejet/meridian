"""Application configuration using Pydantic Settings."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://meridian:meridian@localhost:5432/meridian"
    )
    test_database_url: str = Field(
        default="postgresql+asyncpg://meridian:meridian@localhost:5432/meridian_test"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # JWT
    jwt_secret: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)

    # LLM
    llm_base_url: str = Field(default="http://localhost:8085")
    llm_max_tokens: int = Field(default=2048)
    llm_temperature: float = Field(default=0.1)
    llm_timeout_seconds: int = Field(default=30)

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/1")

    # Email (for Celery tasks)
    smtp_host: str = Field(default="localhost")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    smtp_from_email: str = Field(default="noreply@meridian.local")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # Web Push
    vapid_public_key: str = Field(default="")
    vapid_private_key: str = Field(default="")

    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        case_sensitive=False,
    )


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()