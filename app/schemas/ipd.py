"""
IPD schemas
"""

from pydantic import BaseModel, validator
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from app.schemas.doctor import DoctorResponse


class IPDBase(BaseModel):
    """Base IPD schema"""
    patient_id: str
    bed_id: str
    file_charge: Decimal


class IPDCreate(IPDBase):
    """IPD creation schema"""
    visit_id: Optional[str] = None
    admission_date: Optional[datetime] = None
    attending_doctor_id: Optional[str] = None
    referred_by: Optional[str] = None
    
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
    mobile_number: Optional[str] = None
    
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
    referred_by: Optional[str] = None
    attending_doctor_id: Optional[str] = None
    diagnosis: Optional[str] = None
    procedure_performed: Optional[str] = None
    operation_date: Optional[datetime] = None
    discount: Decimal = Decimal("0.00")
    patient: Optional[PatientNested] = None
    bed: Optional[BedNested] = None
    attending_doctor: Optional[DoctorResponse] = None
    
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
    diagnosis: str
    procedure_performed: str
    operation_date: Optional[datetime] = None
    discount: Decimal = Decimal("0.00")
    payment_mode: str = "CASH"


class BedOccupancyResponse(BaseModel):
    """Bed occupancy statistics response"""
    total_beds: int
    occupied: int
    available: int
    maintenance: int
    occupancy_rate: float
    by_ward_type: dict