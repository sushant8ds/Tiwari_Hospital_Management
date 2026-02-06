"""
Tests for billing CRUD operations
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.crud.billing import billing_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.models.patient import Gender
from app.models.doctor import DoctorStatus
from app.models.visit import VisitType, PaymentMode
from app.models.billing import ChargeType


@pytest.mark.asyncio
async def test_create_investigation_charge(db_session):
    """Test creating an investigation charge"""
    # Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543210"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Create investigation charge
    charge = await billing_crud.create_charge(
        db=db_session,
        charge_type=ChargeType.INVESTIGATION,
        charge_name="X-Ray Chest",
        rate=Decimal("500.00"),
        quantity=1,
        visit_id=visit.visit_id,
        created_by="test_user"
    )
    
    assert charge.charge_id is not None
    assert charge.charge_name == "X-Ray Chest"
    assert charge.rate == Decimal("500.00")
    assert charge.quantity == 1
    assert charge.total_amount == Decimal("500.00")
    assert charge.charge_type == ChargeType.INVESTIGATION


@pytest.mark.asyncio
async def test_create_procedure_charge(db_session):
    """Test creating a procedure charge"""
    # Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543211"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="Surgery",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Create procedure charge
    charge = await billing_crud.create_charge(
        db=db_session,
        charge_type=ChargeType.PROCEDURE,
        charge_name="Dressing",
        rate=Decimal("200.00"),
        quantity=2,
        visit_id=visit.visit_id,
        created_by="test_user"
    )
    
    assert charge.charge_id is not None
    assert charge.charge_name == "Dressing"
    assert charge.rate == Decimal("200.00")
    assert charge.quantity == 2
    assert charge.total_amount == Decimal("400.00")
    assert charge.charge_type == ChargeType.PROCEDURE


@pytest.mark.asyncio
async def test_add_multiple_investigation_charges(db_session):
    """Test adding multiple investigation charges"""
    # Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543212"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="General",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Add multiple investigations
    investigations = [
        {"name": "X-Ray", "rate": 500.00, "quantity": 1},
        {"name": "ECG", "rate": 300.00, "quantity": 1},
        {"name": "Blood Test", "rate": 400.00, "quantity": 1}
    ]
    
    charges = await billing_crud.add_investigation_charges(
        db=db_session,
        visit_id=visit.visit_id,
        ipd_id=None,
        investigations=investigations,
        created_by="test_user"
    )
    
    assert len(charges) == 3
    assert all(charge.charge_type == ChargeType.INVESTIGATION for charge in charges)
    
    # Verify total
    total = sum(charge.total_amount for charge in charges)
    assert total == Decimal("1200.00")


@pytest.mark.asyncio
async def test_add_service_charges_with_time_calculation(db_session):
    """Test adding service charges with automatic time calculation"""
    # Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543213"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="Emergency",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Add service with time calculation (5 hours)
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=5)
    
    services = [
        {
            "name": "Oxygen",
            "rate": 100.00,
            "start_time": start_time,
            "end_time": end_time
        }
    ]
    
    charges = await billing_crud.add_service_charges(
        db=db_session,
        visit_id=visit.visit_id,
        ipd_id=None,
        services=services,
        created_by="test_user"
    )
    
    assert len(charges) == 1
    assert charges[0].quantity == 5  # 5 hours
    assert charges[0].total_amount == Decimal("500.00")  # 5 * 100


@pytest.mark.asyncio
async def test_add_service_charges_with_partial_hours(db_session):
    """Test service charges with partial hours (should round up)"""
    # Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543214"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="Emergency",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Add service with 3.5 hours (should round to 4)
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=3, minutes=30)
    
    services = [
        {
            "name": "Nursing Care",
            "rate": 150.00,
            "start_time": start_time,
            "end_time": end_time
        }
    ]
    
    charges = await billing_crud.add_service_charges(
        db=db_session,
        visit_id=visit.visit_id,
        ipd_id=None,
        services=services,
        created_by="test_user"
    )
    
    assert len(charges) == 1
    assert charges[0].quantity == 4  # Rounded up from 3.5
    assert charges[0].total_amount == Decimal("600.00")  # 4 * 150


@pytest.mark.asyncio
async def test_get_charges_by_visit(db_session):
    """Test retrieving all charges for a visit"""
    # Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543215"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="General",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Add various charges
    await billing_crud.create_charge(
        db=db_session,
        charge_type=ChargeType.INVESTIGATION,
        charge_name="X-Ray",
        rate=Decimal("500.00"),
        quantity=1,
        visit_id=visit.visit_id,
        created_by="test_user"
    )
    
    await billing_crud.create_charge(
        db=db_session,
        charge_type=ChargeType.PROCEDURE,
        charge_name="Dressing",
        rate=Decimal("200.00"),
        quantity=1,
        visit_id=visit.visit_id,
        created_by="test_user"
    )
    
    # Get all charges
    charges = await billing_crud.get_charges_by_visit(db_session, visit.visit_id)
    
    assert len(charges) == 2
    assert any(c.charge_name == "X-Ray" for c in charges)
    assert any(c.charge_name == "Dressing" for c in charges)


@pytest.mark.asyncio
async def test_calculate_total_charges(db_session):
    """Test calculating total charges for a visit"""
    # Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543216"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="General",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Add charges
    await billing_crud.create_charge(
        db=db_session,
        charge_type=ChargeType.INVESTIGATION,
        charge_name="X-Ray",
        rate=Decimal("500.00"),
        quantity=1,
        visit_id=visit.visit_id,
        created_by="test_user"
    )
    
    await billing_crud.create_charge(
        db=db_session,
        charge_type=ChargeType.PROCEDURE,
        charge_name="Dressing",
        rate=Decimal("200.00"),
        quantity=2,
        visit_id=visit.visit_id,
        created_by="test_user"
    )
    
    # Calculate total
    total = await billing_crud.calculate_total_charges(db_session, visit_id=visit.visit_id)
    
    assert total == Decimal("900.00")  # 500 + (200 * 2)


@pytest.mark.asyncio
async def test_update_charge(db_session):
    """Test updating a billing charge"""
    # Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543217"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="General",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Create charge
    charge = await billing_crud.create_charge(
        db=db_session,
        charge_type=ChargeType.INVESTIGATION,
        charge_name="X-Ray",
        rate=Decimal("500.00"),
        quantity=1,
        visit_id=visit.visit_id,
        created_by="test_user"
    )
    
    # Update charge
    updated_charge = await billing_crud.update_charge(
        db=db_session,
        charge_id=charge.charge_id,
        rate=Decimal("600.00"),
        quantity=2
    )
    
    assert updated_charge.rate == Decimal("600.00")
    assert updated_charge.quantity == 2
    assert updated_charge.total_amount == Decimal("1200.00")


@pytest.mark.asyncio
async def test_create_charge_without_visit_or_ipd_fails(db_session):
    """Test that creating a charge without visit_id or ipd_id fails"""
    with pytest.raises(ValueError, match="Either visit_id or ipd_id must be provided"):
        await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="X-Ray",
            rate=Decimal("500.00"),
            quantity=1,
            created_by="test_user"
        )


@pytest.mark.asyncio
async def test_create_charge_with_invalid_visit_fails(db_session):
    """Test that creating a charge with invalid visit_id fails"""
    with pytest.raises(ValueError, match="Visit not found"):
        await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="X-Ray",
            rate=Decimal("500.00"),
            quantity=1,
            visit_id="INVALID_VISIT_ID",
            created_by="test_user"
        )


@pytest.mark.asyncio
async def test_create_charge_with_negative_rate_fails(db_session):
    """Test that creating a charge with negative rate fails"""
    # Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543218"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="General",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    with pytest.raises(ValueError, match="Rate cannot be negative"):
        await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="X-Ray",
            rate=Decimal("-500.00"),
            quantity=1,
            visit_id=visit.visit_id,
            created_by="test_user"
        )


@pytest.mark.asyncio
async def test_create_charge_with_zero_quantity_fails(db_session):
    """Test that creating a charge with zero quantity fails"""
    # Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543219"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="General",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    with pytest.raises(ValueError, match="Quantity must be positive"):
        await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="X-Ray",
            rate=Decimal("500.00"),
            quantity=0,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
