"""
IPD model for inpatient department management
"""

from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class IPDStatus(PyEnum):
    """IPD status options"""
    ADMITTED = "ADMITTED"
    DISCHARGED = "DISCHARGED"
    TRANSFERRED = "TRANSFERRED"


class IPD(Base):
    """IPD model for inpatient admissions"""
    
    __tablename__ = "ipd"
    
    ipd_id = Column(String(20), primary_key=True)
    patient_id = Column(String(20), ForeignKey("patients.patient_id"), nullable=False)
    visit_id = Column(String(30), ForeignKey("visits.visit_id"), nullable=True)
    admission_date = Column(DateTime(timezone=True), nullable=False)
    discharge_date = Column(DateTime(timezone=True), nullable=True)
    file_charge = Column(Numeric(10, 2), nullable=False)
    bed_id = Column(String(20), ForeignKey("beds.bed_id"), nullable=False)
    status = Column(Enum(IPDStatus), nullable=False, default=IPDStatus.ADMITTED)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="ipd_admissions")
    visit = relationship("Visit", back_populates="ipd_admission")
    bed = relationship("Bed", back_populates="ipd_admissions")
    billing_charges = relationship("BillingCharge", back_populates="ipd")
    ot_procedures = relationship("OTProcedure", back_populates="ipd")
    payments = relationship("Payment", back_populates="ipd")
    slips = relationship("Slip", back_populates="ipd")
    
    def __repr__(self):
        return f"<IPD(ipd_id='{self.ipd_id}', patient_id='{self.patient_id}', status='{self.status}')>"