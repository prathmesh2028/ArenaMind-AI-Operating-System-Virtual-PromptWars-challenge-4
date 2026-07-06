import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    APP_ENV: str = "development"
    SECRET_KEY: str = "super_secret_stadium_key"
    
    # PostgreSQL Configuration
    DATABASE_URL: str = "postgresql://postgres:secret_password@localhost:5432/arenamind"
    
    # Firebase Configuration
    FIREBASE_DATABASE_URL: Optional[str] = None
    FIREBASE_CREDENTIALS_JSON_PATH: Optional[str] = None
    
    # Gemini AI Configuration
    GEMINI_API_KEY: str = "mock_gemini_key"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
