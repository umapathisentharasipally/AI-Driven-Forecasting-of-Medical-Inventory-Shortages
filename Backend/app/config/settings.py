from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str = "medical_inventory"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    APP_ENV: str = "development"
    APP_NAME: str = "Medical Inventory Forecasting"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    ML_BASE_PATH: str = "ml"
    ML_CONFIGS_PATH: str = "ml/configs"
    ML_ARTIFACTS_PATH: str = "ml/artifacts"

    PAGE_SIZE_DEFAULT: int = 20
    PAGE_SIZE_MAX: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()