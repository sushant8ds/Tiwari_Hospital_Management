"""
Billing schemas
"""

from pydantic import BaseModel, validator, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional, List


class BillingChargeBase(BaseModel):
    """Base billing charge schema"""
    charge_name: str
    quantity: int = 1
    rate: Decimal
    
    @validator('quantity')
    def validate_quantity(cls, v):
        """Validate quantity"""
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @validator('rate')
    def validate_rate(cls, v):
        """Validate rate"""
        if v < 0:
            raise ValueError('Rate cannot be negative')
        return v


class InvestigationChargeRequest(BillingChargeBase):
    """Investigation charge request schema"""
    pass


class ProcedureChargeRequest(BillingChargeBase):
    """Procedure charge request schema"""
    pass


class ServiceChargeRequest(BillingChargeBase):
    """Service charge request schema with optional time calculation"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Validate end_time is after start_time"""
        if v and 'start_time' in values and values['start_time']:
            if v <= values['start_time']:
                raise ValueError('End time must be after start time')
        return v


class ManualChargeRequest(BillingChargeBase):
    """Manual charge request schema (admin only)"""
    pass


class BillingChargeCreate(BillingChargeBase):
    """Billing charge creation schema"""
    charge_type: str


class BillingChargeResponse(BaseModel):
    """Billing charge response schema"""
    charge_id: str
    visit_id: Optional[str]
    ipd_id: Optional[str]
    charge_type: str
    charge_name: str
    quantity: int
    rate: Decimal
    total_amount: Decimal
    charge_date: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class DischargeBillResponse(BaseModel):
    """Discharge bill response schema"""
    ipd_id: str
    charges: List[BillingChargeResponse]
    total_charges: Decimal
    
    class Config:
        from_attributes = True