"""
CRUD operations for payment processing and tracking
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from app.models.payment import Payment, PaymentType, PaymentStatus
from app.models.patient import Patient
from app.models.visit import Visit
from app.models.ipd import IPD
from app.models.billing import BillingCharge
from app.services.id_generator import generate_id


class PaymentCrud:
    """CRUD operations for payments"""
    
    async def create_payment(
        self,
        db: AsyncSession,
        patient_id: str,
        amount: Decimal,
        payment_mode: str,
        payment_type: PaymentType,
        created_by: str,
        visit_id: Optional[str] = None,
        ipd_id: Optional[str] = None,
        transaction_reference: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Payment:
        """Create a new payment record"""
        # Validate patient exists
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        if not patient:
            raise ValueError("Patient not found")
        
        # Validate visit or IPD if provided
        if visit_id:
            visit_result = await db.execute(
                select(Visit).where(Visit.visit_id == visit_id)
            )
            visit = visit_result.scalar_one_or_none()
            if not visit:
                raise ValueError("Visit not found")
        
        if ipd_id:
            ipd_result = await db.execute(
                select(IPD).where(IPD.ipd_id == ipd_id)
            )
            ipd = ipd_result.scalar_one_or_none()
            if not ipd:
                raise ValueError("IPD record not found")
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Validate payment mode
        valid_modes = ['CASH', 'UPI', 'CARD']
        if payment_mode.upper() not in valid_modes:
            raise ValueError(f"Payment mode must be one of: {', '.join(valid_modes)}")
        
        try:
            # Generate payment ID
            payment_id = await generate_id("PAY")
            
            # Quantize amount to 2 decimal places
            amount = Decimal(str(amount)).quantize(Decimal("0.01"))
            
            # Create payment with local timestamp
            payment = Payment(
                payment_id=payment_id,
                patient_id=patient_id,
                visit_id=visit_id,
                ipd_id=ipd_id,
                payment_type=payment_type,
                amount=amount,
                payment_mode=payment_mode.upper(),
                payment_status=PaymentStatus.COMPLETED,
                transaction_reference=transaction_reference,
                notes=notes,
                payment_date=datetime.now(),  # Use local time instead of server default
                created_by=created_by
            )
            
            db.add(payment)
            await db.commit()
            await db.refresh(payment)
            
            return payment
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def record_advance_payment(
        self,
        db: AsyncSession,
        ipd_id: str,
        amount: Decimal,
        payment_mode: str,
        created_by: str,
        transaction_reference: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Payment:
        """Record an advance payment for IPD"""
        # Get IPD record
        ipd_result = await db.execute(
            select(IPD).where(IPD.ipd_id == ipd_id)
        )
        ipd = ipd_result.scalar_one_or_none()
        if not ipd:
            raise ValueError("IPD record not found")
        
        return await self.create_payment(
            db=db,
            patient_id=ipd.patient_id,
            amount=amount,
            payment_mode=payment_mode,
            payment_type=PaymentType.IPD_ADVANCE,
            created_by=created_by,
            ipd_id=ipd_id,
            transaction_reference=transaction_reference,
            notes=notes
        )
    
    async def get_payment_by_id(
        self,
        db: AsyncSession,
        payment_id: str
    ) -> Optional[Payment]:
        """Get payment by ID"""
        result = await db.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_payments_by_patient(
        self,
        db: AsyncSession,
        patient_id: str
    ) -> List[Payment]:
        """Get all payments for a patient"""
        result = await db.execute(
            select(Payment)
            .where(Payment.patient_id == patient_id)
            .order_by(Payment.payment_date.desc())
        )
        return result.scalars().all()
    
    async def get_payments_by_visit(
        self,
        db: AsyncSession,
        visit_id: str
    ) -> List[Payment]:
        """Get all payments for a visit"""
        result = await db.execute(
            select(Payment)
            .where(Payment.visit_id == visit_id)
            .order_by(Payment.payment_date.desc())
        )
        return result.scalars().all()
    
    async def get_payments_by_ipd(
        self,
        db: AsyncSession,
        ipd_id: str
    ) -> List[Payment]:
        """Get all payments for an IPD admission"""
        result = await db.execute(
            select(Payment)
            .where(Payment.ipd_id == ipd_id)
            .order_by(Payment.payment_date.desc())
        )
        return result.scalars().all()
    
    async def get_advance_payments(
        self,
        db: AsyncSession,
        ipd_id: str
    ) -> List[Payment]:
        """Get all advance payments for an IPD admission"""
        result = await db.execute(
            select(Payment)
            .where(
                Payment.ipd_id == ipd_id,
                Payment.payment_type == PaymentType.IPD_ADVANCE
            )
            .order_by(Payment.payment_date.desc())
        )
        return result.scalars().all()
    
    async def calculate_total_paid(
        self,
        db: AsyncSession,
        patient_id: Optional[str] = None,
        visit_id: Optional[str] = None,
        ipd_id: Optional[str] = None
    ) -> Decimal:
        """Calculate total amount paid"""
        query = select(func.sum(Payment.amount))
        
        if patient_id:
            query = query.where(Payment.patient_id == patient_id)
        elif visit_id:
            query = query.where(Payment.visit_id == visit_id)
        elif ipd_id:
            query = query.where(Payment.ipd_id == ipd_id)
        else:
            raise ValueError("Must provide patient_id, visit_id, or ipd_id")
        
        result = await db.execute(query)
        total = result.scalar()
        
        return Decimal(str(total)) if total else Decimal("0.00")
    
    async def calculate_patient_balance(
        self,
        db: AsyncSession,
        patient_id: str,
        visit_id: Optional[str] = None,
        ipd_id: Optional[str] = None
    ) -> dict:
        """Calculate patient balance (charges - payments)"""
        # Get total charges from billing
        charges_query = select(func.sum(BillingCharge.total_amount))
        
        if visit_id:
            charges_query = charges_query.where(BillingCharge.visit_id == visit_id)
        elif ipd_id:
            charges_query = charges_query.where(BillingCharge.ipd_id == ipd_id)
        else:
            charges_query = charges_query.where(
                (BillingCharge.visit_id.in_(
                    select(Visit.visit_id).where(Visit.patient_id == patient_id)
                )) |
                (BillingCharge.ipd_id.in_(
                    select(IPD.ipd_id).where(IPD.patient_id == patient_id)
                ))
            )
        
        charges_result = await db.execute(charges_query)
        total_charges = charges_result.scalar()
        total_charges = Decimal(str(total_charges)) if total_charges else Decimal("0.00")
        
        # Add OPD fee from visit if visit_id is provided
        if visit_id:
            visit_result = await db.execute(
                select(Visit).where(Visit.visit_id == visit_id)
            )
            visit = visit_result.scalar_one_or_none()
            if visit:
                total_charges += Decimal(str(visit.opd_fee))
        
        # Add file charge from IPD if ipd_id is provided
        if ipd_id:
            ipd_result = await db.execute(
                select(IPD).where(IPD.ipd_id == ipd_id)
            )
            ipd = ipd_result.scalar_one_or_none()
            if ipd:
                total_charges += Decimal(str(ipd.file_charge))
        
        # Get total payments
        total_paid = await self.calculate_total_paid(
            db=db,
            patient_id=patient_id if not (visit_id or ipd_id) else None,
            visit_id=visit_id,
            ipd_id=ipd_id
        )
        
        # Get advance payments for IPD
        advance_balance = Decimal("0.00")
        if ipd_id:
            advance_payments = await self.get_advance_payments(db, ipd_id)
            advance_balance = sum(p.amount for p in advance_payments)
        
        # Calculate balance
        balance_due = total_charges - total_paid
        
        return {
            "patient_id": patient_id,
            "total_charges": total_charges,
            "total_paid": total_paid,
            "balance_due": balance_due,
            "advance_balance": advance_balance
        }


    async def get_daily_collection(
        self,
        db: AsyncSession,
        date: Optional[datetime] = None
    ) -> Decimal:
        """Get total collection for a specific date (defaults to today)"""
        if date is None:
            date = datetime.now().date()
        else:
            date = date.date() if isinstance(date, datetime) else date
        
        # Query payments for the specified date
        result = await db.execute(
            select(func.sum(Payment.amount))
            .where(
                func.date(Payment.payment_date) == date,
                Payment.payment_status == PaymentStatus.COMPLETED
            )
        )
        total = result.scalar()
        
        return Decimal(str(total)) if total else Decimal("0.00")


# Create singleton instance
payment_crud = PaymentCrud()
