"""
Pydantic schemas for Employee model
"""

from pydantic import BaseModel, validator
from datetime import date
from decimal import Decimal
from typing import Optional

from app.models.employee import EmploymentStatus, EmployeeStatus


class EmployeeBase(BaseModel):
    """Base employee schema"""
    name: str
    post: str
    qualification: Optional[str] = None
    employment_status: EmploymentStatus
    duty_hours: int
    joining_date: date
    monthly_salary: Decimal
    
    @validator('duty_hours')
    def validate_duty_hours(cls, v):
        if v <= 0:
            raise ValueError('Duty hours must be positive')
        return v
    
    @validator('monthly_salary')
    def validate_salary(cls, v):
        if v < 0:
            raise ValueError('Monthly salary cannot be negative')
        return v


class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee"""
    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee"""
    name: Optional[str] = None
    post: Optional[str] = None
    qualification: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None
    duty_hours: Optional[int] = None
    monthly_salary: Optional[Decimal] = None
    status: Optional[EmployeeStatus] = None
    
    @validator('duty_hours')
    def validate_duty_hours(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Duty hours must be positive')
        return v
    
    @validator('monthly_salary')
    def validate_salary(cls, v):
        if v is not None and v < 0:
            raise ValueError('Monthly salary cannot be negative')
        return v


class EmployeeResponse(EmployeeBase):
    """Schema for employee response"""
    employee_id: str
    status: EmployeeStatus
    created_date: date
    
    class Config:
        orm_mode = True


class SalarySlipRequest(BaseModel):
    """Schema for salary slip generation request"""
    employee_id: str
    month: int
    year: int
    
    @validator('month')
    def validate_month(cls, v):
        if v < 1 or v > 12:
            raise ValueError('Month must be between 1 and 12')
        return v
    
    @validator('year')
    def validate_year(cls, v):
        if v < 2000 or v > 2100:
            raise ValueError('Year must be between 2000 and 2100')
        return v


class SalarySlipResponse(BaseModel):
    """Schema for salary slip response"""
    employee_id: str
    employee_name: str
    post: str
    month: int
    year: int
    joining_date: str
    employment_status: str
    duty_hours: int
    basic_salary: float
    gross_salary: float
    deductions: float
    net_salary: float
    generated_date: str
