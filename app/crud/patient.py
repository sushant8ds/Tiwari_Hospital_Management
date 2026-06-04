"""
CRUD operations for Patient model
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError

from app.models.patient import Patient, Gender
from app.services.id_generator import generate_patient_id
from app.utils.validators import validate_mobile_number, validate_age, sanitize_string


class PatientCRUD:
    """CRUD operations for Patient model"""
    
    async def create_patient(
        self,
        db: AsyncSession,
        name: str,
        age: int,
        gender: Gender,
        address: str,
        mobile_number: str
    ) -> Patient:
        """Create a new patient with validation"""
        # Validate input data
        if not validate_mobile_number(mobile_number):
            raise ValueError("Invalid mobile number format")
        
        if not validate_age(age):
            raise ValueError("Age must be between 0 and 150")
        
        if not name or not name.strip():
            raise ValueError("Patient name is required")
        
        if not address or not address.strip():
            raise ValueError("Patient address is required")
        
        try:
            patient_id = await generate_patient_id(db)
            
            patient = Patient(
                patient_id=patient_id,
                name=sanitize_string(name),
                age=age,
                gender=gender,
                address=address.strip(),
                mobile_number=mobile_number
            )
            
            db.add(patient)
            await db.commit()
            await db.refresh(patient)
            return patient
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Mobile number already exists")
    
    async def get_patient_by_id(self, db: AsyncSession, patient_id: str) -> Optional[Patient]:
        """Get patient by ID"""
        result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        return result.scalar_one_or_none()
    
    async def get_patient_by_mobile(self, db: AsyncSession, mobile_number: str) -> Optional[Patient]:
        """Get patient by mobile number"""
        result = await db.execute(
            select(Patient).where(Patient.mobile_number == mobile_number)
        )
        return result.scalar_one_or_none()
    
    async def search_patients(
        self, 
        db: AsyncSession, 
        search_term: str,
        limit: int = 50
    ) -> List[Patient]:
        """Search patients by ID, mobile number, or name"""
        if not search_term or not search_term.strip():
            return []
        
        search_term = search_term.strip()
        
        # Search by patient ID, mobile number, or name (case-insensitive)
        result = await db.execute(
            select(Patient).where(
                or_(
                    Patient.patient_id.ilike(f"%{search_term}%"),
                    Patient.mobile_number.ilike(f"%{search_term}%"),
                    Patient.name.ilike(f"%{search_term}%")
                )
            ).limit(limit)
        )
        return result.scalars().all()
    
    async def update_patient(
        self,
        db: AsyncSession,
        patient_id: str,
        name: Optional[str] = None,
        age: Optional[int] = None,
        gender: Optional[Gender] = None,
        address: Optional[str] = None,
        mobile_number: Optional[str] = None
    ) -> Optional[Patient]:
        """Update patient details"""
        patient = await self.get_patient_by_id(db, patient_id)
        if not patient:
            return None
        
        # Validate updates
        if mobile_number and not validate_mobile_number(mobile_number):
            raise ValueError("Invalid mobile number format")
        
        if age is not None and not validate_age(age):
            raise ValueError("Age must be between 0 and 150")
        
        try:
            # Update fields if provided
            if name is not None:
                if not name.strip():
                    raise ValueError("Patient name cannot be empty")
                patient.name = sanitize_string(name)
            
            if age is not None:
                patient.age = age
            
            if gender is not None:
                patient.gender = gender
            
            if address is not None:
                if not address.strip():
                    raise ValueError("Patient address cannot be empty")
                patient.address = address.strip()
            
            if mobile_number is not None:
                patient.mobile_number = mobile_number
            
            await db.commit()
            await db.refresh(patient)
            return patient
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Mobile number already exists")
    
    async def get_patient_history(self, db: AsyncSession, patient_id: str) -> Optional[Patient]:
        """Get patient with all related visits and IPD admissions"""
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Patient)
            .options(
                selectinload(Patient.visits),
                selectinload(Patient.ipd_admissions)
            )
            .where(Patient.patient_id == patient_id)
        )
        return result.scalar_one_or_none()


# Global instance
patient_crud = PatientCRUD()