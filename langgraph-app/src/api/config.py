"""Production configuration with environment validation."""

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Production settings with validation.

    Validates all required environment variables on startup.
    Raises ValidationError if any required variable is missing.
    """

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    # CORS
    cors_origins: list[str] = Field(default_factory=list)
    cors_allow_credentials: bool = True

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/czech_medai"
    )
    db_pool_min_size: int = 10
    db_pool_max_size: int = 50

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 1000

    # Security
    rate_limit_per_minute: int = 10
    max_query_length: int = 1000
    jwt_secret: str | None = None

    # Monitoring
    sentry_dsn: str | None = None
    sentry_environment: str | None = None

    # Logging
    log_format: Literal["json", "text"] = "json"
    log_file: str = "logs/czech-medai.log"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @model_validator(mode="after")
    def validate_cors_production(self) -> "Settings":
        """Validate CORS is properly configured for production."""
        if self.environment == "production":
            if not self.cors_origins:
                raise ValueError(
                    "CORS_ORIGINS must be set for production environment. "
                    "Use comma-separated origins (e.g., 'https://app.example.com')."
                )
            if "*" in self.cors_origins:
                raise ValueError(
                    "Wildcard '*' CORS origin is not allowed in production. "
                    "Specify explicit origins."
                )
        return self

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is valid."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
