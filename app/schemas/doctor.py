"""
Doctor schemas
"""

from pydantic import BaseModel, validator
from decimal import Decimal
from datetime import datetime


class DoctorBase(BaseModel):
    """Base doctor schema"""
    name: str
    department: str
    new_patient_fee: Decimal
    followup_fee: Decimal
    status: str = "ACTIVE"
    
    @validator('new_patient_fee', 'followup_fee')
    def validate_fees(cls, v):
        """Validate fee amounts"""
        if v < 0:
            raise ValueError('Fee cannot be negative')
        return v


class DoctorCreate(DoctorBase):
    """Doctor creation schema"""
    pass


class DoctorUpdate(BaseModel):
    """Doctor update schema - all fields optional"""
    name: str | None = None
    department: str | None = None
    new_patient_fee: Decimal | None = None
    followup_fee: Decimal | None = None
    status: str | None = None
    
    @validator('new_patient_fee', 'followup_fee')
    def validate_fees(cls, v):
        """Validate fee amounts"""
        if v is not None and v < 0:
            raise ValueError('Fee cannot be negative')
        return v


class DoctorResponse(DoctorBase):
    """Doctor response schema"""
    doctor_id: str
    created_date: datetime
    
    class Config:
        from_attributes = True