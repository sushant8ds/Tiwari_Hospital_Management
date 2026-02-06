"""
User model for authentication and role-based access control
"""

from sqlalchemy import Column, String, Enum, DateTime, Boolean
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.core.database import Base


class UserRole(PyEnum):
    """User roles in the system"""
    ADMIN = "ADMIN"
    RECEPTION = "RECEPTION"


class User(Base):
    """User model for system authentication"""
    
    __tablename__ = "users"
    
    user_id = Column(String(20), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.RECEPTION)
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', username='{self.username}', role='{self.role}')>"