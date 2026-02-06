"""
Authentication schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema"""
    username: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema"""
    user_id: str
    username: str
    full_name: str
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User creation schema"""
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.RECEPTION
    
    class Config:
        use_enum_values = True