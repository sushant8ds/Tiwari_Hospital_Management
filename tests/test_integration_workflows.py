"""
Integration tests for complete hospital management workflows

Tests end-to-end workflows including:
- OPD registration to discharge
- IPD admission to discharge
- Payment processing and slip generation

**Validates: Requirements 6.4, 11.4, 12.2**
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.crud.billing import billing_crud
from app.crud.payment import payment_crud
from app.crud.slip import slip_crud
from app.crud.discharge import discharge_crud
from app.crud.ot import ot_crud
from app.models.patient import Gender
from app.models.visit import VisitType, PaymentMode
from app.models.bed import WardType
from app.models.billing import ChargeType
from app.models.slip import SlipType, PrinterFormat


@pytest.mark.asyncio
async def test_opd_registration_to_discharge_workflow(db_session: AsyncSession):
    """
    Test complete OPD workflow:
    1. Register new patient
    2. Create OPD visit
    3. Add investigation charges
    4. Process payment
    5. Generate slip
    """
    # Step 1: Register new patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="John Doe",
        age=35,
        gender=Gender.MALE,
        address="123 Main St",
        mobile_number="9876543210"
    )
    
    assert patient is not None
    assert patient.patient_id.startswith("P")
    assert patient.name == "John Doe"
    
    # Step 2: Create doctor and OPD visit
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Smith",
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
    
    assert visit is not None
    assert visit.visit_id.startswith("V")
    assert visit.opd_fee == doctor.new_patient_fee
    assert visit.serial_number == 1
    
    # Step 3: Add investigation charges
    investigation_charge = await billing_crud.create_charge(
        db=db_session,
        visit_id=visit.visit_id,
        charge_type=ChargeType.INVESTIGATION,
        charge_name="ECG",
        rate=Decimal("200.00"),
        quantity=1,
        created_by="test_user"
    )
    
    assert investigation_charge is not None
    assert investigation_charge.total_amount == Decimal("200.00")
    
    # Step 4: Process payment
    total_amount = visit.opd_fee + investigation_charge.total_amount
    payment = await payment_crud.create_payment(
        db=db_session,
        patient_id=patient.patient_id,
        visit_id=visit.visit_id,
        payment_type="OPD_FEE",
        amount=total_amount,
        payment_mode="CASH",
        created_by="test_user"
    )
    
    assert payment is not None
    assert payment.amount == total_amount
    
    # Step 5: Generate slip
    slip = await slip_crud.generate_opd_slip(
        db=db_session,
        visit_id=visit.visit_id,
        printer_format=PrinterFormat.A4,
        generated_by="test_user"
    )
    
    assert slip is not None
    assert slip.slip_type == SlipType.OPD
    assert slip.barcode_data is not None
    assert patient.patient_id in slip.barcode_data


@pytest.mark.asyncio
async def test_ipd_admission_to_discharge_workflow(db_session: AsyncSession):
    """
    Test complete IPD workflow:
    1. Register patient
    2. Create OPD visit
    3. Admit to IPD
    4. Add various charges (investigation, procedure, service, OT)
    5. Record advance payment
    6. Generate discharge bill
    7. Process final payment
    8. Generate discharge slip
    """
    # Step 1: Register patient
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Jane Smith",
        age=45,
        gender=Gender.FEMALE,
        address="456 Oak Ave",
        mobile_number="9123456789"
    )
    
    # Step 2: Create OPD visit
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Johnson",
        department="Surgery",
        new_patient_fee=Decimal("600.00"),
        followup_fee=Decimal("400.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Step 3: Admit to IPD
    bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="B101",
        ward_type=WardType.PRIVATE,
        per_day_charge=Decimal("1000.00")
    )
    
    ipd = await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=bed.bed_id,
        file_charge=Decimal("500.00"),
        visit_id=visit.visit_id
    )
    
    assert ipd is not None
    assert ipd.ipd_id.startswith("IPD")
    assert ipd.status.value == "ADMITTED"
    
    # Step 4a: Add investigation charges
    investigation = await billing_crud.create_charge(
        db=db_session,
        ipd_id=ipd.ipd_id,
        charge_type=ChargeType.INVESTIGATION,
        charge_name="Blood Test",
        rate=Decimal("500.00"),
        quantity=1,
        created_by="test_user"
    )
    
    # Step 4b: Add procedure charges
    procedure = await billing_crud.create_charge(
        db=db_session,
        ipd_id=ipd.ipd_id,
        charge_type=ChargeType.PROCEDURE,
        charge_name="Dressing",
        rate=Decimal("300.00"),
        quantity=2,
        created_by="test_user"
    )
    
    # Step 4c: Add service charges
    service = await billing_crud.create_charge(
        db=db_session,
        ipd_id=ipd.ipd_id,
        charge_type=ChargeType.SERVICE,
        charge_name="Nursing Care",
        rate=Decimal("200.00"),
        quantity=3,
        created_by="test_user"
    )
    
    # Step 4d: Add OT charges
    ot_procedure = await ot_crud.create_ot_procedure(
        db=db_session,
        ipd_id=ipd.ipd_id,
        operation_name="Appendectomy",
        operation_date=datetime.now(),
        duration_minutes=90,
        surgeon_name="Dr. Johnson",
        created_by="test_user"
    )
    
    await ot_crud.add_ot_charges(
        db=db_session,
        ipd_id=ipd.ipd_id,
        ot_id=ot_procedure.ot_id,
        surgeon_charge=Decimal("5000.00"),
        anesthesia_charge=Decimal("2000.00"),
        facility_charge=Decimal("1000.00"),
        created_by="test_user"
    )
    
    # Step 5: Record advance payment
    advance_payment = await payment_crud.record_advance_payment(
        db=db_session,
        ipd_id=ipd.ipd_id,
        amount=Decimal("5000.00"),
        payment_mode="CASH",
        created_by="test_user"
    )
    
    assert advance_payment is not None
    
    # Step 6: Generate discharge bill
    discharge_bill = await discharge_crud.generate_discharge_bill(
        db=db_session,
        ipd_id=ipd.ipd_id
    )
    
    assert discharge_bill is not None
    assert "summary" in discharge_bill
    assert "charges_by_type" in discharge_bill
    assert "payments" in discharge_bill
    
    # Verify bill includes all charges
    assert "OPD_FEE" in discharge_bill["charges_by_type"]
    assert "FILE_CHARGE" in discharge_bill["charges_by_type"]
    assert "INVESTIGATION" in discharge_bill["charges_by_type"]
    assert "PROCEDURE" in discharge_bill["charges_by_type"]
    assert "SERVICE" in discharge_bill["charges_by_type"]
    assert "OT" in discharge_bill["charges_by_type"]
    
    # Verify advance payment is applied
    assert Decimal(str(discharge_bill["summary"]["advance_paid"])) == Decimal("5000.00")
    assert Decimal(str(discharge_bill["summary"]["total_paid"])) == Decimal("5000.00")
    
    # Step 7: Process final payment
    balance_due = Decimal(str(discharge_bill["summary"]["balance_due"]))
    if balance_due > 0:
        final_payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            ipd_id=ipd.ipd_id,
            payment_type="DISCHARGE",
            amount=balance_due,
            payment_mode="CARD",
            created_by="test_user"
        )
        assert final_payment is not None
    
    # Step 8: Process discharge
    discharged_ipd = await ipd_crud.discharge_patient(
        db=db_session,
        ipd_id=ipd.ipd_id
    )
    
    assert discharged_ipd.status.value == "DISCHARGED"
    assert discharged_ipd.discharge_date is not None
    
    # Step 9: Generate discharge slip
    discharge_slip = await slip_crud.generate_discharge_slip(
        db=db_session,
        ipd_id=ipd.ipd_id,
        printer_format=PrinterFormat.A4,
        generated_by="test_user"
    )
    
    assert discharge_slip is not None
    assert discharge_slip.slip_type == SlipType.DISCHARGE
    assert discharge_slip.barcode_data is not None


@pytest.mark.asyncio
async def test_payment_processing_and_slip_generation_workflow(db_session: AsyncSession):
    """
    Test payment processing and slip generation workflow:
    1. Create patient and visit
    2. Add multiple charges
    3. Process partial payment
    4. Generate payment slip
    5. Process remaining payment
    6. Verify payment history
    """
    # Step 1: Create patient and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Bob Wilson",
        age=50,
        gender=Gender.MALE,
        address="789 Pine Rd",
        mobile_number="9234567890"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Brown",
        department="Orthopedics",
        new_patient_fee=Decimal("700.00"),
        followup_fee=Decimal("500.00")
    )
    
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.UPI
    )
    
    # Step 2: Add multiple charges
    charge1 = await billing_crud.create_charge(
        db=db_session,
        visit_id=visit.visit_id,
        charge_type=ChargeType.INVESTIGATION,
        charge_name="X-Ray",
        rate=Decimal("400.00"),
        quantity=1,
        created_by="test_user"
    )
    
    charge2 = await billing_crud.create_charge(
        db=db_session,
        visit_id=visit.visit_id,
        charge_type=ChargeType.PROCEDURE,
        charge_name="Bandaging",
        rate=Decimal("150.00"),
        quantity=1,
        created_by="test_user"
    )
    
    total_charges = visit.opd_fee + charge1.total_amount + charge2.total_amount
    
    # Step 3: Process partial payment
    partial_payment = await payment_crud.create_payment(
        db=db_session,
        patient_id=patient.patient_id,
        visit_id=visit.visit_id,
        payment_type="OPD_FEE",
        amount=Decimal("800.00"),
        payment_mode="CASH",
        created_by="test_user"
    )
    
    assert partial_payment is not None
    assert partial_payment.amount == Decimal("800.00")
    
    # Step 4: Generate investigation slip
    payment_slip = await slip_crud.generate_investigation_slip(
        db=db_session,
        visit_id=visit.visit_id,
        ipd_id=None,
        printer_format=PrinterFormat.THERMAL,
        generated_by="test_user"
    )
    
    assert payment_slip is not None
    assert payment_slip.slip_type == SlipType.INVESTIGATION
    
    # Step 5: Process remaining payment
    remaining_amount = total_charges - Decimal("800.00")
    if remaining_amount > 0:
        final_payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            visit_id=visit.visit_id,
            payment_type="OPD_FEE",
            amount=remaining_amount,
            payment_mode="UPI",
            created_by="test_user"
        )
        assert final_payment is not None
    
    # Step 6: Verify payment history
    payment_history = await payment_crud.get_payments_by_visit(
        db=db_session,
        visit_id=visit.visit_id
    )
    
    assert len(payment_history) >= 1
    total_paid = sum(p.amount for p in payment_history)
    assert total_paid >= Decimal("800.00")


@pytest.mark.asyncio
async def test_follow_up_visit_workflow(db_session: AsyncSession):
    """
    Test follow-up visit workflow:
    1. Create patient and initial visit
    2. Create follow-up visit
    3. Verify serial number increments
    4. Verify follow-up fee is applied
    """
    # Step 1: Create patient and initial visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Alice Cooper",
        age=28,
        gender=Gender.FEMALE,
        address="321 Elm St",
        mobile_number="9345678901"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Davis",
        department="Dermatology",
        new_patient_fee=Decimal("400.00"),
        followup_fee=Decimal("250.00")
    )
    
    initial_visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    assert initial_visit.serial_number == 1
    assert initial_visit.opd_fee == doctor.new_patient_fee
    
    # Step 2: Create follow-up visit
    followup_visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        visit_type=VisitType.OPD_FOLLOWUP,
        payment_mode=PaymentMode.CASH
    )
    
    # Step 3: Verify serial number increments
    assert followup_visit.serial_number == 2
    
    # Step 4: Verify follow-up fee is applied
    assert followup_visit.opd_fee == doctor.followup_fee
    assert followup_visit.opd_fee < initial_visit.opd_fee


@pytest.mark.asyncio
async def test_bed_change_workflow(db_session: AsyncSession):
    """
    Test bed change workflow during IPD:
    1. Admit patient to general ward
    2. Change to private ward
    3. Verify bed status updates
    4. Verify charges reflect bed change
    """
    # Step 1: Create patient and admit to general ward
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Charlie Brown",
        age=60,
        gender=Gender.MALE,
        address="654 Maple Dr",
        mobile_number="9456789012"
    )
    
    general_bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="G201",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    ipd = await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=general_bed.bed_id,
        file_charge=Decimal("300.00")
    )
    
    assert ipd.bed_id == general_bed.bed_id
    
    # Step 2: Create private bed and change
    private_bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="P301",
        ward_type=WardType.PRIVATE,
        per_day_charge=Decimal("1500.00")
    )
    
    updated_ipd = await ipd_crud.change_bed(
        db=db_session,
        ipd_id=ipd.ipd_id,
        new_bed_id=private_bed.bed_id
    )
    
    # Step 3: Verify bed status updates
    assert updated_ipd.bed_id == private_bed.bed_id
    
    # Verify old bed is available
    old_bed = await bed_crud.get_bed_by_id(db=db_session, bed_id=general_bed.bed_id)
    assert old_bed.status.value == "AVAILABLE"
    
    # Verify new bed is occupied
    new_bed = await bed_crud.get_bed_by_id(db=db_session, bed_id=private_bed.bed_id)
    assert new_bed.status.value == "OCCUPIED"


@pytest.mark.asyncio
async def test_error_handling_workflow(db_session: AsyncSession):
    """
    Test error handling in workflows:
    1. Attempt to admit to occupied bed
    2. Attempt to discharge non-existent IPD
    3. Attempt to add charges to invalid visit
    """
    # Setup: Create patient and bed
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9567890123"
    )
    
    bed = await bed_crud.create_bed(
        db=db_session,
        bed_number="T101",
        ward_type=WardType.GENERAL,
        per_day_charge=Decimal("500.00")
    )
    
    # Admit first patient
    ipd1 = await ipd_crud.admit_patient(
        db=db_session,
        patient_id=patient.patient_id,
        bed_id=bed.bed_id,
        file_charge=Decimal("300.00")
    )
    
    # Test 1: Attempt to admit to occupied bed
    patient2 = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient 2",
        age=35,
        gender=Gender.FEMALE,
        address="Test Address 2",
        mobile_number="9678901234"
    )
    
    with pytest.raises(Exception):
        await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient2.patient_id,
            bed_id=bed.bed_id,  # Same bed - should fail
            file_charge=Decimal("300.00")
        )
    
    # Test 2: Attempt to discharge non-existent IPD
    with pytest.raises(Exception):
        await ipd_crud.discharge_patient(
            db=db_session,
            ipd_id="IPD_NONEXISTENT"
        )
    
    # Test 3: Attempt to add charges to invalid visit
    with pytest.raises(Exception):
        await billing_crud.create_charge(
            db=db_session,
            visit_id="V_INVALID",
            charge_type=ChargeType.INVESTIGATION,
            charge_name="Test",
            rate=Decimal("100.00"),
            quantity=1,
            created_by="test_user"
        )
