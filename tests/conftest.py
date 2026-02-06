"""
Test configuration and fixtures
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        
    async with TestSessionLocal() as session:
        yield session
        
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""
    def get_test_db():
        return db_session
    
    app.dependency_overrides[get_db] = get_test_db
    
    # Use the transport approach for newer httpx versions
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client (alias for client fixture)."""
    def get_test_db():
        return db_session
    
    app.dependency_overrides[get_db] = get_test_db
    
    # Use the transport approach for newer httpx versions
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_patient(db_session: AsyncSession):
    """Create a sample patient for testing."""
    from app.crud.patient import patient_crud
    from app.models.patient import Gender
    
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test Street, Test City",
        mobile_number="9876543210"
    )
    
    return patient


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing."""
    return {
        "name": "John Doe",
        "age": 35,
        "gender": "MALE",
        "address": "123 Test Street, Test City",
        "mobile_number": "9876543210"
    }


@pytest.fixture
def sample_doctor_data():
    """Sample doctor data for testing."""
    return {
        "name": "Dr. Smith",
        "department": "Cardiology",
        "new_patient_fee": 500.00,
        "followup_fee": 300.00,
        "status": "ACTIVE"
    }


@pytest_asyncio.fixture
async def auth_headers(db_session: AsyncSession) -> dict:
    """Create authentication headers for testing."""
    from app.crud.user import user_crud
    from app.models.user import UserRole
    from app.core.security import create_access_token
    
    # Create a test user
    user = await user_crud.create_user(
        db=db_session,
        username="testuser",
        email="test@example.com",
        password="testpass123",
        full_name="Test User",
        role=UserRole.RECEPTION
    )
    
    # Generate token
    token = create_access_token(data={"sub": user.username})
    
    return {"Authorization": f"Bearer {token}"}