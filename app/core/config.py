"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./hospital.db"
    DATABASE_URL_TEST: str = "sqlite+aiosqlite:///./test.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Hospital Information
    HOSPITAL_NAME: str = "Surya City Hospital"
    HOSPITAL_ADDRESS: str = "123 Medical Street, Healthcare City, State - 123456"
    HOSPITAL_PHONE: str = "+91-1234567890"
    HOSPITAL_LOGO_PATH: str = "static/images/hospital_logo.png"
    
    # Application
    ENVIRONMENT: str = "development"
    
    # Printing
    DEFAULT_PRINTER_TYPE: str = "thermal"
    THERMAL_PRINTER_WIDTH: int = 58
    A4_PRINTER_NAME: str = "default"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()