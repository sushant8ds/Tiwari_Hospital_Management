"""
Application configuration settings
"""

from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import Optional
import os


def get_database_url() -> str:
    """
    Get database URL and convert it to the correct format for asyncpg
    """
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/hospital_db")
    
    # Render provides postgres:// but we need postgresql+asyncpg://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    return db_url


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = get_database_url()
    DATABASE_URL_TEST: str = "sqlite+aiosqlite:///./test.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
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
    
    @model_validator(mode="after")
    def check_secret_key_in_production(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production" and self.SECRET_KEY == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be changed from the default value in a production environment.")
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
