"""
Salary Payment model for tracking employee salary payments
"""

from sqlalchemy import Column, String, Integer, Numeric, Enum, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.core.database import Base


class PaymentStatus(PyEnum):
    """Payment status options"""
    PENDING = "PENDING"
    PAID = "PAID"


class SalaryPayment(Base):
    """Salary Payment model for tracking monthly salary payments"""
    
    __tablename__ = "salary_payments"
    
    payment_id = Column(String(20), primary_key=True)
    employee_id = Column(String(20), ForeignKey("employees.employee_id"), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(Date, nullable=True)  # Null if pending
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    notes = Column(String(500), nullable=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    employee = relationship("Employee", backref="salary_payments")
    
    def __repr__(self):
        return f"<SalaryPayment(payment_id='{self.payment_id}', employee_id='{self.employee_id}', month={self.month}, year={self.year}, status='{self.status}')>"
