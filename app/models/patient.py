"""
Patient model for patient registration and management
"""

from sqlalchemy import Column, String, Integer, Enum, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class Gender(PyEnum):
    """Patient gender options"""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class Patient(Base):
    """Patient model for storing patient information"""
    
    __tablename__ = "patients"
    
    patient_id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    address = Column(Text, nullable=False)
    mobile_number = Column(String(15), nullable=False, unique=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    visits = relationship("Visit", back_populates="patient")
    ipd_admissions = relationship("IPD", back_populates="patient")
    payments = relationship("Payment", back_populates="patient")
    slips = relationship("Slip", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(patient_id='{self.patient_id}', name='{self.name}', mobile='{self.mobile_number}')>"