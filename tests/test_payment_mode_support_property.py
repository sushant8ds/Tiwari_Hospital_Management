"""
Property-based tests for payment mode support

**Feature: hospital-management-system, Property 9: Payment Mode Support**
**Validates: Requirements 1.5, 11.1**

Property: For any payment processing operation, the system should accept and process 
Cash, UPI, and Card payment modes correctly
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
from app.models.patient import Gender
from app.models.visit import VisitType, PaymentMode
from app.models.bed import WardType
from app.models.payment import PaymentType


def generate_unique_mobile():
    """Generate a unique 10-digit mobile number starting with 9"""
    # Generate 9 random digits and prepend with 9 to make a valid Indian mobile number
    return "9" + str(uuid.uuid4().int)[:9]


# Strategy for generating valid payment modes
payment_mode_strategy = st.sampled_from(['CASH', 'UPI', 'CARD'])

# Strategy for generating payment amounts
payment_amount_strategy = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("100000.00"),
    places=2
)

# Strategy for generating payment types
payment_type_strategy = st.sampled_from([
    PaymentType.OPD_FEE,
    PaymentType.INVESTIGATION,
    PaymentType.PROCEDURE,
    PaymentType.SERVICE,
    PaymentType.IPD_ADVANCE,
    PaymentType.DISCHARGE
])


class TestPaymentModeSupport:
    """Property-based tests for payment mode support"""
    
    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        payment_mode=payment_mode_strategy,
        amount=payment_amount_strategy,
        payment_type=payment_type_strategy
    )
    async def test_all_payment_modes_accepted(
        self,
        db_session: AsyncSession,
        payment_mode: str,
        amount: Decimal,
        payment_type: PaymentType
    ):
        """
        Property: All valid payment modes (CASH, UPI, CARD) should be accepted
        for any payment processing operation
        """
        # Create patient with unique mobile number
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create payment with the given payment mode
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=amount,
            payment_mode=payment_mode,
            payment_type=payment_type,
            created_by="test_user"
        )
        
        # Verify payment was created successfully
        assert payment is not None
        assert payment.payment_id is not None
        assert payment.payment_mode == payment_mode
        assert payment.amount == amount
        assert payment.payment_type == payment_type
    
    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        payment_mode=payment_mode_strategy,
        amount=payment_amount_strategy
    )
    async def test_payment_mode_for_opd_visits(
        self,
        db_session: AsyncSession,
        payment_mode: str,
        amount: Decimal
    ):
        """
        Property: All payment modes should work correctly for OPD visit payments
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
        
        # Create visit with the payment mode
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode[payment_mode]
        )
        
        # Create payment for the visit
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=amount,
            payment_mode=payment_mode,
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user",
            visit_id=visit.visit_id
        )
        
        # Verify payment mode is correctly stored
        assert payment.payment_mode == payment_mode
        assert payment.visit_id == visit.visit_id
        assert visit.payment_mode.value == payment_mode
    
    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        payment_mode=payment_mode_strategy,
        amount=payment_amount_strategy
    )
    async def test_payment_mode_for_ipd_advance(
        self,
        db_session: AsyncSession,
        payment_mode: str,
        amount: Decimal
    ):
        """
        Property: All payment modes should work correctly for IPD advance payments
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
        
        # Create bed with unique bed number
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
        
        # Record advance payment with the payment mode
        payment = await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=amount,
            payment_mode=payment_mode,
            created_by="test_user"
        )
        
        # Verify payment mode is correctly stored
        assert payment.payment_mode == payment_mode
        assert payment.ipd_id == ipd.ipd_id
        assert payment.payment_type == PaymentType.IPD_ADVANCE
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        payment_mode=payment_mode_strategy,
        amount=payment_amount_strategy,
        has_transaction_ref=st.booleans()
    )
    async def test_payment_mode_with_transaction_reference(
        self,
        db_session: AsyncSession,
        payment_mode: str,
        amount: Decimal,
        has_transaction_ref: bool
    ):
        """
        Property: Payment modes should support optional transaction references
        (especially important for UPI and Card payments)
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
        
        # Generate transaction reference if needed
        transaction_ref = None
        if has_transaction_ref:
            if payment_mode == 'UPI':
                transaction_ref = f"UPI{str(hash(str(amount)))[-10:]}"
            elif payment_mode == 'CARD':
                transaction_ref = f"CARD{str(hash(str(amount)))[-10:]}"
            else:  # CASH
                transaction_ref = f"CASH{str(hash(str(amount)))[-10:]}"
        
        # Create payment
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=amount,
            payment_mode=payment_mode,
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user",
            transaction_reference=transaction_ref
        )
        
        # Verify payment was created with correct transaction reference
        assert payment.payment_mode == payment_mode
        assert payment.transaction_reference == transaction_ref
    
    @pytest.mark.asyncio
    async def test_invalid_payment_mode_rejected(self, db_session: AsyncSession):
        """
        Property: Invalid payment modes should be rejected
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543210"
        )
        
        # Try to create payment with invalid mode
        with pytest.raises(ValueError, match="Payment mode must be one of"):
            await payment_crud.create_payment(
                db=db_session,
                patient_id=patient.patient_id,
                amount=Decimal("500.00"),
                payment_mode="INVALID",
                payment_type=PaymentType.OPD_FEE,
                created_by="test_user"
            )
    
    @pytest.mark.asyncio
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        payment_mode=payment_mode_strategy,
        amount=payment_amount_strategy
    )
    async def test_payment_mode_case_insensitive(
        self,
        db_session: AsyncSession,
        payment_mode: str,
        amount: Decimal
    ):
        """
        Property: Payment modes should be case-insensitive (lowercase input should work)
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
        
        # Create payment with lowercase payment mode
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=amount,
            payment_mode=payment_mode.lower(),
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user"
        )
        
        # Verify payment mode is stored in uppercase
        assert payment.payment_mode == payment_mode.upper()
