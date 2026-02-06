"""
Billing model for all types of charges
"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class ChargeType(PyEnum):
    """Charge type options"""
    INVESTIGATION = "INVESTIGATION"
    PROCEDURE = "PROCEDURE"
    SERVICE = "SERVICE"
    OT = "OT"
    MANUAL = "MANUAL"
    BED = "BED"


class BillingCharge(Base):
    """Billing charges model for all types of charges"""
    
    __tablename__ = "billing_charges"
    
    charge_id = Column(String(30), primary_key=True)
    visit_id = Column(String(30), ForeignKey("visits.visit_id"), nullable=True)
    ipd_id = Column(String(20), ForeignKey("ipd.ipd_id"), nullable=True)
    charge_type = Column(Enum(ChargeType), nullable=False)
    charge_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    rate = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    charge_date = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(20), nullable=False)
    
    # Relationships
    visit = relationship("Visit", back_populates="billing_charges")
    ipd = relationship("IPD", back_populates="billing_charges")
    
    def __repr__(self):
        return f"<BillingCharge(charge_id='{self.charge_id}', type='{self.charge_type}', amount='{self.total_amount}')>"