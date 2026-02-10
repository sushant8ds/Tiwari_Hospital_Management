"""
API endpoints for Owner/Admin panel
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.core.dependencies import get_db, get_current_user, require_admin
from app.crud.doctor import doctor_crud
from app.crud.employee import employee_crud
from app.crud.salary_payment import salary_payment_crud
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.schemas.salary_payment import (
    SalaryPaymentCreate,
    SalaryPaymentUpdate,
    SalaryPaymentMarkPaid,
    SalaryPaymentResponse,
    SalaryPaymentWithEmployee
)
from app.models.user import User
from app.models.employee import EmployeeStatus
from app.models.salary_payment import PaymentStatus

router = APIRouter()


# Doctor Management Endpoints
@router.post("/doctors", response_model=DoctorResponse)
async def create_doctor(
    doctor: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Create a new doctor (Admin only)"""
    try:
        new_doctor = await doctor_crud.create_doctor(
            db=db,
            name=doctor.name,
            department=doctor.department,
            new_patient_fee=doctor.new_patient_fee,
            followup_fee=doctor.followup_fee
        )
        return new_doctor
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/doctors/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: str,
    doctor: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Update doctor details (Admin only)"""
    try:
        updated_doctor = await doctor_crud.update_doctor(
            db=db,
            doctor_id=doctor_id,
            name=doctor.name,
            department=doctor.department,
            new_patient_fee=doctor.new_patient_fee,
            followup_fee=doctor.followup_fee,
            status=doctor.status
        )
        if not updated_doctor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
        return updated_doctor
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Employee Management Endpoints
@router.post("/employees", response_model=EmployeeResponse)
async def create_employee(
    employee: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Create a new employee (Admin only)"""
    try:
        new_employee = await employee_crud.create_employee(
            db=db,
            name=employee.name,
            post=employee.post,
            qualification=employee.qualification,
            employment_status=employee.employment_status,
            duty_hours=employee.duty_hours,
            joining_date=employee.joining_date,
            monthly_salary=employee.monthly_salary
        )
        return new_employee
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/employees", response_model=List[EmployeeResponse])
async def get_all_employees(
    status: Optional[EmployeeStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Get all employees (Admin only)"""
    employees = await employee_crud.get_all_employees(db, status=status)
    return employees


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Get employee by ID (Admin only)"""
    employee = await employee_crud.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Update employee details (Admin only)"""
    try:
        updated_employee = await employee_crud.update_employee(
            db=db,
            employee_id=employee_id,
            name=employee.name,
            post=employee.post,
            qualification=employee.qualification,
            employment_status=employee.employment_status,
            duty_hours=employee.duty_hours,
            monthly_salary=employee.monthly_salary,
            status=employee.status
        )
        if not updated_employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return updated_employee
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Salary Payment Endpoints
@router.post("/salary-payments", response_model=SalaryPaymentResponse)
async def create_salary_payment(
    payment: SalaryPaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Create a salary payment record (Admin only)"""
    try:
        new_payment = await salary_payment_crud.create_payment(
            db=db,
            employee_id=payment.employee_id,
            month=payment.month,
            year=payment.year,
            amount=payment.amount,
            status=payment.status,
            payment_date=payment.payment_date,
            notes=payment.notes
        )
        return new_payment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/salary-payments", response_model=List[SalaryPaymentResponse])
async def get_salary_payments(
    month: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[PaymentStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Get all salary payments with filters (Admin only)"""
    payments = await salary_payment_crud.get_all_payments(
        db=db,
        month=month,
        year=year,
        status=status
    )
    return payments


@router.get("/salary-payments/pending", response_model=List[SalaryPaymentResponse])
async def get_pending_payments(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Get all pending salary payments (Admin only)"""
    payments = await salary_payment_crud.get_pending_payments(
        db=db,
        month=month,
        year=year
    )
    return payments


@router.post("/salary-payments/{payment_id}/mark-paid", response_model=SalaryPaymentResponse)
async def mark_payment_as_paid(
    payment_id: str,
    payment_data: SalaryPaymentMarkPaid,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Mark a salary payment as paid (Admin only)"""
    payment = await salary_payment_crud.mark_as_paid(
        db=db,
        payment_id=payment_id,
        payment_date=payment_data.payment_date,
        notes=payment_data.notes
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.put("/salary-payments/{payment_id}", response_model=SalaryPaymentResponse)
async def update_salary_payment(
    payment_id: str,
    payment: SalaryPaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Update salary payment details (Admin only)"""
    updated_payment = await salary_payment_crud.update_payment(
        db=db,
        payment_id=payment_id,
        amount=payment.amount,
        status=payment.status,
        payment_date=payment.payment_date,
        notes=payment.notes
    )
    if not updated_payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return updated_payment
