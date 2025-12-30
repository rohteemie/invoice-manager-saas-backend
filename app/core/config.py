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
    EMAIL_VERIFICATION_BASE_URL: Optional[str] = Field(
        None,
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
    # Email verification token expiration in hours (default 24 hours)
    EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS: int = Field(
        24,
        validation_alias="EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS"
    )
    # Password reset token expiration in minutes (default 30 minutes)
    PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES: int = Field(
        30,
        validation_alias="PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES"
    )
    POOL_SIZE: int = Field(10, validation_alias="POOL_SIZE")
    MAX_OVERFLOW: int = Field(20, validation_alias="MAX_OVERFLOW")
    POOL_TIMEOUT: int = Field(30, validation_alias="POOL_TIMEOUT")
    POOL_RECYCLE: int = Field(1800, validation_alias="POOL_RECYCLE")
    CONNECT_TIMEOUT: int = Field(10, validation_alias="DB_CONNECT_TIMEOUT")

    # Progressive Login Delay settings (OWASP ASVS & NIST 800-63B compliance)
    LOGIN_DELAY_SHORT: int = Field(
        2, validation_alias="LOGIN_DELAY_SHORT"
    )  # seconds for 4-5 failed attempts
    LOGIN_DELAY_MEDIUM: int = Field(
        30, validation_alias="LOGIN_DELAY_MEDIUM"
    )  # seconds for 6-8 failed attempts
    LOGIN_DELAY_LONG: int = Field(
        900, validation_alias="LOGIN_DELAY_LONG"
    )  # seconds (15 min) for 9+ failed attempts
    LOGIN_DELAY_THRESHOLD_SHORT: int = Field(
        4, validation_alias="LOGIN_DELAY_THRESHOLD_SHORT"
    )
    LOGIN_DELAY_THRESHOLD_MEDIUM: int = Field(
        6, validation_alias="LOGIN_DELAY_THRESHOLD_MEDIUM"
    )
    LOGIN_DELAY_THRESHOLD_LONG: int = Field(
        9, validation_alias="LOGIN_DELAY_THRESHOLD_LONG"
    )
    LOGIN_FAILURE_WINDOW: int = Field(
        3600, validation_alias="LOGIN_FAILURE_WINDOW"
    )  # 1 hour window for failure tracking

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
