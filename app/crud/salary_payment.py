"""
CRUD operations for Salary Payment model
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.models.salary_payment import SalaryPayment, PaymentStatus
from app.models.employee import Employee
from app.services.id_generator import generate_id


class SalaryPaymentCRUD:
    """CRUD operations for Salary Payment model"""
    
    async def create_payment(
        self,
        db: AsyncSession,
        employee_id: str,
        month: int,
        year: int,
        amount: Decimal,
        status: PaymentStatus = PaymentStatus.PENDING,
        payment_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> SalaryPayment:
        """Create a new salary payment record"""
        # Validate employee exists
        result = await db.execute(
            select(Employee).where(Employee.employee_id == employee_id)
        )
        employee = result.scalar_one_or_none()
        if not employee:
            raise ValueError("Employee not found")
        
        # Validate month and year
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        
        if year < 2000 or year > 2100:
            raise ValueError("Invalid year")
        
        # Check if payment already exists for this employee, month, and year
        existing = await db.execute(
            select(SalaryPayment).where(
                and_(
                    SalaryPayment.employee_id == employee_id,
                    SalaryPayment.month == month,
                    SalaryPayment.year == year
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Payment record already exists for {month}/{year}")
        
        try:
            payment_id = await generate_id("SAL")
            
            payment = SalaryPayment(
                payment_id=payment_id,
                employee_id=employee_id,
                month=month,
                year=year,
                amount=Decimal(str(amount)).quantize(Decimal("0.01")),
                status=status,
                payment_date=payment_date,
                notes=notes
            )
            
            db.add(payment)
            await db.commit()
            await db.refresh(payment)
            return payment
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error creating salary payment")
    
    async def get_payment_by_id(
        self,
        db: AsyncSession,
        payment_id: str
    ) -> Optional[SalaryPayment]:
        """Get payment by ID with employee details"""
        result = await db.execute(
            select(SalaryPayment)
            .options(selectinload(SalaryPayment.employee))
            .where(SalaryPayment.payment_id == payment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_employee_payments(
        self,
        db: AsyncSession,
        employee_id: str,
        year: Optional[int] = None
    ) -> List[SalaryPayment]:
        """Get all payments for an employee, optionally filtered by year"""
        query = select(SalaryPayment).where(SalaryPayment.employee_id == employee_id)
        
        if year:
            query = query.where(SalaryPayment.year == year)
        
        query = query.order_by(SalaryPayment.year.desc(), SalaryPayment.month.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_pending_payments(
        self,
        db: AsyncSession,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> List[SalaryPayment]:
        """Get all pending payments, optionally filtered by month/year"""
        query = select(SalaryPayment).options(selectinload(SalaryPayment.employee)).where(
            SalaryPayment.status == PaymentStatus.PENDING
        )
        
        if month:
            query = query.where(SalaryPayment.month == month)
        if year:
            query = query.where(SalaryPayment.year == year)
        
        query = query.order_by(SalaryPayment.year.desc(), SalaryPayment.month.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_all_payments(
        self,
        db: AsyncSession,
        month: Optional[int] = None,
        year: Optional[int] = None,
        status: Optional[PaymentStatus] = None
    ) -> List[SalaryPayment]:
        """Get all payments with filters"""
        query = select(SalaryPayment).options(selectinload(SalaryPayment.employee))
        
        if month:
            query = query.where(SalaryPayment.month == month)
        if year:
            query = query.where(SalaryPayment.year == year)
        if status:
            query = query.where(SalaryPayment.status == status)
        
        query = query.order_by(SalaryPayment.year.desc(), SalaryPayment.month.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def mark_as_paid(
        self,
        db: AsyncSession,
        payment_id: str,
        payment_date: date,
        notes: Optional[str] = None
    ) -> Optional[SalaryPayment]:
        """Mark a payment as paid"""
        payment = await self.get_payment_by_id(db, payment_id)
        
        if not payment:
            return None
        
        payment.status = PaymentStatus.PAID
        payment.payment_date = payment_date
        if notes:
            payment.notes = notes
        
        await db.commit()
        await db.refresh(payment)
        return payment
    
    async def update_payment(
        self,
        db: AsyncSession,
        payment_id: str,
        amount: Optional[Decimal] = None,
        status: Optional[PaymentStatus] = None,
        payment_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> Optional[SalaryPayment]:
        """Update payment details"""
        payment = await self.get_payment_by_id(db, payment_id)
        
        if not payment:
            return None
        
        if amount is not None:
            payment.amount = Decimal(str(amount)).quantize(Decimal("0.01"))
        if status is not None:
            payment.status = status
        if payment_date is not None:
            payment.payment_date = payment_date
        if notes is not None:
            payment.notes = notes
        
        await db.commit()
        await db.refresh(payment)
        return payment


# Global instance
salary_payment_crud = SalaryPaymentCRUD()
