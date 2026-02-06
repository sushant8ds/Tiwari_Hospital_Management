"""
API endpoints for reports and patient history
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.crud.reports import reports_crud
from app.schemas.reports import (
    PatientHistoryResponse,
    DailyOPDReportRequest,
    DailyOPDReportResponse,
    DoctorRevenueReportRequest,
    DoctorRevenueReportResponse,
    IPDOccupancyReportResponse,
    SalaryReportRequest,
    SalaryReportResponse
)

router = APIRouter()


@router.get("/patient-history/{patient_id}", response_model=PatientHistoryResponse)
async def get_patient_history(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive patient history including all visits, charges, and services
    
    Accessible by: Reception, Admin
    """
    try:
        history = await reports_crud.get_patient_history(db, patient_id)
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        return history
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving patient history: {str(e)}"
        )


@router.post("/daily-opd", response_model=DailyOPDReportResponse)
async def get_daily_opd_report(
    request: DailyOPDReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get daily OPD report with patient count and collections
    
    Accessible by: Reception, Admin
    """
    try:
        report = await reports_crud.get_daily_opd_report(
            db=db,
            report_date=request.report_date,
            doctor_id=request.doctor_id
        )
        
        return report
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating daily OPD report: {str(e)}"
        )


@router.post("/doctor-revenue", response_model=DoctorRevenueReportResponse)
async def get_doctor_revenue_report(
    request: DoctorRevenueReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get doctor-wise revenue report for a date range
    
    Accessible by: Admin only
    """
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin users can access revenue reports"
        )
    
    try:
        report = await reports_crud.get_doctor_revenue_report(
            db=db,
            start_date=request.start_date,
            end_date=request.end_date,
            doctor_id=request.doctor_id
        )
        
        return report
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating doctor revenue report: {str(e)}"
        )


@router.get("/ipd-occupancy", response_model=IPDOccupancyReportResponse)
async def get_ipd_occupancy_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get IPD bed occupancy report
    
    Accessible by: Reception, Admin
    """
    try:
        report = await reports_crud.get_ipd_occupancy_report(db)
        
        return report
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating IPD occupancy report: {str(e)}"
        )


@router.post("/salary", response_model=SalaryReportResponse)
async def get_salary_report(
    request: SalaryReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get salary report for all active employees
    
    Accessible by: Admin only
    """
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin users can access salary reports"
        )
    
    try:
        report = await reports_crud.get_salary_report(
            db=db,
            month=request.month,
            year=request.year
        )
        
        return report
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating salary report: {str(e)}"
        )
