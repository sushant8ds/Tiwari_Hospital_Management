"""
Payment schemas
"""

from pydantic import BaseModel, validator, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional


class PaymentBase(BaseModel):
    """Base payment schema"""
    amount: Decimal
    payment_mode: str
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount is positive"""
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    @validator('payment_mode')
    def validate_payment_mode(cls, v):
        """Validate payment mode"""
        valid_modes = ['CASH', 'UPI', 'CARD']
        if v.upper() not in valid_modes:
            raise ValueError(f'Payment mode must be one of: {", ".join(valid_modes)}')
        return v.upper()


class PaymentCreate(PaymentBase):
    """Payment creation schema"""
    patient_id: str
    visit_id: Optional[str] = None
    ipd_id: Optional[str] = None
    payment_type: str
    created_by: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response schema"""
    payment_id: str
    patient_id: str
    visit_id: Optional[str]
    ipd_id: Optional[str]
    payment_type: str
    amount: Decimal
    payment_mode: str
    payment_status: str
    transaction_reference: Optional[str]
    notes: Optional[str]
    payment_date: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class AdvancePaymentRequest(BaseModel):
    """Advance payment request schema"""
    amount: Decimal
    payment_mode: str
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount is positive"""
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    @validator('payment_mode')
    def validate_payment_mode(cls, v):
        """Validate payment mode"""
        valid_modes = ['CASH', 'UPI', 'CARD']
        if v.upper() not in valid_modes:
            raise ValueError(f'Payment mode must be one of: {", ".join(valid_modes)}')
        return v.upper()


class PaymentHistoryResponse(BaseModel):
    """Payment history response schema"""
    payments: list[PaymentResponse]
    total_paid: Decimal
    
    class Config:
        from_attributes = True


class PatientBalanceResponse(BaseModel):
    """Patient balance response schema"""
    patient_id: str
    total_charges: Decimal
    total_paid: Decimal
    balance_due: Decimal
    advance_balance: Decimal
