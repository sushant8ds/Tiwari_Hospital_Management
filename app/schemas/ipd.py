"""
IPD schemas
"""

from pydantic import BaseModel, validator
from decimal import Decimal
from datetime import datetime
from typing import Optional, List


class IPDBase(BaseModel):
    """Base IPD schema"""
    patient_id: str
    bed_id: str
    file_charge: Decimal


class IPDCreate(IPDBase):
    """IPD creation schema"""
    visit_id: Optional[str] = None
    admission_date: Optional[datetime] = None
    
    @validator('file_charge')
    def validate_file_charge(cls, v):
        if v < 0:
            raise ValueError('File charge cannot be negative')
        return v


# Nested schemas for relationships
class PatientNested(BaseModel):
    """Nested patient schema for IPD response"""
    patient_id: str
    name: str
    mobile: Optional[str] = None
    
    class Config:
        from_attributes = True


class BedNested(BaseModel):
    """Nested bed schema for IPD response"""
    bed_id: str
    bed_number: str
    ward_type: str
    per_day_charge: Decimal
    status: str
    
    class Config:
        from_attributes = True


class IPDResponse(IPDBase):
    """IPD response schema"""
    ipd_id: str
    visit_id: Optional[str]
    admission_date: datetime
    discharge_date: Optional[datetime]
    status: str
    created_date: datetime
    patient: Optional[PatientNested] = None
    bed: Optional[BedNested] = None
    
    class Config:
        from_attributes = True


class BedBase(BaseModel):
    """Base Bed schema"""
    bed_number: str
    ward_type: str
    per_day_charge: Decimal


class BedCreate(BedBase):
    """Bed creation schema"""
    @validator('per_day_charge')
    def validate_per_day_charge(cls, v):
        if v < 0:
            raise ValueError('Per day charge cannot be negative')
        return v


class BedResponse(BedBase):
    """Bed response schema"""
    bed_id: str
    status: str
    created_date: datetime
    
    class Config:
        from_attributes = True


class BedChangeRequest(BaseModel):
    """Bed change request schema"""
    new_bed_id: str


class DischargeRequest(BaseModel):
    """Discharge request schema"""
    discharge_date: Optional[datetime] = None


class BedOccupancyResponse(BaseModel):
    """Bed occupancy statistics response"""
    total_beds: int
    occupied: int
    available: int
    maintenance: int
    occupancy_rate: float
    by_ward_type: dict