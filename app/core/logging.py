"""
Structured logging configuration for the Hospital Management System
"""

import logging
import sys
from app.core.config import settings

def setup_logging():
    """Configure structured logging across the application"""
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO
    
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    
    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if settings.ENVIRONMENT != "development" else logging.INFO)

logger = logging.getLogger("hospital_app")
