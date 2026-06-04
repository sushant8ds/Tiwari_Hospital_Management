"""
Tests for authentication system
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.crud.user import user_crud
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession):
    """Create a sample user for testing."""
    user = await user_crud.create_user(
        db=db_session,
        username="testuser",
        email="test@example.com",
        password="testpass123",
        full_name="Test User",
        role=UserRole.RECEPTION
    )
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    """Create an admin user for testing."""
    user = await user_crud.create_user(
        db=db_session,
        username="admin",
        email="admin@example.com",
        password="admin123",
        full_name="Admin User",
        role=UserRole.ADMIN
    )
    return user


class TestUserCRUD:
    """Test user CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Test user creation."""
        user = await user_crud.create_user(
            db=db_session,
            username="newuser",
            email="newuser@example.com",
            password="password123",
            full_name="New User",
            role=UserRole.RECEPTION
        )
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.role == UserRole.RECEPTION
        assert user.is_active is True
        assert user.user_id.startswith("U")
    
    @pytest.mark.asyncio
    async def test_create_duplicate_username(self, db_session: AsyncSession, sample_user: User):
        """Test creating user with duplicate username."""
        with pytest.raises(ValueError, match="Username or email already exists"):
            await user_crud.create_user(
                db=db_session,
                username="testuser",  # Same as sample_user
                email="different@example.com",
                password="password123",
                full_name="Different User",
                role=UserRole.RECEPTION
            )
    
    @pytest.mark.asyncio
    async def test_get_user_by_username(self, db_session: AsyncSession, sample_user: User):
        """Test getting user by username."""
        user = await user_crud.get_user_by_username(db_session, "testuser")
        assert user is not None
        assert user.username == "testuser"
        assert user.user_id == sample_user.user_id
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, db_session: AsyncSession):
        """Test getting non-existent user."""
        user = await user_crud.get_user_by_username(db_session, "nonexistent")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session: AsyncSession, sample_user: User):
        """Test successful user authentication."""
        user = await user_crud.authenticate_user(db_session, "testuser", "testpass123")
        assert user is not None
        assert user.username == "testuser"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session: AsyncSession, sample_user: User):
        """Test authentication with wrong password."""
        user = await user_crud.authenticate_user(db_session, "testuser", "wrongpassword")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, db_session: AsyncSession):
        """Test authentication with non-existent user."""
        user = await user_crud.authenticate_user(db_session, "nonexistent", "password")
        assert user is None


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, sample_user: User):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpass123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_credentials(self, client: AsyncClient, sample_user: User):
        """Test login with wrong credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent", "password": "password"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_profile_authenticated(self, client: AsyncClient, sample_user: User):
        """Test getting profile with valid token."""
        # First login to get token
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpass123"}
        )
        token = login_response.json()["access_token"]
        
        # Get profile
        response = await client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["full_name"] == "Test User"
        assert data["role"] == "RECEPTION"
        assert data["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_get_profile_unauthenticated(self, client: AsyncClient):
        """Test getting profile without token."""
        response = await client.get("/api/v1/auth/profile")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_profile_invalid_token(self, client: AsyncClient):
        """Test getting profile with invalid token."""
        response = await client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_register_user_as_admin(self, client: AsyncClient, admin_user: User):
        """Test user registration by admin."""
        # Login as admin
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]
        
        # Register new user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newstaff",
                "email": "newstaff@example.com",
                "password": "password123",
                "full_name": "New Staff Member",
                "role": "RECEPTION"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newstaff"
        assert data["role"] == "RECEPTION"
    
    @pytest.mark.asyncio
    async def test_register_user_as_reception(self, client: AsyncClient, sample_user: User):
        """Test user registration by reception user (should fail)."""
        # Login as reception
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpass123"}
        )
        token = login_response.json()["access_token"]
        
        # Try to register new user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newstaff",
                "email": "newstaff@example.com",
                "password": "password123",
                "full_name": "New Staff Member",
                "role": "RECEPTION"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "Only admin users can create new accounts" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient):
        """Test logout endpoint."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    @pytest.mark.asyncio
    async def test_admin_role_access(self, client: AsyncClient, admin_user: User):
        """Test admin role access."""
        # Login as admin
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]
        
        # Access profile (should work)
        response = await client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["role"] == "ADMIN"
    
    @pytest.mark.asyncio
    async def test_reception_role_access(self, client: AsyncClient, sample_user: User):
        """Test reception role access."""
        # Login as reception
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpass123"}
        )
        token = login_response.json()["access_token"]
        
        # Access profile (should work)
        response = await client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["role"] == "RECEPTION"