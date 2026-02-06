"""
Schemas for reporting endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime


class DailyOPDReportRequest(BaseModel):
    """Request schema for daily OPD report"""
    report_date: date = Field(..., description="Date for the report")
    doctor_id: Optional[str] = Field(None, description="Optional doctor ID to filter by")


class DoctorRevenueReportRequest(BaseModel):
    """Request schema for doctor revenue report"""
    start_date: date = Field(..., description="Start date for the report")
    end_date: date = Field(..., description="End date for the report")
    doctor_id: Optional[str] = Field(None, description="Optional doctor ID to filter by")


class SalaryReportRequest(BaseModel):
    """Request schema for salary report"""
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    year: int = Field(..., ge=2000, le=2100, description="Year")


class PatientHistoryResponse(BaseModel):
    """Response schema for patient history"""
    patient: Dict[str, Any]
    visits: List[Dict[str, Any]]
    ipd_admissions: List[Dict[str, Any]]
    payments: List[Dict[str, Any]]
    summary: Dict[str, Any]


class DailyOPDReportResponse(BaseModel):
    """Response schema for daily OPD report"""
    report_date: str
    summary: Dict[str, Any]
    doctor_wise: List[Dict[str, Any]]


class DoctorRevenueReportResponse(BaseModel):
    """Response schema for doctor revenue report"""
    start_date: str
    end_date: str
    total_revenue: float
    doctor_wise_revenue: List[Dict[str, Any]]


class IPDOccupancyReportResponse(BaseModel):
    """Response schema for IPD occupancy report"""
    report_date: str
    summary: Dict[str, Any]
    beds: List[Dict[str, Any]]


class SalaryReportResponse(BaseModel):
    """Response schema for salary report"""
    month: int
    year: int
    total_employees: int
    total_salary: float
    employees: List[Dict[str, Any]]
