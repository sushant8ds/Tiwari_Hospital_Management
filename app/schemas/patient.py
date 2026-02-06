"""
Patient schemas
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime, date, time
import re


class PatientBase(BaseModel):
    """Base patient schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Patient name")
    age: int = Field(..., ge=0, le=150, description="Patient age")
    gender: str = Field(..., description="Patient gender (MALE, FEMALE, OTHER)")
    address: str = Field(..., min_length=1, description="Patient address")
    mobile_number: str = Field(..., description="10-digit Indian mobile number")
    
    @validator('mobile_number')
    def validate_mobile_number(cls, v):
        """Validate Indian mobile number format"""
        if not re.match(r'^[6-9]\d{9}$', v):
            raise ValueError('Invalid mobile number format. Must be 10 digits starting with 6-9')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        """Validate gender value"""
        if v.upper() not in ['MALE', 'FEMALE', 'OTHER']:
            raise ValueError('Gender must be MALE, FEMALE, or OTHER')
        return v.upper()


class PatientCreate(PatientBase):
    """Patient creation schema"""
    pass


class PatientUpdate(BaseModel):
    """Patient update schema - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Patient name")
    age: Optional[int] = Field(None, ge=0, le=150, description="Patient age")
    gender: Optional[str] = Field(None, description="Patient gender (MALE, FEMALE, OTHER)")
    address: Optional[str] = Field(None, min_length=1, description="Patient address")
    mobile_number: Optional[str] = Field(None, description="10-digit Indian mobile number")
    
    @validator('mobile_number')
    def validate_mobile_number(cls, v):
        """Validate Indian mobile number format"""
        if v is not None and not re.match(r'^[6-9]\d{9}$', v):
            raise ValueError('Invalid mobile number format. Must be 10 digits starting with 6-9')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        """Validate gender value"""
        if v is not None and v.upper() not in ['MALE', 'FEMALE', 'OTHER']:
            raise ValueError('Gender must be MALE, FEMALE, or OTHER')
        return v.upper() if v else None


class PatientResponse(PatientBase):
    """Patient response schema"""
    patient_id: str
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True


class PatientSearch(BaseModel):
    """Patient search schema"""
    patient_id: Optional[str] = None
    mobile_number: Optional[str] = None
    name: Optional[str] = None


# Visit-related schemas for history
class VisitSummary(BaseModel):
    """Visit summary for patient history"""
    visit_id: str
    visit_type: str
    doctor_id: str
    department: str
    serial_number: int
    visit_date: date
    visit_time: time
    opd_fee: float
    payment_mode: str
    status: str
    created_date: datetime
    
    class Config:
        from_attributes = True


class IPDSummary(BaseModel):
    """IPD summary for patient history"""
    ipd_id: str
    admission_date: datetime
    discharge_date: Optional[datetime]
    file_charge: float
    bed_id: str
    status: str
    created_date: datetime
    
    class Config:
        from_attributes = True


class PatientHistoryResponse(BaseModel):
    """Patient history response with visits and IPD admissions"""
    patient: PatientResponse
    visits: List[VisitSummary]
    ipd_admissions: List[IPDSummary]
    
    class Config:
        from_attributes = True