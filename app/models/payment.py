"""
Payment model for tracking all payment transactions
"""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class PaymentType(PyEnum):
    """Payment type options"""
    OPD_FEE = "OPD_FEE"
    IPD_ADVANCE = "IPD_ADVANCE"
    INVESTIGATION = "INVESTIGATION"
    PROCEDURE = "PROCEDURE"
    SERVICE = "SERVICE"
    OT = "OT"
    DISCHARGE = "DISCHARGE"
    MANUAL = "MANUAL"


class PaymentStatus(PyEnum):
    """Payment status options"""
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base):
    """Payment model for all payment transactions"""
    
    __tablename__ = "payments"
    
    payment_id = Column(String(30), primary_key=True)
    patient_id = Column(String(20), ForeignKey("patients.patient_id"), nullable=False)
    visit_id = Column(String(30), ForeignKey("visits.visit_id"), nullable=True)
    ipd_id = Column(String(20), ForeignKey("ipd.ipd_id"), nullable=True)
    payment_type = Column(Enum(PaymentType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_mode = Column(String(20), nullable=False)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.COMPLETED)
    transaction_reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    payment_date = Column(DateTime(timezone=False), server_default=func.now())
    created_by = Column(String(20), nullable=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="payments")
    visit = relationship("Visit", back_populates="payments")
    ipd = relationship("IPD", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(payment_id='{self.payment_id}', amount='{self.amount}', mode='{self.payment_mode}')>"
