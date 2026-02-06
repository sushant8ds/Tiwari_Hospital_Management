"""
Tests for employee CRUD operations
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import date

from app.crud.employee import employee_crud
from app.models.employee import EmploymentStatus, EmployeeStatus


class TestEmployeeCRUD:
    """Test employee CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_employee(self, db_session: AsyncSession):
        """Test creating a new employee"""
        employee = await employee_crud.create_employee(
            db=db_session,
            name="John Doe",
            post="Nurse",
            employment_status=EmploymentStatus.PERMANENT,
            duty_hours=8,
            joining_date=date(2024, 1, 1),
            monthly_salary=Decimal("30000.00"),
            qualification="B.Sc Nursing"
        )
        
        assert employee.employee_id is not None
        assert employee.employee_id.startswith("EMP")
        assert employee.name == "John Doe"
        assert employee.post == "Nurse"
        assert employee.qualification == "B.Sc Nursing"
        assert employee.employment_status == EmploymentStatus.PERMANENT
        assert employee.duty_hours == 8
        assert employee.joining_date == date(2024, 1, 1)
        assert employee.monthly_salary == Decimal("30000.00")
        assert employee.status == EmployeeStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_create_employee_without_qualification(self, db_session: AsyncSession):
        """Test creating an employee without qualification"""
        employee = await employee_crud.create_employee(
            db=db_session,
            name="Jane Smith",
            post="Receptionist",
            employment_status=EmploymentStatus.PROBATION,
            duty_hours=8,
            joining_date=date(2024, 2, 1),
            monthly_salary=Decimal("20000.00")
        )
        
        assert employee.employee_id is not None
        assert employee.name == "Jane Smith"
        assert employee.qualification is None
        assert employee.employment_status == EmploymentStatus.PROBATION
    
    @pytest.mark.asyncio
    async def test_create_employee_validation(self, db_session: AsyncSession):
        """Test employee creation validation"""
        # Test empty name
        with pytest.raises(ValueError, match="Employee name is required"):
            await employee_crud.create_employee(
                db=db_session,
                name="",
                post="Nurse",
                employment_status=EmploymentStatus.PERMANENT,
                duty_hours=8,
                joining_date=date(2024, 1, 1),
                monthly_salary=Decimal("30000.00")
            )
        
        # Test empty post
        with pytest.raises(ValueError, match="Employee post is required"):
            await employee_crud.create_employee(
                db=db_session,
                name="John Doe",
                post="",
                employment_status=EmploymentStatus.PERMANENT,
                duty_hours=8,
                joining_date=date(2024, 1, 1),
                monthly_salary=Decimal("30000.00")
            )
        
        # Test negative duty hours
        with pytest.raises(ValueError, match="Duty hours must be positive"):
            await employee_crud.create_employee(
                db=db_session,
                name="John Doe",
                post="Nurse",
                employment_status=EmploymentStatus.PERMANENT,
                duty_hours=-1,
                joining_date=date(2024, 1, 1),
                monthly_salary=Decimal("30000.00")
            )
        
        # Test negative salary
        with pytest.raises(ValueError, match="Monthly salary cannot be negative"):
            await employee_crud.create_employee(
                db=db_session,
                name="John Doe",
                post="Nurse",
                employment_status=EmploymentStatus.PERMANENT,
                duty_hours=8,
                joining_date=date(2024, 1, 1),
                monthly_salary=Decimal("-1000.00")
            )
    
    @pytest.mark.asyncio
    async def test_get_employee_by_id(self, db_session: AsyncSession):
        """Test getting employee by ID"""
        # Create employee
        employee = await employee_crud.create_employee(
            db=db_session,
            name="Test Employee",
            post="Technician",
            employment_status=EmploymentStatus.PERMANENT,
            duty_hours=8,
            joining_date=date(2024, 1, 1),
            monthly_salary=Decimal("25000.00")
        )
        
        # Get employee by ID
        retrieved = await employee_crud.get_employee_by_id(db_session, employee.employee_id)
        
        assert retrieved is not None
        assert retrieved.employee_id == employee.employee_id
        assert retrieved.name == "Test Employee"
    
    @pytest.mark.asyncio
    async def test_get_employee_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent employee"""
        employee = await employee_crud.get_employee_by_id(db_session, "EMP99999999999")
        assert employee is None
    
    @pytest.mark.asyncio
    async def test_get_all_employees(self, db_session: AsyncSession):
        """Test getting all employees"""
        # Create multiple employees
        await employee_crud.create_employee(
            db=db_session,
            name="Employee 1",
            post="Nurse",
            employment_status=EmploymentStatus.PERMANENT,
            duty_hours=8,
            joining_date=date(2024, 1, 1),
            monthly_salary=Decimal("30000.00")
        )
        
        await employee_crud.create_employee(
            db=db_session,
            name="Employee 2",
            post="Doctor",
            employment_status=EmploymentStatus.PERMANENT,
            duty_hours=10,
            joining_date=date(2024, 1, 15),
            monthly_salary=Decimal("80000.00")
        )
        
        # Get all employees
        employees = await employee_crud.get_all_employees(db_session)
        
        assert len(employees) >= 2
    
    @pytest.mark.asyncio
    async def test_get_all_employees_filtered_by_status(self, db_session: AsyncSession):
        """Test getting employees filtered by status"""
        # Create active employee
        active_emp = await employee_crud.create_employee(
            db=db_session,
            name="Active Employee",
            post="Nurse",
            employment_status=EmploymentStatus.PERMANENT,
            duty_hours=8,
            joining_date=date(2024, 1, 1),
            monthly_salary=Decimal("30000.00")
        )
        
        # Create and deactivate another employee
        inactive_emp = await employee_crud.create_employee(
            db=db_session,
            name="Inactive Employee",
            post="Technician",
            employment_status=EmploymentStatus.PERMANENT,
            duty_hours=8,
            joining_date=date(2024, 1, 1),
            monthly_salary=Decimal("25000.00")
        )
        await employee_crud.delete_employee(db_session, inactive_emp.employee_id)
        
        # Get only active employees
        active_employees = await employee_crud.get_all_employees(
            db_session,
            status=EmployeeStatus.ACTIVE
        )
        
        assert all(emp.status == EmployeeStatus.ACTIVE for emp in active_employees)
    
    @pytest.mark.asyncio
    async def test_update_employee(self, db_session: AsyncSession):
        """Test updating employee details"""
        # Create employee
        employee = await employee_crud.create_employee(
            db=db_session,
            name="Original Name",
            post="Nurse",
            employment_status=EmploymentStatus.PROBATION,
            duty_hours=8,
            joining_date=date(2024, 1, 1),
            monthly_salary=Decimal("25000.00")
        )
        
        # Update employee
        updated = await employee_crud.update_employee(
            db=db_session,
            employee_id=employee.employee_id,
            name="Updated Name",
            post="Senior Nurse",
            employment_status=EmploymentStatus.PERMANENT,
            monthly_salary=Decimal("35000.00")
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.post == "Senior Nurse"
        assert updated.employment_status == EmploymentStatus.PERMANENT
        assert updated.monthly_salary == Decimal("35000.00")
        assert updated.duty_hours == 8  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_employee_not_found(self, db_session: AsyncSession):
        """Test updating non-existent employee"""
        updated = await employee_crud.update_employee(
            db=db_session,
            employee_id="EMP99999999999",
            name="New Name"
        )
        
        assert updated is None
    
    @pytest.mark.asyncio
    async def test_delete_employee(self, db_session: AsyncSession):
        """Test soft deleting employee"""
        # Create employee
        employee = await employee_crud.create_employee(
            db=db_session,
            name="To Delete",
            post="Nurse",
            employment_status=EmploymentStatus.PERMANENT,
            duty_hours=8,
            joining_date=date(2024, 1, 1),
            monthly_salary=Decimal("30000.00")
        )
        
        # Delete employee
        success = await employee_crud.delete_employee(db_session, employee.employee_id)
        assert success is True
        
        # Verify employee is inactive
        deleted = await employee_crud.get_employee_by_id(db_session, employee.employee_id)
        assert deleted is not None
        assert deleted.status == EmployeeStatus.INACTIVE
    
    @pytest.mark.asyncio
    async def test_delete_employee_not_found(self, db_session: AsyncSession):
        """Test deleting non-existent employee"""
        success = await employee_crud.delete_employee(db_session, "EMP99999999999")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_generate_salary_slip(self, db_session: AsyncSession):
        """Test generating salary slip"""
        # Create employee
        employee = await employee_crud.create_employee(
            db=db_session,
            name="Salary Test",
            post="Nurse",
            employment_status=EmploymentStatus.PERMANENT,
            duty_hours=8,
            joining_date=date(2024, 1, 1),
            monthly_salary=Decimal("30000.00")
        )
        
        # Generate salary slip
        slip = await employee_crud.generate_salary_slip(
            db=db_session,
            employee_id=employee.employee_id,
            month=1,
            year=2024
        )
        
        assert slip["employee_id"] == employee.employee_id
        assert slip["employee_name"] == "Salary Test"
        assert slip["post"] == "Nurse"
        assert slip["month"] == 1
        assert slip["year"] == 2024
        assert slip["basic_salary"] == 30000.00
        assert slip["net_salary"] == 30000.00
    
    @pytest.mark.asyncio
    async def test_generate_salary_slip_inactive_employee(self, db_session: AsyncSession):
        """Test generating salary slip for inactive employee"""
        # Create and deactivate employee
        employee = await employee_crud.create_employee(
            db=db_session,
            name="Inactive Test",
            post="Nurse",
            employment_status=EmploymentStatus.PERMANENT,
            duty_hours=8,
            joining_date=date(2024, 1, 1),
            monthly_salary=Decimal("30000.00")
        )
        await employee_crud.delete_employee(db_session, employee.employee_id)
        
        # Try to generate salary slip
        with pytest.raises(ValueError, match="Cannot generate salary slip for inactive employee"):
            await employee_crud.generate_salary_slip(
                db=db_session,
                employee_id=employee.employee_id,
                month=1,
                year=2024
            )
    
    @pytest.mark.asyncio
    async def test_generate_salary_slip_validation(self, db_session: AsyncSession):
        """Test salary slip generation validation"""
        # Create employee
        employee = await employee_crud.create_employee(
            db=db_session,
            name="Validation Test",
            post="Nurse",
            employment_status=EmploymentStatus.PERMANENT,
            duty_hours=8,
            joining_date=date(2024, 1, 1),
            monthly_salary=Decimal("30000.00")
        )
        
        # Test invalid month
        with pytest.raises(ValueError, match="Invalid month"):
            await employee_crud.generate_salary_slip(
                db=db_session,
                employee_id=employee.employee_id,
                month=13,
                year=2024
            )
        
        # Test invalid year
        with pytest.raises(ValueError, match="Invalid year"):
            await employee_crud.generate_salary_slip(
                db=db_session,
                employee_id=employee.employee_id,
                month=1,
                year=1999
            )
