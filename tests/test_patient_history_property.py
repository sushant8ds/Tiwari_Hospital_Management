"""
Property-based tests for patient history completeness

**Feature: hospital-management-system, Property 19: Patient History Completeness**

**Validates: Requirements 13.2, 13.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.crud.reports import reports_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.crud.billing import billing_crud
from app.crud.payment import payment_crud
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
    max_value=5000,
    places=2,
    allow_nan=False,
    allow_infinity=False
)

payment_amount_strategy = st.decimals(
    min_value=500,
    max_value=3000,
    places=2,
    allow_nan=False,
    allow_infinity=False
)


class TestPatientHistoryCompleteness:
    """Property 19: Patient History Completeness"""
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        investigation_charge=charge_amount_strategy,
        procedure_charge=charge_amount_strategy
    )
    async def test_history_includes_all_visits(
        self,
        db_session: AsyncSession,
        investigation_charge: Decimal,
        procedure_charge: Decimal
    ):
        """
        Property: Patient history should include all visits with their charges
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
        
        # Create first visit (new patient)
        visit1 = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Add investigation charge to first visit
        investigation_charge = investigation_charge.quantize(Decimal("0.01"))
        await billing_crud.create_charge(
            db=db_session,
            visit_id=visit1.visit_id,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="Blood Test",
            rate=investigation_charge,
            quantity=1,
            created_by="test_user"
        )
        
        # Create second visit (follow-up)
        visit2 = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_FOLLOWUP,
            payment_mode=PaymentMode.UPI
        )
        
        # Add procedure charge to second visit
        procedure_charge = procedure_charge.quantize(Decimal("0.01"))
        await billing_crud.create_charge(
            db=db_session,
            visit_id=visit2.visit_id,
            charge_type=ChargeType.PROCEDURE,
            charge_name="Dressing",
            rate=procedure_charge,
            quantity=1,
            created_by="test_user"
        )
        
        # Get patient history
        history = await reports_crud.get_patient_history(
            db=db_session,
            patient_id=patient.patient_id
        )
        
        # Verify history is not None
        assert history is not None
        
        # Verify patient details are included
        assert history["patient"]["patient_id"] == patient.patient_id
        assert history["patient"]["name"] == patient.name
        assert history["patient"]["age"] == patient.age
        
        # Verify all visits are included
        assert len(history["visits"]) == 2
        
        # Verify first visit details
        visit1_data = next((v for v in history["visits"] if v["visit_id"] == visit1.visit_id), None)
        assert visit1_data is not None
        assert visit1_data["visit_type"] == VisitType.OPD_NEW.value
        assert visit1_data["opd_fee"] == float(visit1.opd_fee)
        assert len(visit1_data["charges"]) == 1
        assert visit1_data["charges"][0]["charge_type"] == ChargeType.INVESTIGATION.value
        assert visit1_data["charges"][0]["charge_name"] == "Blood Test"
        assert Decimal(str(visit1_data["charges"][0]["total_amount"])) == investigation_charge
        
        # Verify second visit details
        visit2_data = next((v for v in history["visits"] if v["visit_id"] == visit2.visit_id), None)
        assert visit2_data is not None
        assert visit2_data["visit_type"] == VisitType.OPD_FOLLOWUP.value
        assert visit2_data["opd_fee"] == float(visit2.opd_fee)
        assert len(visit2_data["charges"]) == 1
        assert visit2_data["charges"][0]["charge_type"] == ChargeType.PROCEDURE.value
        assert visit2_data["charges"][0]["charge_name"] == "Dressing"
        assert Decimal(str(visit2_data["charges"][0]["total_amount"])) == procedure_charge
        
        # Verify summary totals
        expected_total_charges = (
            visit1.opd_fee + investigation_charge +
            visit2.opd_fee + procedure_charge
        )
        assert Decimal(str(history["summary"]["total_charges"])) == expected_total_charges.quantize(Decimal("0.01"))
        assert history["summary"]["total_visits"] == 2
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        ipd_charge=charge_amount_strategy,
        payment_amount=payment_amount_strategy
    )
    async def test_history_includes_all_ipd_admissions(
        self,
        db_session: AsyncSession,
        ipd_charge: Decimal,
        payment_amount: Decimal
    ):
        """
        Property: Patient history should include all IPD admissions with their charges
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
        
        # Add charge to IPD
        ipd_charge = ipd_charge.quantize(Decimal("0.01"))
        await billing_crud.create_charge(
            db=db_session,
            ipd_id=ipd.ipd_id,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="CT Scan",
            rate=ipd_charge,
            quantity=1,
            created_by="test_user"
        )
        
        # Record payment
        payment_amount = payment_amount.quantize(Decimal("0.01"))
        await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=payment_amount,
            payment_mode="CASH",
            created_by="test_user"
        )
        
        # Get patient history
        history = await reports_crud.get_patient_history(
            db=db_session,
            patient_id=patient.patient_id
        )
        
        # Verify history is not None
        assert history is not None
        
        # Verify IPD admissions are included
        assert len(history["ipd_admissions"]) == 1
        
        # Verify IPD details
        ipd_data = history["ipd_admissions"][0]
        assert ipd_data["ipd_id"] == ipd.ipd_id
        assert ipd_data["file_charge"] == float(ipd.file_charge)
        assert ipd_data["status"] == ipd.status.value
        
        # Verify IPD charges are included
        assert len(ipd_data["charges"]) == 1
        assert ipd_data["charges"][0]["charge_type"] == ChargeType.INVESTIGATION.value
        assert ipd_data["charges"][0]["charge_name"] == "CT Scan"
        assert Decimal(str(ipd_data["charges"][0]["total_amount"])) == ipd_charge
        
        # Verify bed details are included
        assert ipd_data["bed"] is not None
        assert ipd_data["bed"]["bed_number"] == bed.bed_number
        assert ipd_data["bed"]["ward_type"] == bed.ward_type.value
        
        # Verify payments are included
        assert len(history["payments"]) == 1
        assert history["payments"][0]["payment_type"] == PaymentType.IPD_ADVANCE.value
        assert Decimal(str(history["payments"][0]["amount"])) == payment_amount
        assert history["payments"][0]["ipd_id"] == ipd.ipd_id
        
        # Verify summary totals
        expected_total_charges = ipd.file_charge + ipd_charge
        assert Decimal(str(history["summary"]["total_charges"])) == expected_total_charges.quantize(Decimal("0.01"))
        assert Decimal(str(history["summary"]["total_paid"])) == payment_amount
        assert history["summary"]["total_ipd_admissions"] == 1
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        visit_charge=charge_amount_strategy,
        ipd_charge=charge_amount_strategy,
        payment1=payment_amount_strategy,
        payment2=payment_amount_strategy
    )
    async def test_history_includes_all_services_and_payments(
        self,
        db_session: AsyncSession,
        visit_charge: Decimal,
        ipd_charge: Decimal,
        payment1: Decimal,
        payment2: Decimal
    ):
        """
        Property: Patient history should include all services (visits + IPD) and all payments
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
        
        # Create visit
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Add charge to visit
        visit_charge = visit_charge.quantize(Decimal("0.01"))
        await billing_crud.create_charge(
            db=db_session,
            visit_id=visit.visit_id,
            charge_type=ChargeType.SERVICE,
            charge_name="Consultation",
            rate=visit_charge,
            quantity=1,
            created_by="test_user"
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
        
        # Add charge to IPD
        ipd_charge = ipd_charge.quantize(Decimal("0.01"))
        await billing_crud.create_charge(
            db=db_session,
            ipd_id=ipd.ipd_id,
            charge_type=ChargeType.MANUAL,
            charge_name="Special Service",
            rate=ipd_charge,
            quantity=1,
            created_by="test_user"
        )
        
        # Record first payment (advance)
        payment1 = payment1.quantize(Decimal("0.01"))
        await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=payment1,
            payment_mode="CASH",
            created_by="test_user"
        )
        
        # Record second payment (advance)
        payment2 = payment2.quantize(Decimal("0.01"))
        await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=payment2,
            payment_mode="UPI",
            created_by="test_user"
        )
        
        # Get patient history
        history = await reports_crud.get_patient_history(
            db=db_session,
            patient_id=patient.patient_id
        )
        
        # Verify history is not None
        assert history is not None
        
        # Verify all visits are included
        assert len(history["visits"]) == 1
        assert history["visits"][0]["visit_id"] == visit.visit_id
        assert len(history["visits"][0]["charges"]) == 1
        
        # Verify all IPD admissions are included
        assert len(history["ipd_admissions"]) == 1
        assert history["ipd_admissions"][0]["ipd_id"] == ipd.ipd_id
        assert len(history["ipd_admissions"][0]["charges"]) == 1
        
        # Verify all payments are included
        assert len(history["payments"]) == 2
        payment_amounts = [Decimal(str(p["amount"])) for p in history["payments"]]
        assert payment1 in payment_amounts
        assert payment2 in payment_amounts
        
        # Verify summary calculations
        expected_total_charges = (
            visit.opd_fee + visit_charge +
            ipd.file_charge + ipd_charge
        )
        expected_total_paid = payment1 + payment2
        expected_balance = expected_total_charges - expected_total_paid
        
        assert Decimal(str(history["summary"]["total_charges"])) == expected_total_charges.quantize(Decimal("0.01"))
        assert Decimal(str(history["summary"]["total_paid"])) == expected_total_paid.quantize(Decimal("0.01"))
        assert Decimal(str(history["summary"]["balance_due"])) == expected_balance.quantize(Decimal("0.01"))
    
    @pytest.mark.asyncio
    async def test_history_for_patient_with_no_visits_or_ipd(
        self,
        db_session: AsyncSession
    ):
        """
        Property: Patient history should work correctly for patients with no visits or IPD
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
        
        # Get patient history
        history = await reports_crud.get_patient_history(
            db=db_session,
            patient_id=patient.patient_id
        )
        
        # Verify history is not None
        assert history is not None
        
        # Verify patient details are included
        assert history["patient"]["patient_id"] == patient.patient_id
        assert history["patient"]["name"] == patient.name
        
        # Verify empty lists for visits, IPD, and payments
        assert len(history["visits"]) == 0
        assert len(history["ipd_admissions"]) == 0
        assert len(history["payments"]) == 0
        
        # Verify summary shows zero values
        assert history["summary"]["total_visits"] == 0
        assert history["summary"]["total_ipd_admissions"] == 0
        assert Decimal(str(history["summary"]["total_charges"])) == Decimal("0.00")
        assert Decimal(str(history["summary"]["total_paid"])) == Decimal("0.00")
        assert Decimal(str(history["summary"]["balance_due"])) == Decimal("0.00")
