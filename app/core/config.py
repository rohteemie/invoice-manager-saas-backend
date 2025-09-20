import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./multitenant_saas.db"
    )

    # API
    api_v1_str: str = "/api/v1"
    project_name: str = "Multi-Tenant SaaS Backend"

    class Config:
        env_file = ".env"


settings = Settings()
