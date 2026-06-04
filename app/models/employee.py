"""
Employee model for staff management and salary processing
"""

from sqlalchemy import Column, String, Integer, Date, Numeric, Enum, DateTime
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.core.database import Base


class EmploymentStatus(PyEnum):
    """Employment status options"""
    PERMANENT = "PERMANENT"
    PROBATION = "PROBATION"


class EmployeeStatus(PyEnum):
    """Employee status options"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Employee(Base):
    """Employee model for staff management"""
    
    __tablename__ = "employees"
    
    employee_id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    post = Column(String(50), nullable=False)
    qualification = Column(String(100), nullable=True)
    employment_status = Column(Enum(EmploymentStatus), nullable=False)
    duty_hours = Column(Integer, nullable=False)
    joining_date = Column(Date, nullable=False)
    monthly_salary = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(EmployeeStatus), nullable=False, default=EmployeeStatus.ACTIVE)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Employee(employee_id='{self.employee_id}', name='{self.name}', post='{self.post}')>"