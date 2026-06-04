"""
CRUD operations for Doctor model
"""

from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.doctor import Doctor, DoctorStatus
from app.services.id_generator import generate_user_id  # Reuse for doctor IDs
from app.utils.validators import sanitize_string


class DoctorCRUD:
    """CRUD operations for Doctor model"""
    
    async def create_doctor(
        self,
        db: AsyncSession,
        name: str,
        department: str,
        new_patient_fee: Decimal,
        followup_fee: Decimal,
        status: DoctorStatus = DoctorStatus.ACTIVE
    ) -> Doctor:
        """Create a new doctor with validation"""
        # Validate input data
        if not name or not name.strip():
            raise ValueError("Doctor name is required")
        
        if not department or not department.strip():
            raise ValueError("Department is required")
        
        if new_patient_fee < 0:
            raise ValueError("New patient fee cannot be negative")
        
        if followup_fee < 0:
            raise ValueError("Follow-up fee cannot be negative")
        
        try:
            # Generate doctor ID using similar pattern as user ID
            doctor_id = await generate_user_id(db)
            doctor_id = doctor_id.replace("U", "D")  # Replace U with D for doctor
            
            doctor = Doctor(
                doctor_id=doctor_id,
                name=sanitize_string(name),
                department=department.strip().title(),
                new_patient_fee=new_patient_fee,
                followup_fee=followup_fee,
                status=status
            )
            
            db.add(doctor)
            await db.commit()
            await db.refresh(doctor)
            return doctor
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error creating doctor record")
    
    async def get_doctor_by_id(self, db: AsyncSession, doctor_id: str) -> Optional[Doctor]:
        """Get doctor by ID"""
        result = await db.execute(
            select(Doctor).where(Doctor.doctor_id == doctor_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_doctors(self, db: AsyncSession) -> List[Doctor]:
        """Get all active doctors"""
        result = await db.execute(
            select(Doctor)
            .where(Doctor.status == DoctorStatus.ACTIVE)
            .order_by(Doctor.name)
        )
        return result.scalars().all()
    
    async def get_doctors_by_department(
        self, 
        db: AsyncSession, 
        department: str
    ) -> List[Doctor]:
        """Get active doctors by department"""
        result = await db.execute(
            select(Doctor)
            .where(
                Doctor.department.ilike(f"%{department}%"),
                Doctor.status == DoctorStatus.ACTIVE
            )
            .order_by(Doctor.name)
        )
        return result.scalars().all()
    
    async def update_doctor(
        self,
        db: AsyncSession,
        doctor_id: str,
        name: Optional[str] = None,
        department: Optional[str] = None,
        new_patient_fee: Optional[Decimal] = None,
        followup_fee: Optional[Decimal] = None,
        status: Optional[DoctorStatus] = None
    ) -> Optional[Doctor]:
        """Update doctor details"""
        doctor = await self.get_doctor_by_id(db, doctor_id)
        if not doctor:
            return None
        
        # Validate updates
        if new_patient_fee is not None and new_patient_fee < 0:
            raise ValueError("New patient fee cannot be negative")
        
        if followup_fee is not None and followup_fee < 0:
            raise ValueError("Follow-up fee cannot be negative")
        
        try:
            # Update fields if provided
            if name is not None:
                if not name.strip():
                    raise ValueError("Doctor name cannot be empty")
                doctor.name = sanitize_string(name)
            
            if department is not None:
                if not department.strip():
                    raise ValueError("Department cannot be empty")
                doctor.department = department.strip().title()
            
            if new_patient_fee is not None:
                doctor.new_patient_fee = new_patient_fee
            
            if followup_fee is not None:
                doctor.followup_fee = followup_fee
            
            if status is not None:
                doctor.status = status
            
            await db.commit()
            await db.refresh(doctor)
            return doctor
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error updating doctor record")
    
    async def get_doctor_with_visits(self, db: AsyncSession, doctor_id: str) -> Optional[Doctor]:
        """Get doctor with all related visits"""
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Doctor)
            .options(selectinload(Doctor.visits))
            .where(Doctor.doctor_id == doctor_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_departments(self, db: AsyncSession) -> List[str]:
        """Get all unique departments from active doctors"""
        result = await db.execute(
            select(Doctor.department)
            .where(Doctor.status == DoctorStatus.ACTIVE)
            .distinct()
            .order_by(Doctor.department)
        )
        return [dept for dept in result.scalars().all() if dept]


# Global instance
doctor_crud = DoctorCRUD()