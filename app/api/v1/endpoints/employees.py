"""
API endpoints for employee management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.crud.employee import employee_crud
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    SalarySlipRequest,
    SalarySlipResponse
)
from app.models.user import User, UserRole
from app.models.employee import EmployeeStatus

router = APIRouter()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new employee (Admin only)
    """
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create employees"
        )
    
    try:
        employee = await employee_crud.create_employee(
            db=db,
            name=employee_data.name,
            post=employee_data.post,
            employment_status=employee_data.employment_status,
            duty_hours=employee_data.duty_hours,
            joining_date=employee_data.joining_date,
            monthly_salary=employee_data.monthly_salary,
            qualification=employee_data.qualification
        )
        return employee
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get employee by ID
    """
    employee = await employee_crud.get_employee_by_id(db, employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return employee


@router.get("/", response_model=List[EmployeeResponse])
async def get_all_employees(
    status: Optional[EmployeeStatus] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all employees, optionally filtered by status
    """
    employees = await employee_crud.get_all_employees(
        db=db,
        status=status,
        limit=limit
    )
    return employees


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update employee details (Admin only)
    """
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update employees"
        )
    
    try:
        employee = await employee_crud.update_employee(
            db=db,
            employee_id=employee_id,
            name=employee_data.name,
            post=employee_data.post,
            qualification=employee_data.qualification,
            employment_status=employee_data.employment_status,
            duty_hours=employee_data.duty_hours,
            monthly_salary=employee_data.monthly_salary,
            status=employee_data.status
        )
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        return employee
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete employee (soft delete - sets status to INACTIVE) (Admin only)
    """
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can delete employees"
        )
    
    success = await employee_crud.delete_employee(db, employee_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )


@router.post("/salary-slip", response_model=SalarySlipResponse)
async def generate_salary_slip(
    slip_request: SalarySlipRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate salary slip for an employee (Admin only)
    """
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can generate salary slips"
        )
    
    try:
        salary_slip = await employee_crud.generate_salary_slip(
            db=db,
            employee_id=slip_request.employee_id,
            month=slip_request.month,
            year=slip_request.year
        )
        return salary_slip
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
