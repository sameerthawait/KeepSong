import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Keepsong API"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = Field(default="postgresql://postgres:password@localhost:5432/keepsong")
    JWT_SECRET: str = Field(default="supersecretjwtkeyforlocaldevelopment123!")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Object Storage (S3 / Cloudflare R2)
    OBJECT_STORAGE_ENDPOINT: str = Field(default="")
    OBJECT_STORAGE_BUCKET: str = Field(default="keepsong-assets")
    OBJECT_STORAGE_ACCESS_KEY_ID: str = Field(default="")
    OBJECT_STORAGE_SECRET_ACCESS_KEY: str = Field(default="")

    # Third-party API keys & Sentry
    ASR_API_KEY: str = Field(default="")
    NIM_API_KEY: str = Field(default="")
    NIM_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1")
    NIM_MODEL: str = Field(default="meta/llama-3.1-8b-instruct")
    WEATHER_API_KEY: str = Field(default="")
    SENTRY_DSN: str = Field(default="")
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
