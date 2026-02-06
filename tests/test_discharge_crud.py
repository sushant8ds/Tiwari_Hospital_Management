"""
Unit tests for discharge CRUD operations
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.discharge import discharge_crud
from app.crud.patient import patient_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.crud.billing import billing_crud
from app.crud.payment import payment_crud
from app.models.patient import Gender
from app.models.bed import WardType
from app.models.billing import ChargeType
from app.models.payment import PaymentType


@pytest.mark.asyncio
async def test_generate_discharge_bill(db_session: AsyncSession):
    """Test generating discharge bill"""
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
        bed_number="BED001",
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
    
    # Add some charges
    await billing_crud.create_charge(
        db=db_session,
        ipd_id=ipd.ipd_id,
        charge_type=ChargeType.INVESTIGATION,
        charge_name="X-Ray",
        rate=Decimal("500.00"),
        quantity=1,
        created_by="test_user"
    )
    
    # Add payment
    await payment_crud.record_advance_payment(
        db=db_session,
        ipd_id=ipd.ipd_id,
        amount=Decimal("1000.00"),
        payment_mode="CASH",
        created_by="test_user"
    )
    
    # Generate discharge bill
    bill = await discharge_crud.generate_discharge_bill(db_session, ipd.ipd_id)
    
    # Verify bill structure
    assert bill is not None
    assert bill["ipd_id"] == ipd.ipd_id
    assert "patient" in bill
    assert bill["patient"]["id"] == patient.patient_id
    assert "admission" in bill
    assert "charges_by_type" in bill
    assert "payments" in bill
    assert "summary" in bill
    
    # Verify summary
    assert bill["summary"]["total_charges"] == 1500.00  # 1000 file + 500 investigation
    assert bill["summary"]["total_paid"] == 1000.00
    assert bill["summary"]["advance_paid"] == 1000.00
    assert bill["summary"]["balance_due"] == 500.00


@pytest.mark.asyncio
async def test_process_discharge(db_session: AsyncSession):
    """Test processing discharge"""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543211"
    )
    
    # Create bed
    bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="BED002",
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
    
    # Process discharge
    discharged_ipd = await discharge_crud.process_discharge(
        db=db_session,
        ipd_id=ipd.ipd_id
    )
    
    # Verify discharge
    assert discharged_ipd is not None
    assert discharged_ipd.discharge_date is not None
    assert discharged_ipd.status.value == "DISCHARGED"


@pytest.mark.asyncio
async def test_calculate_pending_amount(db_session: AsyncSession):
    """Test calculating pending amount"""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543212"
    )
    
    # Create bed
    bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="BED003",
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
    
    # Add charges
    await billing_crud.create_charge(
        db=db_session,
        ipd_id=ipd.ipd_id,
        charge_type=ChargeType.INVESTIGATION,
        charge_name="Blood Test",
        rate=Decimal("300.00"),
        quantity=1,
        created_by="test_user"
    )
    
    # Add partial payment
    await payment_crud.record_advance_payment(
        db=db_session,
        ipd_id=ipd.ipd_id,
        amount=Decimal("500.00"),
        payment_mode="CASH",
        created_by="test_user"
    )
    
    # Calculate pending amount
    pending = await discharge_crud.calculate_pending_amount(db_session, ipd.ipd_id)
    
    # Verify pending amount
    assert pending == Decimal("800.00")  # 1000 + 300 - 500
