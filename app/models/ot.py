"""
Operation Theater (OT) model
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class OTProcedure(Base):
    """Operation Theater procedure model"""
    
    __tablename__ = "ot_procedures"
    
    ot_id = Column(String(30), primary_key=True)
    ipd_id = Column(String(20), ForeignKey("ipd.ipd_id"), nullable=False)
    operation_name = Column(String(200), nullable=False)
    operation_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False)  # Duration in minutes
    surgeon_name = Column(String(100), nullable=False)
    anesthesia_type = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(20), nullable=False)
    
    # Relationships
    ipd = relationship("IPD", back_populates="ot_procedures")
    
    def __repr__(self):
        return f"<OTProcedure(ot_id='{self.ot_id}', operation='{self.operation_name}')>"
