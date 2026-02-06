"""
Doctor model for managing doctors and their consultation fees
"""

from sqlalchemy import Column, String, Numeric, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class DoctorStatus(PyEnum):
    """Doctor status options"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Doctor(Base):
    """Doctor model for storing doctor information and fees"""
    
    __tablename__ = "doctors"
    
    doctor_id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)
    new_patient_fee = Column(Numeric(10, 2), nullable=False)
    followup_fee = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(DoctorStatus), nullable=False, default=DoctorStatus.ACTIVE)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    visits = relationship("Visit", back_populates="doctor")
    
    def __repr__(self):
        return f"<Doctor(doctor_id='{self.doctor_id}', name='{self.name}', department='{self.department}')>"