"""
Test Doctor CRUD operations
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.doctor import doctor_crud
from app.models.doctor import Doctor, DoctorStatus


@pytest.mark.asyncio
async def test_create_doctor_success(db_session: AsyncSession):
    """Test successful doctor creation."""
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. John Smith",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    assert doctor.doctor_id.startswith("D")
    assert doctor.name == "Dr. John Smith"
    assert doctor.department == "Cardiology"
    assert doctor.new_patient_fee == Decimal("500.00")
    assert doctor.followup_fee == Decimal("300.00")
    assert doctor.status == DoctorStatus.ACTIVE


@pytest.mark.asyncio
async def test_create_doctor_invalid_name(db_session: AsyncSession):
    """Test doctor creation with invalid name."""
    with pytest.raises(ValueError, match="Doctor name is required"):
        await doctor_crud.create_doctor(
            db=db_session,
            name="",  # Empty name
            department="Cardiology",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )


@pytest.mark.asyncio
async def test_create_doctor_invalid_department(db_session: AsyncSession):
    """Test doctor creation with invalid department."""
    with pytest.raises(ValueError, match="Department is required"):
        await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. John Smith",
            department="",  # Empty department
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )


@pytest.mark.asyncio
async def test_create_doctor_negative_fees(db_session: AsyncSession):
    """Test doctor creation with negative fees."""
    with pytest.raises(ValueError, match="New patient fee cannot be negative"):
        await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. John Smith",
            department="Cardiology",
            new_patient_fee=Decimal("-100.00"),  # Negative fee
            followup_fee=Decimal("300.00")
        )
    
    with pytest.raises(ValueError, match="Follow-up fee cannot be negative"):
        await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. John Smith",
            department="Cardiology",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("-50.00")  # Negative fee
        )


@pytest.mark.asyncio
async def test_get_doctor_by_id(db_session: AsyncSession):
    """Test getting doctor by ID."""
    # Create doctor
    created_doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. John Smith",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    # Get doctor by ID
    retrieved_doctor = await doctor_crud.get_doctor_by_id(
        db=db_session, 
        doctor_id=created_doctor.doctor_id
    )
    
    assert retrieved_doctor is not None
    assert retrieved_doctor.doctor_id == created_doctor.doctor_id
    assert retrieved_doctor.name == "Dr. John Smith"


@pytest.mark.asyncio
async def test_get_active_doctors(db_session: AsyncSession):
    """Test getting active doctors."""
    # Create active doctor
    active_doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Active",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00"),
        status=DoctorStatus.ACTIVE
    )
    
    # Create inactive doctor
    inactive_doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Inactive",
        department="Neurology",
        new_patient_fee=Decimal("600.00"),
        followup_fee=Decimal("400.00"),
        status=DoctorStatus.INACTIVE
    )
    
    # Get active doctors
    active_doctors = await doctor_crud.get_active_doctors(db=db_session)
    
    assert len(active_doctors) == 1
    assert active_doctors[0].name == "Dr. Active"
    assert active_doctors[0].status == DoctorStatus.ACTIVE


@pytest.mark.asyncio
async def test_get_doctors_by_department(db_session: AsyncSession):
    """Test getting doctors by department."""
    # Create doctors in different departments
    cardio_doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Heart",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    neuro_doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Brain",
        department="Neurology",
        new_patient_fee=Decimal("600.00"),
        followup_fee=Decimal("400.00")
    )
    
    # Get cardiology doctors
    cardio_doctors = await doctor_crud.get_doctors_by_department(
        db=db_session, 
        department="Cardiology"
    )
    
    assert len(cardio_doctors) == 1
    assert cardio_doctors[0].name == "Dr. Heart"
    assert cardio_doctors[0].department == "Cardiology"


@pytest.mark.asyncio
async def test_update_doctor(db_session: AsyncSession):
    """Test doctor update functionality."""
    # Create doctor
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. John Smith",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    # Update doctor
    updated_doctor = await doctor_crud.update_doctor(
        db=db_session,
        doctor_id=doctor.doctor_id,
        name="Dr. John Updated",
        new_patient_fee=Decimal("550.00")
    )
    
    assert updated_doctor is not None
    assert updated_doctor.name == "Dr. John Updated"
    assert updated_doctor.new_patient_fee == Decimal("550.00")
    assert updated_doctor.followup_fee == Decimal("300.00")  # Unchanged


@pytest.mark.asyncio
async def test_get_all_departments(db_session: AsyncSession):
    """Test getting all departments."""
    # Create doctors in different departments
    await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Heart",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Brain",
        department="Neurology",
        new_patient_fee=Decimal("600.00"),
        followup_fee=Decimal("400.00")
    )
    
    # Create inactive doctor (should not be included)
    await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Inactive",
        department="Orthopedics",
        new_patient_fee=Decimal("400.00"),
        followup_fee=Decimal("250.00"),
        status=DoctorStatus.INACTIVE
    )
    
    # Get all departments
    departments = await doctor_crud.get_all_departments(db=db_session)
    
    assert len(departments) == 2
    assert "Cardiology" in departments
    assert "Neurology" in departments
    assert "Orthopedics" not in departments  # Inactive doctor's department