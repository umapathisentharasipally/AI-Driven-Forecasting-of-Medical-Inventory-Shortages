from pathlib import Path
from typing import List, Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    MONGO_DB_NAME: str
    MONGO_CLUSTER_NAME: str
    MONGO_USERNAME: str
    MONGO_PASSWORD: str

    @property
    def mongo_uri(self):
        return (
            f"mongodb+srv://"
            f"{self.MONGO_USERNAME}:"
            f"{self.MONGO_PASSWORD}@"
            f"{self.MONGO_CLUSTER_NAME}.mongodb.net/"
            f"{self.MONGO_DB_NAME}"
            f"?retryWrites=true&w=majority"
        )

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ADMIN_EMAIL: Optional[EmailStr] = None
    ADMIN_PASSWORD: Optional[str] = None
    ADMIN_FULL_NAME: str = "Administrator"
    ADMIN_DEPARTMENT: str = "IT"
    ADMIN_EMPLOYEE_ID: Optional[str] = None
    ADMIN_ROLE_NAME: str = "admin"

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
        env_file=str(BASE_DIR.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()