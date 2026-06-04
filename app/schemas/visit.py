"""
Visit schemas
"""

from pydantic import BaseModel, validator, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime, date, time


class VisitBase(BaseModel):
    """Base visit schema"""
    patient_id: str = Field(..., description="Patient ID")
    doctor_id: str = Field(..., description="Doctor ID")
    payment_mode: str = Field(..., description="Payment mode (CASH, UPI, CARD)")
    
    @validator('payment_mode')
    def validate_payment_mode(cls, v):
        """Validate payment mode"""
        if v.upper() not in ['CASH', 'UPI', 'CARD']:
            raise ValueError('Payment mode must be CASH, UPI, or CARD')
        return v.upper()


class OPDRegistrationRequest(BaseModel):
    """OPD new patient registration request"""
    patient_id: str = Field(..., description="Patient ID")
    doctor_id: str = Field(..., description="Doctor ID")
    payment_mode: str = Field(..., description="Payment mode (CASH, UPI, CARD)")
    visit_date: Optional[date] = Field(None, description="Visit date (defaults to today)")
    visit_time: Optional[time] = Field(None, description="Visit time (defaults to now)")
    
    @validator('payment_mode')
    def validate_payment_mode(cls, v):
        """Validate payment mode"""
        if v.upper() not in ['CASH', 'UPI', 'CARD']:
            raise ValueError('Payment mode must be CASH, UPI, or CARD')
        return v.upper()


class FollowUpRegistrationRequest(BaseModel):
    """Follow-up patient registration request"""
    patient_id: str = Field(..., description="Patient ID")
    doctor_id: str = Field(..., description="Doctor ID")
    payment_mode: str = Field(..., description="Payment mode (CASH, UPI, CARD)")
    visit_date: Optional[date] = Field(None, description="Visit date (defaults to today)")
    visit_time: Optional[time] = Field(None, description="Visit time (defaults to now)")
    
    @validator('payment_mode')
    def validate_payment_mode(cls, v):
        """Validate payment mode"""
        if v.upper() not in ['CASH', 'UPI', 'CARD']:
            raise ValueError('Payment mode must be CASH, UPI, or CARD')
        return v.upper()


class VisitCreate(VisitBase):
    """Visit creation schema"""
    visit_type: str = Field(..., description="Visit type (OPD_NEW, OPD_FOLLOWUP)")
    
    @validator('visit_type')
    def validate_visit_type(cls, v):
        """Validate visit type"""
        if v.upper() not in ['OPD_NEW', 'OPD_FOLLOWUP']:
            raise ValueError('Visit type must be OPD_NEW or OPD_FOLLOWUP')
        return v.upper()


class DoctorInfo(BaseModel):
    """Doctor information for visit response"""
    doctor_id: str
    name: str
    department: str
    new_patient_fee: Decimal
    followup_fee: Decimal
    
    class Config:
        from_attributes = True


class PatientInfo(BaseModel):
    """Patient information for visit response"""
    patient_id: str
    name: str
    age: int
    gender: str
    mobile_number: str
    
    class Config:
        from_attributes = True


class VisitResponse(VisitBase):
    """Visit response schema"""
    visit_id: str
    visit_type: str
    department: str
    serial_number: int
    visit_date: date
    visit_time: time
    opd_fee: Decimal
    status: str
    created_date: datetime
    
    class Config:
        from_attributes = True


class VisitDetailResponse(VisitResponse):
    """Detailed visit response with patient and doctor info"""
    patient: Optional[PatientInfo] = None
    doctor: Optional[DoctorInfo] = None
    
    class Config:
        from_attributes = True


class FollowUpPatientInfo(BaseModel):
    """Follow-up patient information"""
    patient: PatientInfo
    last_visit_date: date
    last_visit_doctor: str
    last_visit_department: str
    
    class Config:
        from_attributes = True