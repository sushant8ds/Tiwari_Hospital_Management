"""
Test database models
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient, Gender
from app.models.doctor import Doctor, DoctorStatus
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_create_patient(db_session: AsyncSession, sample_patient_data):
    """Test patient creation."""
    patient = Patient(
        patient_id="P202401010001",
        **sample_patient_data
    )
    
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    
    assert patient.patient_id == "P202401010001"
    assert patient.name == sample_patient_data["name"]
    assert patient.gender == Gender.MALE


@pytest.mark.asyncio
async def test_create_doctor(db_session: AsyncSession, sample_doctor_data):
    """Test doctor creation."""
    doctor = Doctor(
        doctor_id="D001",
        **sample_doctor_data
    )
    
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    
    assert doctor.doctor_id == "D001"
    assert doctor.name == sample_doctor_data["name"]
    assert doctor.status == DoctorStatus.ACTIVE


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test user creation."""
    user = User(
        user_id="U001",
        username="admin",
        email="admin@hospital.com",
        hashed_password="hashed_password",
        full_name="System Administrator",
        role=UserRole.ADMIN
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.user_id == "U001"
    assert user.username == "admin"
    assert user.role == UserRole.ADMIN