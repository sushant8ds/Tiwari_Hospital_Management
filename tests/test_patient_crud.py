"""
Test Patient CRUD operations
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.patient import patient_crud
from app.models.patient import Patient, Gender


@pytest.mark.asyncio
async def test_create_patient_success(db_session: AsyncSession):
    """Test successful patient creation."""
    patient = await patient_crud.create_patient(
        db=db_session,
        name="John Doe",
        age=35,
        gender=Gender.MALE,
        address="123 Test Street, Test City",
        mobile_number="9876543210"
    )
    
    assert patient.patient_id.startswith("P")
    assert patient.name == "John Doe"
    assert patient.age == 35
    assert patient.gender == Gender.MALE
    assert patient.mobile_number == "9876543210"


@pytest.mark.asyncio
async def test_create_patient_invalid_mobile(db_session: AsyncSession):
    """Test patient creation with invalid mobile number."""
    with pytest.raises(ValueError, match="Invalid mobile number format"):
        await patient_crud.create_patient(
            db=db_session,
            name="John Doe",
            age=35,
            gender=Gender.MALE,
            address="123 Test Street",
            mobile_number="123456789"  # Invalid format
        )


@pytest.mark.asyncio
async def test_create_patient_invalid_age(db_session: AsyncSession):
    """Test patient creation with invalid age."""
    with pytest.raises(ValueError, match="Age must be between 0 and 150"):
        await patient_crud.create_patient(
            db=db_session,
            name="John Doe",
            age=200,  # Invalid age
            gender=Gender.MALE,
            address="123 Test Street",
            mobile_number="9876543210"
        )


@pytest.mark.asyncio
async def test_create_patient_empty_name(db_session: AsyncSession):
    """Test patient creation with empty name."""
    with pytest.raises(ValueError, match="Patient name is required"):
        await patient_crud.create_patient(
            db=db_session,
            name="",  # Empty name
            age=35,
            gender=Gender.MALE,
            address="123 Test Street",
            mobile_number="9876543210"
        )


@pytest.mark.asyncio
async def test_create_patient_duplicate_mobile(db_session: AsyncSession):
    """Test patient creation with duplicate mobile number."""
    # Create first patient
    await patient_crud.create_patient(
        db=db_session,
        name="John Doe",
        age=35,
        gender=Gender.MALE,
        address="123 Test Street",
        mobile_number="9876543210"
    )
    
    # Try to create second patient with same mobile
    with pytest.raises(ValueError, match="Mobile number already exists"):
        await patient_crud.create_patient(
            db=db_session,
            name="Jane Doe",
            age=30,
            gender=Gender.FEMALE,
            address="456 Another Street",
            mobile_number="9876543210"  # Duplicate mobile
        )


@pytest.mark.asyncio
async def test_get_patient_by_id(db_session: AsyncSession):
    """Test getting patient by ID."""
    # Create patient
    created_patient = await patient_crud.create_patient(
        db=db_session,
        name="John Doe",
        age=35,
        gender=Gender.MALE,
        address="123 Test Street",
        mobile_number="9876543210"
    )
    
    # Get patient by ID
    retrieved_patient = await patient_crud.get_patient_by_id(
        db=db_session, 
        patient_id=created_patient.patient_id
    )
    
    assert retrieved_patient is not None
    assert retrieved_patient.patient_id == created_patient.patient_id
    assert retrieved_patient.name == "John Doe"


@pytest.mark.asyncio
async def test_get_patient_by_mobile(db_session: AsyncSession):
    """Test getting patient by mobile number."""
    # Create patient
    created_patient = await patient_crud.create_patient(
        db=db_session,
        name="John Doe",
        age=35,
        gender=Gender.MALE,
        address="123 Test Street",
        mobile_number="9876543210"
    )
    
    # Get patient by mobile
    retrieved_patient = await patient_crud.get_patient_by_mobile(
        db=db_session, 
        mobile_number="9876543210"
    )
    
    assert retrieved_patient is not None
    assert retrieved_patient.patient_id == created_patient.patient_id
    assert retrieved_patient.mobile_number == "9876543210"


@pytest.mark.asyncio
async def test_search_patients(db_session: AsyncSession):
    """Test patient search functionality."""
    # Create test patients
    patient1 = await patient_crud.create_patient(
        db=db_session,
        name="John Doe",
        age=35,
        gender=Gender.MALE,
        address="123 Test Street",
        mobile_number="9876543210"
    )
    
    patient2 = await patient_crud.create_patient(
        db=db_session,
        name="Jane Smith",
        age=28,
        gender=Gender.FEMALE,
        address="456 Another Street",
        mobile_number="9876543211"
    )
    
    # Search by name
    results = await patient_crud.search_patients(db=db_session, search_term="John")
    assert len(results) == 1
    assert results[0].name == "John Doe"
    
    # Search by mobile
    results = await patient_crud.search_patients(db=db_session, search_term="9876543211")
    assert len(results) == 1
    assert results[0].name == "Jane Smith"
    
    # Search by patient ID
    results = await patient_crud.search_patients(db=db_session, search_term=patient1.patient_id)
    assert len(results) == 1
    assert results[0].patient_id == patient1.patient_id


@pytest.mark.asyncio
async def test_update_patient(db_session: AsyncSession):
    """Test patient update functionality."""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="John Doe",
        age=35,
        gender=Gender.MALE,
        address="123 Test Street",
        mobile_number="9876543210"
    )
    
    # Update patient
    updated_patient = await patient_crud.update_patient(
        db=db_session,
        patient_id=patient.patient_id,
        name="John Updated",
        age=36
    )
    
    assert updated_patient is not None
    assert updated_patient.name == "John Updated"
    assert updated_patient.age == 36
    assert updated_patient.mobile_number == "9876543210"  # Unchanged


@pytest.mark.asyncio
async def test_update_nonexistent_patient(db_session: AsyncSession):
    """Test updating non-existent patient."""
    result = await patient_crud.update_patient(
        db=db_session,
        patient_id="P999999999999",
        name="Non Existent"
    )
    
    assert result is None