"""
Property-based tests for payment recording immediacy

**Feature: hospital-management-system, Property 21: Payment Recording Immediacy**
**Validates: Requirements 11.2**

Property: For any payment transaction, patient balances and payment history should be 
updated immediately upon successful payment processing
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.crud.payment import payment_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.crud.billing import billing_crud
from app.models.patient import Gender
from app.models.visit import VisitType, PaymentMode
from app.models.bed import WardType
from app.models.payment import PaymentType
from app.models.billing import ChargeType


def generate_unique_mobile():
    """Generate a unique 10-digit mobile number starting with 9"""
    return "9" + str(uuid.uuid4().int)[:9]


# Strategy for generating valid payment modes
payment_mode_strategy = st.sampled_from(['CASH', 'UPI', 'CARD'])

# Strategy for generating payment amounts
payment_amount_strategy = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("50000.00"),
    places=2
)

# Strategy for generating charge amounts
charge_amount_strategy = st.decimals(
    min_value=Decimal("100.00"),
    max_value=Decimal("10000.00"),
    places=2
)


class TestPaymentRecordingImmediacy:
    """Property-based tests for payment recording immediacy"""
    
    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        payment_amount=payment_amount_strategy,
        payment_mode=payment_mode_strategy
    )
    async def test_balance_updated_immediately_after_payment(
        self,
        db_session: AsyncSession,
        payment_amount: Decimal,
        payment_mode: str
    ):
        """
        Property: Patient balance should be updated immediately after payment is recorded
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
        
        # Get initial balance (should be 0)
        initial_balance = await payment_crud.calculate_patient_balance(
            db=db_session,
            patient_id=patient.patient_id
        )
        assert initial_balance["balance_due"] == Decimal("0.00")
        
        # Create payment
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=payment_amount,
            payment_mode=payment_mode,
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user"
        )
        
        # Immediately check balance after payment
        updated_balance = await payment_crud.calculate_patient_balance(
            db=db_session,
            patient_id=patient.patient_id
        )
        
        # Verify balance is updated immediately
        assert updated_balance["total_paid"] == payment_amount
        assert updated_balance["balance_due"] == -payment_amount  # Negative because payment without charges
    
    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        payment_amount=payment_amount_strategy,
        payment_mode=payment_mode_strategy
    )
    async def test_payment_history_accessible_immediately(
        self,
        db_session: AsyncSession,
        payment_amount: Decimal,
        payment_mode: str
    ):
        """
        Property: Payment history should be immediately accessible after payment is recorded
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
        
        # Get initial payment history (should be empty)
        initial_history = await payment_crud.get_payments_by_patient(
            db=db_session,
            patient_id=patient.patient_id
        )
        assert len(initial_history) == 0
        
        # Create payment
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=payment_amount,
            payment_mode=payment_mode,
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user"
        )
        
        # Immediately retrieve payment history
        updated_history = await payment_crud.get_payments_by_patient(
            db=db_session,
            patient_id=patient.patient_id
        )
        
        # Verify payment is immediately in history
        assert len(updated_history) == 1
        assert updated_history[0].payment_id == payment.payment_id
        assert updated_history[0].amount == payment_amount
        assert updated_history[0].payment_mode == payment_mode

    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        charge_amount=charge_amount_strategy,
        payment_amount=payment_amount_strategy,
        payment_mode=payment_mode_strategy
    )
    async def test_balance_reflects_charges_and_payments_immediately(
        self,
        db_session: AsyncSession,
        charge_amount: Decimal,
        payment_amount: Decimal,
        payment_mode: str
    ):
        """
        Property: Balance should immediately reflect both charges and payments
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
            payment_mode=PaymentMode[payment_mode]
        )
        
        # Add a charge
        charge = await billing_crud.create_charge(
            db=db_session,
            visit_id=visit.visit_id,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="X-Ray",
            quantity=1,
            rate=charge_amount,
            created_by="test_user"
        )
        
        # Check balance after charge (should include OPD fee + charge)
        balance_after_charge = await payment_crud.calculate_patient_balance(
            db=db_session,
            patient_id=patient.patient_id,
            visit_id=visit.visit_id
        )
        expected_charges = Decimal(str(visit.opd_fee)) + charge_amount
        assert balance_after_charge["total_charges"] == expected_charges
        assert balance_after_charge["balance_due"] == expected_charges
        
        # Make a payment
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=payment_amount,
            payment_mode=payment_mode,
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user",
            visit_id=visit.visit_id
        )
        
        # Immediately check balance after payment
        balance_after_payment = await payment_crud.calculate_patient_balance(
            db=db_session,
            patient_id=patient.patient_id,
            visit_id=visit.visit_id
        )
        
        # Verify balance is updated immediately
        assert balance_after_payment["total_charges"] == expected_charges
        assert balance_after_payment["total_paid"] == payment_amount
        assert balance_after_payment["balance_due"] == expected_charges - payment_amount
    
    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        advance_amount=payment_amount_strategy,
        payment_mode=payment_mode_strategy
    )
    async def test_ipd_advance_balance_updated_immediately(
        self,
        db_session: AsyncSession,
        advance_amount: Decimal,
        payment_mode: str
    ):
        """
        Property: IPD advance balance should be updated immediately after advance payment
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
        
        # Admit patient
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Check initial balance
        initial_balance = await payment_crud.calculate_patient_balance(
            db=db_session,
            patient_id=patient.patient_id,
            ipd_id=ipd.ipd_id
        )
        assert initial_balance["advance_balance"] == Decimal("0.00")
        
        # Record advance payment
        payment = await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=advance_amount,
            payment_mode=payment_mode,
            created_by="test_user"
        )
        
        # Immediately check balance after advance payment
        updated_balance = await payment_crud.calculate_patient_balance(
            db=db_session,
            patient_id=patient.patient_id,
            ipd_id=ipd.ipd_id
        )
        
        # Verify advance balance is updated immediately
        assert updated_balance["advance_balance"] == advance_amount
        assert updated_balance["total_paid"] == advance_amount
    
    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_payments=st.integers(min_value=2, max_value=5),
        payment_mode=payment_mode_strategy
    )
    async def test_multiple_payments_updated_immediately(
        self,
        db_session: AsyncSession,
        num_payments: int,
        payment_mode: str
    ):
        """
        Property: Multiple sequential payments should all be reflected immediately in balance
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
        
        # Track total paid
        total_paid = Decimal("0.00")
        payment_ids = []
        
        # Make multiple payments
        for i in range(num_payments):
            payment_amount = Decimal(f"{(i + 1) * 100}.00")
            
            payment = await payment_crud.create_payment(
                db=db_session,
                patient_id=patient.patient_id,
                amount=payment_amount,
                payment_mode=payment_mode,
                payment_type=PaymentType.OPD_FEE,
                created_by="test_user"
            )
            
            total_paid += payment_amount
            payment_ids.append(payment.payment_id)
            
            # Immediately check balance after each payment
            current_balance = await payment_crud.calculate_patient_balance(
                db=db_session,
                patient_id=patient.patient_id
            )
            
            # Verify balance is updated immediately after each payment
            assert current_balance["total_paid"] == total_paid
            
            # Verify payment history includes all payments so far
            payment_history = await payment_crud.get_payments_by_patient(
                db=db_session,
                patient_id=patient.patient_id
            )
            assert len(payment_history) == i + 1
            
            # Verify all previous payment IDs are in history
            history_ids = [p.payment_id for p in payment_history]
            for payment_id in payment_ids:
                assert payment_id in history_ids
    
    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        payment_amount=payment_amount_strategy,
        payment_mode=payment_mode_strategy,
        payment_type=st.sampled_from([
            PaymentType.OPD_FEE,
            PaymentType.INVESTIGATION,
            PaymentType.PROCEDURE,
            PaymentType.SERVICE
        ])
    )
    async def test_payment_retrievable_by_id_immediately(
        self,
        db_session: AsyncSession,
        payment_amount: Decimal,
        payment_mode: str,
        payment_type: PaymentType
    ):
        """
        Property: Payment should be retrievable by ID immediately after creation
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
        
        # Create payment
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=payment_amount,
            payment_mode=payment_mode,
            payment_type=payment_type,
            created_by="test_user"
        )
        
        # Immediately retrieve payment by ID
        retrieved_payment = await payment_crud.get_payment_by_id(
            db=db_session,
            payment_id=payment.payment_id
        )
        
        # Verify payment is immediately retrievable with correct data
        assert retrieved_payment is not None
        assert retrieved_payment.payment_id == payment.payment_id
        assert retrieved_payment.amount == payment_amount
        assert retrieved_payment.payment_mode == payment_mode
        assert retrieved_payment.payment_type == payment_type
        assert retrieved_payment.patient_id == patient.patient_id
    
    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        charge_amount=charge_amount_strategy,
        payment_amount=payment_amount_strategy,
        payment_mode=payment_mode_strategy
    )
    async def test_visit_payment_history_updated_immediately(
        self,
        db_session: AsyncSession,
        charge_amount: Decimal,
        payment_amount: Decimal,
        payment_mode: str
    ):
        """
        Property: Visit-specific payment history should be updated immediately
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
            payment_mode=PaymentMode[payment_mode]
        )
        
        # Check initial visit payment history
        initial_history = await payment_crud.get_payments_by_visit(
            db=db_session,
            visit_id=visit.visit_id
        )
        assert len(initial_history) == 0
        
        # Create payment for visit
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=payment_amount,
            payment_mode=payment_mode,
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user",
            visit_id=visit.visit_id
        )
        
        # Immediately check visit payment history
        updated_history = await payment_crud.get_payments_by_visit(
            db=db_session,
            visit_id=visit.visit_id
        )
        
        # Verify payment is immediately in visit history
        assert len(updated_history) == 1
        assert updated_history[0].payment_id == payment.payment_id
        assert updated_history[0].visit_id == visit.visit_id
