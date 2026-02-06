"""
Tests for payment CRUD operations
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.payment import payment_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.crud.billing import billing_crud
from app.models.patient import Gender
from app.models.doctor import DoctorStatus
from app.models.visit import VisitType, PaymentMode
from app.models.bed import WardType
from app.models.payment import PaymentType, PaymentStatus
from app.models.billing import ChargeType


class TestPaymentCrud:
    """Test payment CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_payment(self, db_session: AsyncSession):
        """Test creating a payment"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543210"
        )
        
        # Create payment
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=Decimal("500.00"),
            payment_mode="CASH",
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user"
        )
        
        assert payment.payment_id is not None
        assert payment.patient_id == patient.patient_id
        assert payment.amount == Decimal("500.00")
        assert payment.payment_mode == "CASH"
        assert payment.payment_type == PaymentType.OPD_FEE
        assert payment.payment_status == PaymentStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_create_payment_with_upi(self, db_session: AsyncSession):
        """Test creating a payment with UPI"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543211"
        )
        
        # Create payment with UPI
        payment = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=Decimal("1000.00"),
            payment_mode="UPI",
            payment_type=PaymentType.INVESTIGATION,
            created_by="test_user",
            transaction_reference="UPI123456789",
            notes="Payment via PhonePe"
        )
        
        assert payment.payment_mode == "UPI"
        assert payment.transaction_reference == "UPI123456789"
        assert payment.notes == "Payment via PhonePe"
    
    @pytest.mark.asyncio
    async def test_record_advance_payment(self, db_session: AsyncSession):
        """Test recording an advance payment for IPD"""
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
            bed_number="PAY001",
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
        
        # Record advance payment
        payment = await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=Decimal("5000.00"),
            payment_mode="CARD",
            created_by="test_user",
            transaction_reference="CARD987654321"
        )
        
        assert payment.ipd_id == ipd.ipd_id
        assert payment.payment_type == PaymentType.IPD_ADVANCE
        assert payment.amount == Decimal("5000.00")
        assert payment.payment_mode == "CARD"
    
    @pytest.mark.asyncio
    async def test_get_payments_by_patient(self, db_session: AsyncSession):
        """Test getting all payments for a patient"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543213"
        )
        
        # Create multiple payments
        payment1 = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=Decimal("500.00"),
            payment_mode="CASH",
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user"
        )
        
        payment2 = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=Decimal("1000.00"),
            payment_mode="UPI",
            payment_type=PaymentType.INVESTIGATION,
            created_by="test_user"
        )
        
        # Get all payments
        payments = await payment_crud.get_payments_by_patient(db_session, patient.patient_id)
        
        assert len(payments) == 2
        assert any(p.payment_id == payment1.payment_id for p in payments)
        assert any(p.payment_id == payment2.payment_id for p in payments)
    
    @pytest.mark.asyncio
    async def test_calculate_total_paid(self, db_session: AsyncSession):
        """Test calculating total amount paid"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543214"
        )
        
        # Create payments
        await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=Decimal("500.00"),
            payment_mode="CASH",
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user"
        )
        
        await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=Decimal("1500.00"),
            payment_mode="UPI",
            payment_type=PaymentType.INVESTIGATION,
            created_by="test_user"
        )
        
        # Calculate total
        total = await payment_crud.calculate_total_paid(
            db=db_session,
            patient_id=patient.patient_id
        )
        
        assert total == Decimal("2000.00")
    
    @pytest.mark.asyncio
    async def test_calculate_patient_balance(self, db_session: AsyncSession):
        """Test calculating patient balance"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543215"
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
        
        # Add charges
        await billing_crud.add_investigation_charges(
            db=db_session,
            visit_id=visit.visit_id,
            ipd_id=None,
            investigations=[
                {"name": "X-Ray", "quantity": 1, "rate": Decimal("500.00")}
            ],
            created_by="test_user"
        )
        
        # Add payment
        await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=Decimal("300.00"),
            payment_mode="CASH",
            payment_type=PaymentType.OPD_FEE,
            created_by="test_user",
            visit_id=visit.visit_id
        )
        
        # Calculate balance
        balance = await payment_crud.calculate_patient_balance(
            db=db_session,
            patient_id=patient.patient_id,
            visit_id=visit.visit_id
        )
        
        # Total charges: 500 (OPD fee) + 500 (X-Ray) = 1000
        # Total paid: 300
        # Balance due: 700
        assert balance["total_charges"] == Decimal("1000.00")
        assert balance["total_paid"] == Decimal("300.00")
        assert balance["balance_due"] == Decimal("700.00")
    
    @pytest.mark.asyncio
    async def test_get_advance_payments(self, db_session: AsyncSession):
        """Test getting advance payments for IPD"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543216"
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="PAY002",
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
        
        # Record multiple advance payments
        await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=Decimal("2000.00"),
            payment_mode="CASH",
            created_by="test_user"
        )
        
        await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=Decimal("3000.00"),
            payment_mode="UPI",
            created_by="test_user"
        )
        
        # Get advance payments
        advances = await payment_crud.get_advance_payments(db_session, ipd.ipd_id)
        
        assert len(advances) == 2
        total_advance = sum(p.amount for p in advances)
        assert total_advance == Decimal("5000.00")
    
    @pytest.mark.asyncio
    async def test_invalid_payment_mode(self, db_session: AsyncSession):
        """Test creating payment with invalid payment mode"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543217"
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
    async def test_negative_payment_amount(self, db_session: AsyncSession):
        """Test creating payment with negative amount"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543218"
        )
        
        # Try to create payment with negative amount
        with pytest.raises(ValueError, match="Amount must be positive"):
            await payment_crud.create_payment(
                db=db_session,
                patient_id=patient.patient_id,
                amount=Decimal("-500.00"),
                payment_mode="CASH",
                payment_type=PaymentType.OPD_FEE,
                created_by="test_user"
            )
