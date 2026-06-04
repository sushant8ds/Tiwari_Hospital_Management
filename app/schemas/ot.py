"""
Operation Theater (OT) schemas
"""

from pydantic import BaseModel, validator, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional


class OTProcedureBase(BaseModel):
    """Base OT procedure schema"""
    operation_name: str
    operation_date: datetime
    duration_minutes: int
    surgeon_name: str
    anesthesia_type: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        """Validate duration is positive"""
        if v <= 0:
            raise ValueError('Duration must be positive')
        return v
    
    @validator('operation_name', 'surgeon_name')
    def validate_not_empty(cls, v):
        """Validate fields are not empty"""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class OTProcedureCreate(OTProcedureBase):
    """OT procedure creation schema"""
    ipd_id: str


class OTProcedureResponse(OTProcedureBase):
    """OT procedure response schema"""
    ot_id: str
    ipd_id: str
    created_date: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class OTChargesRequest(BaseModel):
    """OT charges request schema"""
    surgeon_charge: Decimal
    anesthesia_charge: Decimal
    facility_charge: Decimal
    assistant_charge: Optional[Decimal] = Decimal("0.00")
    
    @validator('surgeon_charge', 'anesthesia_charge', 'facility_charge', 'assistant_charge')
    def validate_charges(cls, v):
        """Validate charges are non-negative"""
        if v < 0:
            raise ValueError('Charges cannot be negative')
        return v


class OTChargesResponse(BaseModel):
    """OT charges response schema"""
    surgeon_charge: Decimal
    anesthesia_charge: Decimal
    facility_charge: Decimal
    assistant_charge: Decimal
    total_charge: Decimal
