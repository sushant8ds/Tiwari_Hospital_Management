"""
Bed model for IPD bed management
"""

from sqlalchemy import Column, String, Enum, Numeric, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class WardType(PyEnum):
    """Ward type options"""
    GENERAL = "GENERAL"
    SEMI_PRIVATE = "SEMI_PRIVATE"
    PRIVATE = "PRIVATE"


class BedStatus(PyEnum):
    """Bed status options"""
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"


class Bed(Base):
    """Bed model for IPD bed allocation"""
    
    __tablename__ = "beds"
    
    bed_id = Column(String(20), primary_key=True)
    bed_number = Column(String(10), nullable=False, unique=True)
    ward_type = Column(Enum(WardType), nullable=False)
    per_day_charge = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(BedStatus), nullable=False, default=BedStatus.AVAILABLE)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ipd_admissions = relationship("IPD", back_populates="bed")
    
    def __repr__(self):
        return f"<Bed(bed_id='{self.bed_id}', bed_number='{self.bed_number}', ward_type='{self.ward_type}')>"