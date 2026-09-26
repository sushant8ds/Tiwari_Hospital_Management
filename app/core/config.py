"""
Application configuration settings
"""

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


def normalize_db_url(db_url: str) -> str:
    """Convert postgres:// and postgresql:// to postgresql+asyncpg:// for asyncpg driver"""
    if not db_url:
        return "postgresql+asyncpg://postgres:postgres@localhost:5432/hospital_db"
    
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return db_url


class Settings(BaseSettings):
    """Application settings"""
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")
    
    # Database
    DATABASE_URL: str = normalize_db_url(os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/hospital_db"))
    DATABASE_URL_TEST: str = "sqlite+aiosqlite:///./test.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours - full work shift
    
    # Hospital Information
    HOSPITAL_NAME: str = "Surya Hospital"
    HOSPITAL_ADDRESS: str = "Tamkuhi Raj, Kushinagar, Uttar Pradesh - 274407"
    HOSPITAL_PHONE: str = "+91-9580845238"
    HOSPITAL_LOGO_PATH: str = "static/images/hospital_logo.png"
    
    # Application
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Printing
    DEFAULT_PRINTER_TYPE: str = "thermal"
    THERMAL_PRINTER_WIDTH: int = 58
    A4_PRINTER_NAME: str = "default"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            return normalize_db_url(v)
        return v


# Global settings instance
settings = Settings()
