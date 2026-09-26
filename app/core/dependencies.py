"""
FastAPI dependencies for authentication and authorization
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User, UserRole
from app.crud.user import user_crud


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    
    try:
        payload = verify_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = await user_crud.get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_user_from_token_or_query(
    request: Request,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from Authorization header, query param, or cookies"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    jwt_token = token
    if not jwt_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            jwt_token = auth_header.split(" ")[1]
        elif "access_token" in request.cookies:
            jwt_token = request.cookies.get("access_token")
            
    if not jwt_token:
        raise credentials_exception
        
    try:
        payload = verify_token(jwt_token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
        
    user = await user_crud.get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: UserRole):
    """Decorator factory for role-based access control"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    return role_checker


def require_admin():
    """Require admin role"""
    return require_role(UserRole.ADMIN)


def require_reception():
    """Require reception role"""
    return require_role(UserRole.RECEPTION)


def require_admin_or_reception():
    """Require admin or reception role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in [UserRole.ADMIN, UserRole.RECEPTION]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Required role: ADMIN or RECEPTION"
            )
        return current_user
    return role_checker