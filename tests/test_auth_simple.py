"""
Simple tests for authentication system
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.user import User, UserRole
from app.crud.user import user_crud
from app.core.database import Base
from app.core.security import verify_password, get_password_hash, create_access_token, verify_token


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_auth.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="function")
async def db_session():
    """Create a test database session."""
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        
    async with TestSessionLocal() as session:
        yield session
        
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


class TestSecurityFunctions:
    """Test security utility functions."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpass123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token
        payload = verify_token(token)
        assert payload["sub"] == "testuser"
    
    def test_invalid_jwt_token(self):
        """Test invalid JWT token verification."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException):
            verify_token("invalid_token")


class TestUserCRUD:
    """Test user CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test user creation."""
        user = await user_crud.create_user(
            db=db_session,
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.RECEPTION
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.RECEPTION
        assert user.is_active is True
        assert user.user_id.startswith("U")
        assert verify_password("password123", user.hashed_password)
    
    @pytest.mark.asyncio
    async def test_get_user_by_username(self, db_session):
        """Test getting user by username."""
        # Create a user first
        created_user = await user_crud.create_user(
            db=db_session,
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.RECEPTION
        )
        
        # Get user by username
        user = await user_crud.get_user_by_username(db_session, "testuser")
        assert user is not None
        assert user.username == "testuser"
        assert user.user_id == created_user.user_id
    
    @pytest.mark.asyncio
    async def test_authenticate_user(self, db_session):
        """Test user authentication."""
        # Create a user first
        await user_crud.create_user(
            db=db_session,
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.RECEPTION
        )
        
        # Test successful authentication
        user = await user_crud.authenticate_user(db_session, "testuser", "password123")
        assert user is not None
        assert user.username == "testuser"
        
        # Test failed authentication
        user = await user_crud.authenticate_user(db_session, "testuser", "wrongpassword")
        assert user is None
        
        # Test non-existent user
        user = await user_crud.authenticate_user(db_session, "nonexistent", "password")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_create_duplicate_username(self, db_session):
        """Test creating user with duplicate username."""
        # Create first user
        await user_crud.create_user(
            db=db_session,
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.RECEPTION
        )
        
        # Try to create user with same username
        with pytest.raises(ValueError, match="Username or email already exists"):
            await user_crud.create_user(
                db=db_session,
                username="testuser",  # Same username
                email="different@example.com",
                password="password123",
                full_name="Different User",
                role=UserRole.RECEPTION
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])