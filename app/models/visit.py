"""
Visit model for OPD visits and follow-ups
"""

from sqlalchemy import Column, String, Integer, Enum, Date, Time, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class VisitType(PyEnum):
    """Visit type options"""
    OPD_NEW = "OPD_NEW"
    OPD_FOLLOWUP = "OPD_FOLLOWUP"


class PaymentMode(PyEnum):
    """Payment mode options"""
    CASH = "CASH"
    UPI = "UPI"
    CARD = "CARD"


class VisitStatus(PyEnum):
    """Visit status options"""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Visit(Base):
    """Visit model for OPD visits"""
    
    __tablename__ = "visits"
    
    visit_id = Column(String(30), primary_key=True)
    patient_id = Column(String(20), ForeignKey("patients.patient_id"), nullable=False)
    visit_type = Column(Enum(VisitType), nullable=False)
    doctor_id = Column(String(20), ForeignKey("doctors.doctor_id"), nullable=False)
    department = Column(String(50), nullable=False)
    serial_number = Column(Integer, nullable=False)
    visit_date = Column(Date, nullable=False)
    visit_time = Column(Time, nullable=False)
    opd_fee = Column(Numeric(10, 2), nullable=False)
    payment_mode = Column(Enum(PaymentMode), nullable=False)
    status = Column(Enum(VisitStatus), nullable=False, default=VisitStatus.ACTIVE)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="visits")
    doctor = relationship("Doctor", back_populates="visits")
    billing_charges = relationship("BillingCharge", back_populates="visit")
    ipd_admission = relationship("IPD", back_populates="visit", uselist=False)
    payments = relationship("Payment", back_populates="visit")
    slips = relationship("Slip", back_populates="visit")
    
    def __repr__(self):
        return f"<Visit(visit_id='{self.visit_id}', patient_id='{self.patient_id}', type='{self.visit_type}')>"