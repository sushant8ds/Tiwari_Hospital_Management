"""
CRUD operations for Employee model
"""

from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.employee import Employee, EmploymentStatus, EmployeeStatus
from app.services.id_generator import generate_id


class EmployeeCRUD:
    """CRUD operations for Employee model"""
    
    async def create_employee(
        self,
        db: AsyncSession,
        name: str,
        post: str,
        employment_status: EmploymentStatus,
        duty_hours: int,
        joining_date: date,
        monthly_salary: Decimal,
        qualification: Optional[str] = None
    ) -> Employee:
        """Create a new employee with validation"""
        # Validate input data
        if not name or not name.strip():
            raise ValueError("Employee name is required")
        
        if not post or not post.strip():
            raise ValueError("Employee post is required")
        
        if duty_hours <= 0:
            raise ValueError("Duty hours must be positive")
        
        if monthly_salary < 0:
            raise ValueError("Monthly salary cannot be negative")
        
        try:
            # Generate unique employee ID: EMP + YYYYMMDD + 4-digit sequence
            employee_id = await generate_id("EMP")
            
            # Ensure salary is quantized to 2 decimal places
            monthly_salary = Decimal(str(monthly_salary)).quantize(Decimal("0.01"))
            
            employee = Employee(
                employee_id=employee_id,
                name=name.strip(),
                post=post.strip(),
                qualification=qualification.strip() if qualification else None,
                employment_status=employment_status,
                duty_hours=duty_hours,
                joining_date=joining_date,
                monthly_salary=monthly_salary,
                status=EmployeeStatus.ACTIVE
            )
            
            db.add(employee)
            await db.commit()
            await db.refresh(employee)
            return employee
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error creating employee")
    
    async def get_employee_by_id(
        self,
        db: AsyncSession,
        employee_id: str
    ) -> Optional[Employee]:
        """Get employee by ID"""
        result = await db.execute(
            select(Employee).where(Employee.employee_id == employee_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_employees(
        self,
        db: AsyncSession,
        status: Optional[EmployeeStatus] = None,
        limit: int = 100
    ) -> List[Employee]:
        """Get all employees, optionally filtered by status"""
        query = select(Employee)
        
        if status:
            query = query.where(Employee.status == status)
        
        query = query.order_by(Employee.created_date.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_employee(
        self,
        db: AsyncSession,
        employee_id: str,
        name: Optional[str] = None,
        post: Optional[str] = None,
        qualification: Optional[str] = None,
        employment_status: Optional[EmploymentStatus] = None,
        duty_hours: Optional[int] = None,
        monthly_salary: Optional[Decimal] = None,
        status: Optional[EmployeeStatus] = None
    ) -> Optional[Employee]:
        """Update employee details"""
        employee = await self.get_employee_by_id(db, employee_id)
        
        if not employee:
            return None
        
        try:
            if name is not None:
                if not name.strip():
                    raise ValueError("Employee name cannot be empty")
                employee.name = name.strip()
            
            if post is not None:
                if not post.strip():
                    raise ValueError("Employee post cannot be empty")
                employee.post = post.strip()
            
            if qualification is not None:
                employee.qualification = qualification.strip() if qualification else None
            
            if employment_status is not None:
                employee.employment_status = employment_status
            
            if duty_hours is not None:
                if duty_hours <= 0:
                    raise ValueError("Duty hours must be positive")
                employee.duty_hours = duty_hours
            
            if monthly_salary is not None:
                if monthly_salary < 0:
                    raise ValueError("Monthly salary cannot be negative")
                employee.monthly_salary = Decimal(str(monthly_salary)).quantize(Decimal("0.01"))
            
            if status is not None:
                employee.status = status
            
            await db.commit()
            await db.refresh(employee)
            return employee
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error updating employee")
    
    async def delete_employee(
        self,
        db: AsyncSession,
        employee_id: str
    ) -> bool:
        """Soft delete employee by setting status to INACTIVE"""
        employee = await self.get_employee_by_id(db, employee_id)
        
        if not employee:
            return False
        
        employee.status = EmployeeStatus.INACTIVE
        await db.commit()
        return True
    
    async def generate_salary_slip(
        self,
        db: AsyncSession,
        employee_id: str,
        month: int,
        year: int
    ) -> dict:
        """Generate salary slip for an employee"""
        employee = await self.get_employee_by_id(db, employee_id)
        
        if not employee:
            raise ValueError("Employee not found")
        
        if employee.status != EmployeeStatus.ACTIVE:
            raise ValueError("Cannot generate salary slip for inactive employee")
        
        # Validate month and year
        if month < 1 or month > 12:
            raise ValueError("Invalid month")
        
        if year < 2000 or year > 2100:
            raise ValueError("Invalid year")
        
        # Calculate salary components (basic implementation)
        basic_salary = employee.monthly_salary
        
        # In a real system, you would calculate deductions, allowances, etc.
        # For now, we'll keep it simple
        gross_salary = basic_salary
        deductions = Decimal("0.00")
        net_salary = gross_salary - deductions
        
        salary_slip = {
            "employee_id": employee.employee_id,
            "employee_name": employee.name,
            "post": employee.post,
            "month": month,
            "year": year,
            "joining_date": employee.joining_date.isoformat(),
            "employment_status": employee.employment_status.value,
            "duty_hours": employee.duty_hours,
            "basic_salary": float(basic_salary),
            "gross_salary": float(gross_salary),
            "deductions": float(deductions),
            "net_salary": float(net_salary),
            "generated_date": datetime.now().isoformat()
        }
        
        return salary_slip


# Global instance
employee_crud = EmployeeCRUD()
