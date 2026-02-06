"""
CRUD operations for User model
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.services.id_generator import generate_user_id


class UserCRUD:
    """CRUD operations for User model"""
    
    async def create_user(
        self,
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.RECEPTION
    ) -> User:
        """Create a new user"""
        try:
            user_id = await generate_user_id(db)
            hashed_password = get_password_hash(password)
            
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                role=role
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Username or email already exists")
    
    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(
            select(User).where(User.username == username, User.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(
            select(User).where(User.user_id == user_id, User.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def authenticate_user(
        self, 
        db: AsyncSession, 
        username: str, 
        password: str
    ) -> Optional[User]:
        """Authenticate user with username and password"""
        from app.core.security import verify_password
        
        user = await self.get_user_by_username(db, username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def update_user_status(
        self, 
        db: AsyncSession, 
        user_id: str, 
        is_active: bool
    ) -> Optional[User]:
        """Update user active status"""
        user = await self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        user.is_active = is_active
        await db.commit()
        await db.refresh(user)
        return user


# Global instance
user_crud = UserCRUD()