"""
Tests for IPD CRUD operations
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Gender
from app.models.doctor import DoctorStatus
from app.models.visit import VisitType, PaymentMode
from app.models.bed import WardType, BedStatus
from app.models.ipd import IPDStatus
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.ipd import ipd_crud, bed_crud


@pytest.mark.asyncio
async def test_create_bed(db_session: AsyncSession):
    """Test creating a new bed"""
    bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="G101",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    assert bed.bed_number == "G101"
    assert bed.ward_type == WardType.GENERAL
    assert bed.per_day_charge == Decimal("500.00")
    assert bed.status == BedStatus.AVAILABLE


@pytest.mark.asyncio
async def test_admit_patient_to_ipd(db_session: AsyncSession):
    """Test admitting a patient to IPD"""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543210"
    )
    
    # Create bed
    bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="G102",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    # Admit patient
    ipd = await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=bed.bed_id,
        file_charge=Decimal("1000.00")
    )
    
    assert ipd.patient_id == patient.patient_id
    assert ipd.bed_id == bed.bed_id
    assert ipd.file_charge == Decimal("1000.00")
    assert ipd.status == IPDStatus.ADMITTED
    
    # Verify bed is now occupied
    updated_bed = await bed_crud.get_bed_by_id(db_session, bed.bed_id)
    assert updated_bed.status == BedStatus.OCCUPIED


@pytest.mark.asyncio
async def test_admit_patient_with_visit(db_session: AsyncSession):
    """Test admitting a patient to IPD with OPD visit"""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543211"
    )
    
    # Create doctor
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="General",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    # Create visit
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Create bed
    bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="G103",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    # Admit patient with visit
    ipd = await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=bed.bed_id,
        file_charge=Decimal("1000.00"),
        visit_id=visit.visit_id
    )
    
    assert ipd.visit_id == visit.visit_id
    assert ipd.status == IPDStatus.ADMITTED


@pytest.mark.asyncio
async def test_change_bed(db_session: AsyncSession):
    """Test changing bed allocation"""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543212"
    )
    
    # Create two beds
    bed1 = await bed_crud.create_bed(
        db=db_session,
        bed_number="G104",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    bed2 = await bed_crud.create_bed(
        db=db_session,
        bed_number="P101",
        ward_type=WardType.PRIVATE,
        per_day_charge=Decimal("1500.00")
    )
    
    # Admit patient to first bed
    ipd = await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=bed1.bed_id,
        file_charge=Decimal("1000.00")
    )
    
    # Change to second bed
    updated_ipd = await ipd_crud.change_bed(
        db=db_session,
        ipd_id=ipd.ipd_id,
        new_bed_id=bed2.bed_id
    )
    
    assert updated_ipd.bed_id == bed2.bed_id
    
    # Verify first bed is now available
    bed1_updated = await bed_crud.get_bed_by_id(db_session, bed1.bed_id)
    assert bed1_updated.status == BedStatus.AVAILABLE
    
    # Verify second bed is now occupied
    bed2_updated = await bed_crud.get_bed_by_id(db_session, bed2.bed_id)
    assert bed2_updated.status == BedStatus.OCCUPIED


@pytest.mark.asyncio
async def test_discharge_patient(db_session: AsyncSession):
    """Test discharging a patient"""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543213"
    )
    
    # Create bed
    bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="G105",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    # Admit patient
    ipd = await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=bed.bed_id,
        file_charge=Decimal("1000.00")
    )
    
    # Discharge patient
    discharged_ipd = await ipd_crud.discharge_patient(
        db=db_session,
        ipd_id=ipd.ipd_id
    )
    
    assert discharged_ipd.status == IPDStatus.DISCHARGED
    assert discharged_ipd.discharge_date is not None
    
    # Verify bed is now available
    bed_updated = await bed_crud.get_bed_by_id(db_session, bed.bed_id)
    assert bed_updated.status == BedStatus.AVAILABLE


@pytest.mark.asyncio
async def test_calculate_bed_charges(db_session: AsyncSession):
    """Test calculating bed charges"""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543214"
    )
    
    # Create bed
    bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="G106",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    # Admit patient 3 days ago
    admission_date = datetime.now() - timedelta(days=3)
    ipd = await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=bed.bed_id,
        file_charge=Decimal("1000.00"),
        admission_date=admission_date
    )
    
    # Calculate bed charges
    total_charges = await ipd_crud.calculate_bed_charges(
        db=db_session,
        ipd_id=ipd.ipd_id
    )
    
    # 3 days * 500 = 1500
    assert total_charges == Decimal("1500.00")


@pytest.mark.asyncio
async def test_get_available_beds(db_session: AsyncSession):
    """Test getting available beds"""
    # Create beds
    await bed_crud.create_bed(
        db=db_session,
        bed_number="G107",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    await bed_crud.create_bed(
        db=db_session,
        bed_number="P102",
        ward_type=WardType.PRIVATE,
        per_day_charge=Decimal("1500.00")
    )
    
    # Get all available beds
    available_beds = await bed_crud.get_available_beds(db_session)
    assert len(available_beds) >= 2
    
    # Get available general beds
    general_beds = await bed_crud.get_available_beds(db_session, WardType.GENERAL)
    assert all(bed.ward_type == WardType.GENERAL for bed in general_beds)


@pytest.mark.asyncio
async def test_bed_occupancy_stats(db_session: AsyncSession):
    """Test getting bed occupancy statistics"""
    # Create beds
    bed1 = await bed_crud.create_bed(
        db=db_session,
        bed_number="G108",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    bed2 = await bed_crud.create_bed(
        db=db_session,
        bed_number="G109",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    # Create patient and admit to one bed
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543215"
    )
    
    await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=bed1.bed_id,
        file_charge=Decimal("1000.00")
    )
    
    # Get occupancy stats
    stats = await bed_crud.get_bed_occupancy_stats(db_session)
    
    assert stats["total_beds"] >= 2
    assert stats["occupied"] >= 1
    assert stats["available"] >= 1
    assert "by_ward_type" in stats


@pytest.mark.asyncio
async def test_admit_to_occupied_bed_fails(db_session: AsyncSession):
    """Test that admitting to an occupied bed fails"""
    # Create patient 1
    patient1 = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient 1",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543216"
    )
    
    # Create patient 2
    patient2 = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient 2",
        age=25,
        gender=Gender.FEMALE,
        address="Test Address",
        mobile_number="9876543217"
    )
    
    # Create bed
    bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="G110",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    # Admit patient 1
    await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient1.patient_id,
        bed_id=bed.bed_id,
        file_charge=Decimal("1000.00")
    )
    
    # Try to admit patient 2 to same bed - should fail
    with pytest.raises(ValueError, match="not available"):
        await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient2.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )


@pytest.mark.asyncio
async def test_get_patient_ipd_history(db_session: AsyncSession):
    """Test getting patient IPD history"""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543218"
    )
    
    # Create beds
    bed1 = await bed_crud.create_bed(
        db=db_session,
        bed_number="G111",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    bed2 = await bed_crud.create_bed(
        db=db_session,
        bed_number="G112",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    # Admit patient twice
    ipd1 = await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=bed1.bed_id,
        file_charge=Decimal("1000.00")
    )
    
    # Discharge first admission
    await ipd_crud.discharge_patient(db_session, ipd1.ipd_id)
    
    # Second admission
    await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=bed2.bed_id,
        file_charge=Decimal("1000.00")
    )
    
    # Get all IPD history
    history = await ipd_crud.get_ipd_by_patient(db_session, patient.patient_id)
    assert len(history) == 2
    
    # Get only admitted
    admitted = await ipd_crud.get_ipd_by_patient(db_session, patient.patient_id, IPDStatus.ADMITTED)
    assert len(admitted) == 1
    assert admitted[0].status == IPDStatus.ADMITTED
