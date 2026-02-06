"""
CRUD operations for Visit model
"""

from typing import Optional, List
from datetime import date, time, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError

from app.models.visit import Visit, VisitType, PaymentMode, VisitStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.services.id_generator import generate_visit_id


class VisitCRUD:
    """CRUD operations for Visit model"""
    
    async def _get_next_serial_number(
        self, 
        db: AsyncSession, 
        doctor_id: str, 
        visit_date: date
    ) -> int:
        """Get next serial number for doctor on given date"""
        result = await db.execute(
            select(func.max(Visit.serial_number))
            .where(
                and_(
                    Visit.doctor_id == doctor_id,
                    Visit.visit_date == visit_date
                )
            )
        )
        max_serial = result.scalar()
        return (max_serial or 0) + 1
    
    async def create_visit(
        self,
        db: AsyncSession,
        patient_id: str,
        doctor_id: str,
        visit_type: VisitType,
        payment_mode: PaymentMode,
        visit_date: Optional[date] = None,
        visit_time: Optional[time] = None
    ) -> Visit:
        """Create a new visit with automatic serial number generation"""
        # Validate patient exists
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        if not patient:
            raise ValueError("Patient not found")
        
        # Validate doctor exists and is active
        doctor_result = await db.execute(
            select(Doctor).where(Doctor.doctor_id == doctor_id)
        )
        doctor = doctor_result.scalar_one_or_none()
        if not doctor:
            raise ValueError("Doctor not found")
        
        # Use current date/time if not provided
        if visit_date is None:
            visit_date = date.today()
        if visit_time is None:
            visit_time = datetime.now().time()
        
        # Determine OPD fee based on visit type
        if visit_type == VisitType.OPD_NEW:
            opd_fee = doctor.new_patient_fee
        else:
            opd_fee = doctor.followup_fee
        
        try:
            # Generate unique visit ID
            visit_id = await generate_visit_id(db)
            
            # Get next serial number for this doctor on this date
            serial_number = await self._get_next_serial_number(db, doctor_id, visit_date)
            
            visit = Visit(
                visit_id=visit_id,
                patient_id=patient_id,
                visit_type=visit_type,
                doctor_id=doctor_id,
                department=doctor.department,
                serial_number=serial_number,
                visit_date=visit_date,
                visit_time=visit_time,
                opd_fee=opd_fee,
                payment_mode=payment_mode,
                status=VisitStatus.ACTIVE
            )
            
            db.add(visit)
            await db.commit()
            await db.refresh(visit)
            return visit
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error creating visit record")
    
    async def get_visit_by_id(self, db: AsyncSession, visit_id: str) -> Optional[Visit]:
        """Get visit by ID"""
        result = await db.execute(
            select(Visit).where(Visit.visit_id == visit_id)
        )
        return result.scalar_one_or_none()
    
    async def get_visit_with_details(self, db: AsyncSession, visit_id: str) -> Optional[Visit]:
        """Get visit with patient and doctor details"""
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Visit)
            .options(
                selectinload(Visit.patient),
                selectinload(Visit.doctor),
                selectinload(Visit.billing_charges)
            )
            .where(Visit.visit_id == visit_id)
        )
        return result.scalar_one_or_none()
    
    async def get_daily_visits(
        self, 
        db: AsyncSession, 
        visit_date: date,
        doctor_id: Optional[str] = None
    ) -> List[Visit]:
        """Get all visits for a specific date, optionally filtered by doctor"""
        query = select(Visit).where(Visit.visit_date == visit_date)
        
        if doctor_id:
            query = query.where(Visit.doctor_id == doctor_id)
        
        query = query.order_by(Visit.serial_number)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_patient_visits(
        self, 
        db: AsyncSession, 
        patient_id: str,
        limit: int = 50
    ) -> List[Visit]:
        """Get all visits for a patient"""
        result = await db.execute(
            select(Visit)
            .where(Visit.patient_id == patient_id)
            .order_by(Visit.visit_date.desc(), Visit.visit_time.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update_visit_status(
        self,
        db: AsyncSession,
        visit_id: str,
        status: VisitStatus
    ) -> Optional[Visit]:
        """Update visit status"""
        visit = await self.get_visit_by_id(db, visit_id)
        if not visit:
            return None
        
        visit.status = status
        await db.commit()
        await db.refresh(visit)
        return visit
    
    async def get_doctor_daily_count(
        self, 
        db: AsyncSession, 
        doctor_id: str, 
        visit_date: date
    ) -> int:
        """Get count of visits for a doctor on a specific date"""
        result = await db.execute(
            select(func.count(Visit.visit_id))
            .where(
                and_(
                    Visit.doctor_id == doctor_id,
                    Visit.visit_date == visit_date
                )
            )
        )
        return result.scalar() or 0
    
    async def get_follow_up_patients(
        self, 
        db: AsyncSession, 
        search_term: str,
        limit: int = 20
    ) -> List[dict]:
        """Get patients eligible for follow-up visits"""
        from sqlalchemy.orm import selectinload
        
        # Search for patients who have had previous visits
        subquery = select(Visit.patient_id).distinct()
        
        if search_term.strip():
            # Search by patient ID or mobile number
            patient_query = select(Patient).options(selectinload(Patient.visits)).where(
                and_(
                    Patient.patient_id.in_(subquery),
                    or_(
                        Patient.patient_id.ilike(f"%{search_term}%"),
                        Patient.mobile_number.ilike(f"%{search_term}%")
                    )
                )
            ).limit(limit)
        else:
            patient_query = select(Patient).options(selectinload(Patient.visits)).where(
                Patient.patient_id.in_(subquery)
            ).limit(limit)
        
        result = await db.execute(patient_query)
        patients = result.scalars().all()
        
        # Return patient data with last visit info
        follow_up_data = []
        for patient in patients:
            if patient.visits:
                last_visit = max(patient.visits, key=lambda v: (v.visit_date, v.visit_time))
                follow_up_data.append({
                    "patient": patient,
                    "last_visit": last_visit,
                    "last_doctor": last_visit.doctor if hasattr(last_visit, 'doctor') else None
                })
        
        return follow_up_data
    
    async def get_recent_visits(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Visit]:
        """Get recent visits with patient and doctor information"""
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Visit)
            .options(selectinload(Visit.patient))
            .options(selectinload(Visit.doctor))
            .order_by(Visit.created_date.desc())
            .limit(limit)
        )
        return result.scalars().all()


# Global instance
visit_crud = VisitCRUD()

