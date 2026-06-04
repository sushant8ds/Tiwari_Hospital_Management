"""
Slip model for tracking all generated slips
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class SlipType(PyEnum):
    """Slip type options"""
    OPD = "OPD"
    INVESTIGATION = "INVESTIGATION"
    PROCEDURE = "PROCEDURE"
    SERVICE = "SERVICE"
    OT = "OT"
    DISCHARGE = "DISCHARGE"


class PrinterFormat(PyEnum):
    """Printer format options"""
    A4 = "A4"
    THERMAL = "THERMAL"


class Slip(Base):
    """Slip model for all generated slips"""
    
    __tablename__ = "slips"
    
    slip_id = Column(String(30), primary_key=True)
    patient_id = Column(String(20), ForeignKey("patients.patient_id"), nullable=False)
    visit_id = Column(String(30), ForeignKey("visits.visit_id"), nullable=True)
    ipd_id = Column(String(20), ForeignKey("ipd.ipd_id"), nullable=True)
    slip_type = Column(Enum(SlipType), nullable=False)
    barcode_data = Column(String(100), nullable=False)
    barcode_image = Column(Text, nullable=True)  # Base64 encoded image
    slip_content = Column(Text, nullable=False)  # JSON or HTML content
    printer_format = Column(Enum(PrinterFormat), nullable=False, default=PrinterFormat.A4)
    is_reprinted = Column(Boolean, default=False)
    original_slip_id = Column(String(30), nullable=True)  # For reprints
    generated_date = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(String(20), nullable=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="slips")
    visit = relationship("Visit", back_populates="slips")
    ipd = relationship("IPD", back_populates="slips")
    
    def __repr__(self):
        return f"<Slip(slip_id='{self.slip_id}', type='{self.slip_type}')>"
