"""
Property-based tests for discharge bill generation and advance payment application

**Feature: hospital-management-system**

Property 15: Discharge Bill Completeness
Property 16: Advance Payment Application

**Validates: Requirements 6.1, 6.2, 11.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.crud.discharge import discharge_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.crud.billing import billing_crud
from app.crud.payment import payment_crud
from app.crud.ot import ot_crud
from app.models.patient import Gender
from app.models.visit import VisitType, PaymentMode
from app.models.bed import WardType
from app.models.billing import ChargeType
from app.models.payment import PaymentType


def generate_unique_mobile():
    """Generate a unique 10-digit mobile number starting with 9"""
    return "9" + str(uuid.uuid4().int)[:9]


# Strategies
charge_amount_strategy = st.decimals(
    min_value=100,
    max_value=10000,
    places=2,
    allow_nan=False,
    allow_infinity=False
)

payment_amount_strategy = st.decimals(
    min_value=500,
    max_value=5000,
    places=2,
    allow_nan=False,
    allow_infinity=False
)


class TestDischargeBillCompleteness:
    """Property 15: Discharge Bill Completeness"""
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        investigation_charge=charge_amount_strategy,
        procedure_charge=charge_amount_strategy
    )
    async def test_discharge_bill_includes_all_charge_types(
        self,
        db_session: AsyncSession,
        investigation_charge: Decimal,
        procedure_charge: Decimal
    ):
        """
        Property: Discharge bill should include all applicable charges
        (OPD, IPD, investigations, procedures, services, OT, manual)
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Test",
            department="General",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        # Create visit (OPD)
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
            bed_number=f"BED{generate_unique_mobile()[:6]}",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        # Admit patient to IPD
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00"),
            visit_id=visit.visit_id
        )
        
        # Add investigation charge
        investigation_charge = investigation_charge.quantize(Decimal("0.01"))
        await billing_crud.create_charge(
            db=db_session,
            ipd_id=ipd.ipd_id,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="X-Ray Chest",
            rate=investigation_charge,
            quantity=1,
            created_by="test_user"
        )
        
        # Add procedure charge
        procedure_charge = procedure_charge.quantize(Decimal("0.01"))
        await billing_crud.create_charge(
            db=db_session,
            ipd_id=ipd.ipd_id,
            charge_type=ChargeType.PROCEDURE,
            charge_name="Dressing",
            rate=procedure_charge,
            quantity=1,
            created_by="test_user"
        )
        
        # Add service charge
        service_charge = Decimal("200.00")
        await billing_crud.create_charge(
            db=db_session,
            ipd_id=ipd.ipd_id,
            charge_type=ChargeType.SERVICE,
            charge_name="Nursing Care",
            rate=service_charge,
            quantity=2,
            created_by="test_user"
        )
        
        # Add manual charge
        manual_charge = Decimal("150.00")
        await billing_crud.create_charge(
            db=db_session,
            ipd_id=ipd.ipd_id,
            charge_type=ChargeType.MANUAL,
            charge_name="Miscellaneous",
            rate=manual_charge,
            quantity=1,
            created_by="test_user"
        )
        
        # Add OT procedure and charges
        from datetime import datetime
        ot_procedure = await ot_crud.create_ot_procedure(
            db=db_session,
            ipd_id=ipd.ipd_id,
            operation_name="Appendectomy",
            operation_date=datetime.now(),
            duration_minutes=120,
            surgeon_name="Dr. Surgeon",
            created_by="test_user"
        )
        
        # Add OT charges to billing
        await ot_crud.add_ot_charges(
            db=db_session,
            ipd_id=ipd.ipd_id,
            ot_id=ot_procedure.ot_id,
            surgeon_charge=Decimal("5000.00"),
            anesthesia_charge=Decimal("2000.00"),
            facility_charge=Decimal("1000.00"),
            assistant_charge=Decimal("500.00"),
            created_by="test_user"
        )
        
        # Generate discharge bill
        discharge_bill = await discharge_crud.generate_discharge_bill(
            db=db_session,
            ipd_id=ipd.ipd_id
        )
        
        # Verify all charge types are present in the bill
        charges_by_type = discharge_bill["charges_by_type"]
        
        # Verify OPD fee is included
        assert "OPD_FEE" in charges_by_type
        assert len(charges_by_type["OPD_FEE"]) > 0
        assert charges_by_type["OPD_FEE"][0]["total"] == float(visit.opd_fee)
        
        # Verify IPD file charge is included
        assert "FILE_CHARGE" in charges_by_type
        assert len(charges_by_type["FILE_CHARGE"]) > 0
        assert charges_by_type["FILE_CHARGE"][0]["total"] == float(ipd.file_charge)
        
        # Verify investigation charge is included
        assert "INVESTIGATION" in charges_by_type
        assert len(charges_by_type["INVESTIGATION"]) > 0
        assert charges_by_type["INVESTIGATION"][0]["total"] == float(investigation_charge)
        
        # Verify procedure charge is included
        assert "PROCEDURE" in charges_by_type
        assert len(charges_by_type["PROCEDURE"]) > 0
        assert charges_by_type["PROCEDURE"][0]["total"] == float(procedure_charge)
        
        # Verify service charge is included
        assert "SERVICE" in charges_by_type
        assert len(charges_by_type["SERVICE"]) > 0
        assert charges_by_type["SERVICE"][0]["total"] == float(service_charge * 2)
        
        # Verify manual charge is included
        assert "MANUAL" in charges_by_type
        assert len(charges_by_type["MANUAL"]) > 0
        assert charges_by_type["MANUAL"][0]["total"] == float(manual_charge)
        
        # Verify OT charge is included (OT charges are stored as separate billing records)
        assert "OT" in charges_by_type
        assert len(charges_by_type["OT"]) == 4  # surgeon, anesthesia, facility, assistant
        ot_total_from_bill = sum(Decimal(str(charge["total"])) for charge in charges_by_type["OT"])
        ot_total = Decimal("5000.00") + Decimal("2000.00") + Decimal("1000.00") + Decimal("500.00")
        assert ot_total_from_bill == ot_total
        
        # Verify total charges calculation
        expected_total = (
            visit.opd_fee +
            ipd.file_charge +
            investigation_charge +
            procedure_charge +
            (service_charge * 2) +
            manual_charge +
            ot_total
        )
        
        assert Decimal(str(discharge_bill["summary"]["total_charges"])) == expected_total.quantize(Decimal("0.01"))
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(charge_amount=charge_amount_strategy)
    async def test_discharge_bill_without_opd_visit(
        self,
        db_session: AsyncSession,
        charge_amount: Decimal
    ):
        """
        Property: Discharge bill should work correctly for direct IPD admission
        (without OPD visit)
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        # Admit patient directly to IPD (no visit)
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Add a charge
        charge_amount = charge_amount.quantize(Decimal("0.01"))
        await billing_crud.create_charge(
            db=db_session,
            ipd_id=ipd.ipd_id,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="Blood Test",
            rate=charge_amount,
            quantity=1,
            created_by="test_user"
        )
        
        # Generate discharge bill
        discharge_bill = await discharge_crud.generate_discharge_bill(
            db=db_session,
            ipd_id=ipd.ipd_id
        )
        
        # Verify OPD fee is NOT included
        assert "OPD_FEE" not in discharge_bill["charges_by_type"]
        
        # Verify IPD file charge is included
        assert "FILE_CHARGE" in discharge_bill["charges_by_type"]
        
        # Verify investigation charge is included
        assert "INVESTIGATION" in discharge_bill["charges_by_type"]
        
        # Verify total charges
        expected_total = ipd.file_charge + charge_amount
        assert Decimal(str(discharge_bill["summary"]["total_charges"])) == expected_total.quantize(Decimal("0.01"))


class TestAdvancePaymentApplication:
    """Property 16: Advance Payment Application"""
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        advance_payment=payment_amount_strategy,
        charge_amount=charge_amount_strategy
    )
    async def test_net_payable_equals_charges_minus_advance(
        self,
        db_session: AsyncSession,
        advance_payment: Decimal,
        charge_amount: Decimal
    ):
        """
        Property: Net payable amount should equal total charges minus advance payments
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        # Admit patient to IPD
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Record advance payment
        advance_payment = advance_payment.quantize(Decimal("0.01"))
        await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=advance_payment,
            payment_mode="CASH",
            created_by="test_user"
        )
        
        # Add charges
        charge_amount = charge_amount.quantize(Decimal("0.01"))
        await billing_crud.create_charge(
            db=db_session,
            ipd_id=ipd.ipd_id,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="CT Scan",
            rate=charge_amount,
            quantity=1,
            created_by="test_user"
        )
        
        # Generate discharge bill
        discharge_bill = await discharge_crud.generate_discharge_bill(
            db=db_session,
            ipd_id=ipd.ipd_id
        )
        
        # Calculate expected values
        total_charges = ipd.file_charge + charge_amount
        expected_balance = total_charges - advance_payment
        
        # Verify advance payment is recorded
        assert Decimal(str(discharge_bill["summary"]["advance_paid"])) == advance_payment
        
        # Verify total paid equals advance
        assert Decimal(str(discharge_bill["summary"]["total_paid"])) == advance_payment
        
        # Verify balance due = total charges - advance payment
        assert Decimal(str(discharge_bill["summary"]["balance_due"])) == expected_balance.quantize(Decimal("0.01"))
        
        # Verify the equation: balance_due = total_charges - total_paid
        assert (
            Decimal(str(discharge_bill["summary"]["balance_due"])) ==
            Decimal(str(discharge_bill["summary"]["total_charges"])) - Decimal(str(discharge_bill["summary"]["total_paid"]))
        )
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        advance1=payment_amount_strategy,
        advance2=payment_amount_strategy,
        charge_amount=charge_amount_strategy
    )
    async def test_multiple_advance_payments_applied_correctly(
        self,
        db_session: AsyncSession,
        advance1: Decimal,
        advance2: Decimal,
        charge_amount: Decimal
    ):
        """
        Property: Multiple advance payments should be summed and applied correctly
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        # Admit patient to IPD
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Record first advance payment
        advance1 = advance1.quantize(Decimal("0.01"))
        await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=advance1,
            payment_mode="CASH",
            created_by="test_user"
        )
        
        # Record second advance payment
        advance2 = advance2.quantize(Decimal("0.01"))
        await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=advance2,
            payment_mode="UPI",
            created_by="test_user"
        )
        
        # Add charges
        charge_amount = charge_amount.quantize(Decimal("0.01"))
        await billing_crud.create_charge(
            db=db_session,
            ipd_id=ipd.ipd_id,
            charge_type=ChargeType.PROCEDURE,
            charge_name="Minor Surgery",
            rate=charge_amount,
            quantity=1,
            created_by="test_user"
        )
        
        # Generate discharge bill
        discharge_bill = await discharge_crud.generate_discharge_bill(
            db=db_session,
            ipd_id=ipd.ipd_id
        )
        
        # Calculate expected values
        total_advances = advance1 + advance2
        total_charges = ipd.file_charge + charge_amount
        expected_balance = total_charges - total_advances
        
        # Verify total advance paid
        assert Decimal(str(discharge_bill["summary"]["advance_paid"])) == total_advances.quantize(Decimal("0.01"))
        
        # Verify total paid equals sum of advances
        assert Decimal(str(discharge_bill["summary"]["total_paid"])) == total_advances.quantize(Decimal("0.01"))
        
        # Verify balance due
        assert Decimal(str(discharge_bill["summary"]["balance_due"])) == expected_balance.quantize(Decimal("0.01"))
        
        # Verify payment details include both payments
        assert len(discharge_bill["payments"]) == 2
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(advance_payment=payment_amount_strategy)
    async def test_advance_exceeds_charges_shows_negative_balance(
        self,
        db_session: AsyncSession,
        advance_payment: Decimal
    ):
        """
        Property: When advance payment exceeds charges, balance should be negative
        (indicating refund due)
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        # Admit patient to IPD with minimal charges
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("100.00")  # Small file charge
        )
        
        # Record large advance payment
        advance_payment = advance_payment.quantize(Decimal("0.01"))
        # Ensure advance is larger than file charge
        if advance_payment <= Decimal("100.00"):
            advance_payment = Decimal("5000.00")
        
        await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=advance_payment,
            payment_mode="CASH",
            created_by="test_user"
        )
        
        # Generate discharge bill (no additional charges)
        discharge_bill = await discharge_crud.generate_discharge_bill(
            db=db_session,
            ipd_id=ipd.ipd_id
        )
        
        # Calculate expected values
        total_charges = ipd.file_charge
        expected_balance = total_charges - advance_payment
        
        # Verify balance is negative (refund due)
        assert Decimal(str(discharge_bill["summary"]["balance_due"])) == expected_balance.quantize(Decimal("0.01"))
        assert Decimal(str(discharge_bill["summary"]["balance_due"])) < Decimal("0.00")
        
        # Verify advance paid is recorded correctly
        assert Decimal(str(discharge_bill["summary"]["advance_paid"])) == advance_payment
