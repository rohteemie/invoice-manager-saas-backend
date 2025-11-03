from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class Settings(BaseSettings):
    PROJECT_NAME: str = Field(..., validation_alias="PROJECT_NAME")
    SECRET_KEY: str = Field(..., validation_alias="SECRET_KEY")
    ACCESS_TOKEN_EXPIRATION: int = Field(
        60 * 24,
        validation_alias="ACCESS_TOKEN_EXPIRATION"
    )
    REFRESH_TOKEN_EXPIRATION: int = Field(
        60 * 24 * 7,
        validation_alias="REFRESH_TOKEN_EXPIRATION"
    )
    DATABASE_URL: str = Field(..., validation_alias="DATABASE_URL")
    REDIS_URL: Optional[str] = Field(
        None,
        validation_alias="REDIS_URL"
    )
    SENTRY_DSN: Optional[str] = Field(
        None,
        validation_alias="SENTRY_DSN"
    )
    ENVIRONMENT: str = Field(
        "development",
        validation_alias="ENVIRONMENT"
    )
    RATE_LIMIT_RETRY_AFTER_FALLBACK: str = Field(
        "60",
        validation_alias="RATE_LIMIT_RETRY_AFTER_FALLBACK"
    )
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = Field(
        ["*"],
        validation_alias="CORS_ORIGINS"
    )
    # Email configuration
    EMAIL_VERIFICATION_BASE_URL: Optional[str] = Field(
        "https://yourapp.com",
        validation_alias="EMAIL_VERIFICATION_BASE_URL"
    )
    # SendGrid / Email settings
    SENDGRID_API_KEY: Optional[str] = Field(
        None,
        validation_alias="SENDGRID_API_KEY"
    )
    EMAILS_FROM: Optional[str] = Field(
        None,
        validation_alias="EMAILS_FROM"
    )

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
