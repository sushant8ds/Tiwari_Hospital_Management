"""
Pydantic schemas for Salary Payment model
"""

from pydantic import BaseModel, validator
from datetime import date
from decimal import Decimal
from typing import Optional

from app.models.salary_payment import PaymentStatus


class SalaryPaymentBase(BaseModel):
    """Base salary payment schema"""
    employee_id: str
    month: int
    year: int
    amount: Decimal
    
    @validator('month')
    def validate_month(cls, v):
        if v < 1 or v > 12:
            raise ValueError('Month must be between 1 and 12')
        return v
    
    @validator('year')
    def validate_year(cls, v):
        if v < 2000 or v > 2100:
            raise ValueError('Year must be between 2000 and 2100')
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError('Amount cannot be negative')
        return v


class SalaryPaymentCreate(SalaryPaymentBase):
    """Schema for creating a salary payment"""
    status: Optional[PaymentStatus] = PaymentStatus.PENDING
    payment_date: Optional[date] = None
    notes: Optional[str] = None


class SalaryPaymentUpdate(BaseModel):
    """Schema for updating a salary payment"""
    amount: Optional[Decimal] = None
    status: Optional[PaymentStatus] = None
    payment_date: Optional[date] = None
    notes: Optional[str] = None


class SalaryPaymentMarkPaid(BaseModel):
    """Schema for marking payment as paid"""
    payment_date: date
    notes: Optional[str] = None


class SalaryPaymentResponse(SalaryPaymentBase):
    """Schema for salary payment response"""
    payment_id: str
    status: PaymentStatus
    payment_date: Optional[date]
    notes: Optional[str]
    created_date: date
    
    class Config:
        orm_mode = True


class SalaryPaymentWithEmployee(SalaryPaymentResponse):
    """Schema for salary payment with employee details"""
    employee_name: str
    employee_post: str
    
    class Config:
        orm_mode = True
