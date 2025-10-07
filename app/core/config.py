from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


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
    API_V1_STR: str = "/api/v1"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
