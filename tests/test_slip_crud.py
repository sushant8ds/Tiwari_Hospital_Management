"""
Unit tests for slip CRUD operations
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.slip import slip_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.models.patient import Gender
from app.models.visit import VisitType, PaymentMode
from app.models.bed import WardType
from app.models.slip import PrinterFormat


@pytest.mark.asyncio
async def test_generate_opd_slip(db_session: AsyncSession):
    """Test generating OPD slip"""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543210"
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
    
    # Generate OPD slip
    slip = await slip_crud.generate_opd_slip(
        db=db_session,
        visit_id=visit.visit_id,
        printer_format=PrinterFormat.A4,
        generated_by="test_user"
    )
    
    # Verify slip
    assert slip is not None
    assert slip.slip_id is not None
    assert slip.patient_id == patient.patient_id
    assert slip.visit_id == visit.visit_id
    assert slip.slip_type.value == "OPD"
    assert slip.barcode_data is not None
    assert slip.barcode_image is not None
    assert slip.slip_content is not None
    assert slip.printer_format == PrinterFormat.A4
    assert slip.is_reprinted is False


@pytest.mark.asyncio
async def test_reprint_slip(db_session: AsyncSession):
    """Test reprinting a slip"""
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
    
    # Generate original slip
    original_slip = await slip_crud.generate_opd_slip(
        db=db_session,
        visit_id=visit.visit_id,
        printer_format=PrinterFormat.A4,
        generated_by="test_user"
    )
    
    # Reprint slip
    reprinted_slip = await slip_crud.reprint_slip(
        db=db_session,
        original_slip_id=original_slip.slip_id,
        generated_by="test_user"
    )
    
    # Verify reprinted slip
    assert reprinted_slip is not None
    assert reprinted_slip.slip_id != original_slip.slip_id
    assert reprinted_slip.patient_id == original_slip.patient_id
    assert reprinted_slip.visit_id == original_slip.visit_id
    assert reprinted_slip.slip_type == original_slip.slip_type
    assert reprinted_slip.barcode_data == original_slip.barcode_data
    assert reprinted_slip.is_reprinted is True
    assert reprinted_slip.original_slip_id == original_slip.slip_id


@pytest.mark.asyncio
async def test_get_slips_by_patient(db_session: AsyncSession):
    """Test getting all slips for a patient"""
    # Create patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543212"
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
    
    # Generate slip
    slip = await slip_crud.generate_opd_slip(
        db=db_session,
        visit_id=visit.visit_id,
        printer_format=PrinterFormat.A4,
        generated_by="test_user"
    )
    
    # Get slips by patient
    slips = await slip_crud.get_slips_by_patient(
        db=db_session,
        patient_id=patient.patient_id
    )
    
    # Verify
    assert len(slips) == 1
    assert slips[0].slip_id == slip.slip_id
