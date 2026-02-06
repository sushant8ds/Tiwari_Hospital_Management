"""
CRUD operations for IPD model
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError

from app.models.ipd import IPD, IPDStatus
from app.models.bed import Bed, BedStatus, WardType
from app.models.patient import Patient
from app.models.visit import Visit
from app.services.id_generator import generate_ipd_id


class IPDCRUD:
    """CRUD operations for IPD model"""
    
    async def admit_patient(
        self,
        db: AsyncSession,
        patient_id: str,
        bed_id: str,
        file_charge: Decimal,
        visit_id: Optional[str] = None,
        admission_date: Optional[datetime] = None
    ) -> IPD:
        """Admit a patient to IPD"""
        # Validate patient exists
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        if not patient:
            raise ValueError("Patient not found")
        
        # Validate bed exists and is available
        bed_result = await db.execute(
            select(Bed).where(Bed.bed_id == bed_id)
        )
        bed = bed_result.scalar_one_or_none()
        if not bed:
            raise ValueError("Bed not found")
        
        if bed.status != BedStatus.AVAILABLE:
            raise ValueError(f"Bed {bed.bed_number} is not available")
        
        # Validate visit if provided
        if visit_id:
            visit_result = await db.execute(
                select(Visit).where(Visit.visit_id == visit_id)
            )
            visit = visit_result.scalar_one_or_none()
            if not visit:
                raise ValueError("Visit not found")
            
            if visit.patient_id != patient_id:
                raise ValueError("Visit does not belong to this patient")
        
        # Validate file charge
        if file_charge < 0:
            raise ValueError("File charge cannot be negative")
        
        try:
            # Generate unique IPD ID
            ipd_id = await generate_ipd_id(db)
            
            # Create IPD admission
            ipd = IPD(
                ipd_id=ipd_id,
                patient_id=patient_id,
                visit_id=visit_id,
                admission_date=admission_date or datetime.now(),
                file_charge=file_charge,
                bed_id=bed_id,
                status=IPDStatus.ADMITTED
            )
            
            # Mark bed as occupied
            bed.status = BedStatus.OCCUPIED
            
            db.add(ipd)
            await db.commit()
            await db.refresh(ipd)
            return ipd
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error creating IPD admission")
    
    async def get_ipd_by_id(
        self, 
        db: AsyncSession, 
        ipd_id: str
    ) -> Optional[IPD]:
        """Get IPD admission by ID"""
        result = await db.execute(
            select(IPD).where(IPD.ipd_id == ipd_id)
        )
        return result.scalar_one_or_none()
    
    async def get_ipd_by_patient(
        self, 
        db: AsyncSession, 
        patient_id: str,
        status: Optional[IPDStatus] = None
    ) -> List[IPD]:
        """Get all IPD admissions for a patient"""
        query = select(IPD).where(IPD.patient_id == patient_id)
        
        if status:
            query = query.where(IPD.status == status)
        
        result = await db.execute(query.order_by(IPD.admission_date.desc()))
        return result.scalars().all()
    
    async def get_active_ipd_admissions(
        self, 
        db: AsyncSession
    ) -> List[IPD]:
        """Get all active IPD admissions with patient and bed details"""
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(IPD)
            .options(selectinload(IPD.patient))
            .options(selectinload(IPD.bed))
            .where(IPD.status == IPDStatus.ADMITTED)
            .order_by(IPD.admission_date.desc())
        )
        return result.scalars().all()
    
    async def change_bed(
        self,
        db: AsyncSession,
        ipd_id: str,
        new_bed_id: str
    ) -> IPD:
        """Change bed allocation for an IPD patient"""
        # Get IPD admission
        ipd = await self.get_ipd_by_id(db, ipd_id)
        if not ipd:
            raise ValueError("IPD admission not found")
        
        if ipd.status != IPDStatus.ADMITTED:
            raise ValueError("Can only change bed for admitted patients")
        
        # Get current bed
        current_bed_result = await db.execute(
            select(Bed).where(Bed.bed_id == ipd.bed_id)
        )
        current_bed = current_bed_result.scalar_one_or_none()
        
        # Get new bed
        new_bed_result = await db.execute(
            select(Bed).where(Bed.bed_id == new_bed_id)
        )
        new_bed = new_bed_result.scalar_one_or_none()
        if not new_bed:
            raise ValueError("New bed not found")
        
        if new_bed.status != BedStatus.AVAILABLE:
            raise ValueError(f"Bed {new_bed.bed_number} is not available")
        
        try:
            # Update bed statuses
            if current_bed:
                current_bed.status = BedStatus.AVAILABLE
            new_bed.status = BedStatus.OCCUPIED
            
            # Update IPD bed allocation
            ipd.bed_id = new_bed_id
            
            await db.commit()
            await db.refresh(ipd)
            return ipd
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error changing bed")
    
    async def discharge_patient(
        self,
        db: AsyncSession,
        ipd_id: str,
        discharge_date: Optional[datetime] = None
    ) -> IPD:
        """Discharge a patient from IPD"""
        # Get IPD admission
        ipd = await self.get_ipd_by_id(db, ipd_id)
        if not ipd:
            raise ValueError("IPD admission not found")
        
        if ipd.status != IPDStatus.ADMITTED:
            raise ValueError("Patient is not currently admitted")
        
        # Get bed
        bed_result = await db.execute(
            select(Bed).where(Bed.bed_id == ipd.bed_id)
        )
        bed = bed_result.scalar_one_or_none()
        
        try:
            # Update IPD status
            ipd.status = IPDStatus.DISCHARGED
            ipd.discharge_date = discharge_date or datetime.now()
            
            # Mark bed as available
            if bed:
                bed.status = BedStatus.AVAILABLE
            
            await db.commit()
            await db.refresh(ipd)
            return ipd
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error discharging patient")
    
    async def calculate_bed_charges(
        self,
        db: AsyncSession,
        ipd_id: str
    ) -> Decimal:
        """Calculate total bed charges for an IPD admission"""
        # Get IPD admission
        ipd = await self.get_ipd_by_id(db, ipd_id)
        if not ipd:
            raise ValueError("IPD admission not found")
        
        # Get bed
        bed_result = await db.execute(
            select(Bed).where(Bed.bed_id == ipd.bed_id)
        )
        bed = bed_result.scalar_one_or_none()
        if not bed:
            raise ValueError("Bed not found")
        
        # Calculate number of days
        end_date = ipd.discharge_date or datetime.now()
        days = (end_date - ipd.admission_date).days
        
        # Minimum 1 day charge
        if days < 1:
            days = 1
        
        # Calculate total bed charges
        total_bed_charges = bed.per_day_charge * days
        
        return Decimal(str(total_bed_charges)).quantize(Decimal("0.01"))


class BedCRUD:
    """CRUD operations for Bed model"""
    
    async def create_bed(
        self,
        db: AsyncSession,
        bed_number: str,
        ward_type: WardType,
        per_day_charge: Decimal
    ) -> Bed:
        """Create a new bed"""
        # Validate input
        if not bed_number or not bed_number.strip():
            raise ValueError("Bed number is required")
        
        if per_day_charge < 0:
            raise ValueError("Per day charge cannot be negative")
        
        # Check if bed number already exists
        existing_bed_result = await db.execute(
            select(Bed).where(Bed.bed_number == bed_number.strip())
        )
        existing_bed = existing_bed_result.scalar_one_or_none()
        if existing_bed:
            raise ValueError(f"Bed number {bed_number} already exists")
        
        try:
            # Generate bed ID with microseconds for uniqueness
            import time
            bed_id = f"BED{datetime.now().strftime('%Y%m%d%H%M%S')}{int(time.time() * 1000000) % 1000000:06d}"
            
            bed = Bed(
                bed_id=bed_id,
                bed_number=bed_number.strip(),
                ward_type=ward_type,
                per_day_charge=per_day_charge,
                status=BedStatus.AVAILABLE
            )
            
            db.add(bed)
            await db.commit()
            await db.refresh(bed)
            return bed
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error creating bed")
    
    async def get_bed_by_id(
        self, 
        db: AsyncSession, 
        bed_id: str
    ) -> Optional[Bed]:
        """Get bed by ID"""
        result = await db.execute(
            select(Bed).where(Bed.bed_id == bed_id)
        )
        return result.scalar_one_or_none()
    
    async def get_bed_by_number(
        self, 
        db: AsyncSession, 
        bed_number: str
    ) -> Optional[Bed]:
        """Get bed by bed number"""
        result = await db.execute(
            select(Bed).where(Bed.bed_number == bed_number)
        )
        return result.scalar_one_or_none()
    
    async def get_beds_by_ward_type(
        self, 
        db: AsyncSession, 
        ward_type: WardType,
        status: Optional[BedStatus] = None
    ) -> List[Bed]:
        """Get beds by ward type"""
        query = select(Bed).where(Bed.ward_type == ward_type)
        
        if status:
            query = query.where(Bed.status == status)
        
        result = await db.execute(query.order_by(Bed.bed_number))
        return result.scalars().all()
    
    async def get_available_beds(
        self, 
        db: AsyncSession,
        ward_type: Optional[WardType] = None
    ) -> List[Bed]:
        """Get all available beds"""
        query = select(Bed).where(Bed.status == BedStatus.AVAILABLE)
        
        if ward_type:
            query = query.where(Bed.ward_type == ward_type)
        
        result = await db.execute(query.order_by(Bed.ward_type, Bed.bed_number))
        return result.scalars().all()
    
    async def get_bed_occupancy_stats(
        self, 
        db: AsyncSession
    ) -> dict:
        """Get bed occupancy statistics"""
        # Get all beds
        all_beds_result = await db.execute(select(Bed))
        all_beds = all_beds_result.scalars().all()
        
        # Calculate statistics
        total_beds = len(all_beds)
        occupied_beds = sum(1 for bed in all_beds if bed.status == BedStatus.OCCUPIED)
        available_beds = sum(1 for bed in all_beds if bed.status == BedStatus.AVAILABLE)
        maintenance_beds = sum(1 for bed in all_beds if bed.status == BedStatus.MAINTENANCE)
        
        # Calculate by ward type
        ward_stats = {}
        for ward_type in WardType:
            ward_beds = [bed for bed in all_beds if bed.ward_type == ward_type]
            ward_stats[ward_type.value] = {
                "total": len(ward_beds),
                "occupied": sum(1 for bed in ward_beds if bed.status == BedStatus.OCCUPIED),
                "available": sum(1 for bed in ward_beds if bed.status == BedStatus.AVAILABLE),
                "maintenance": sum(1 for bed in ward_beds if bed.status == BedStatus.MAINTENANCE)
            }
        
        return {
            "total_beds": total_beds,
            "occupied": occupied_beds,
            "available": available_beds,
            "maintenance": maintenance_beds,
            "occupancy_rate": round((occupied_beds / total_beds * 100) if total_beds > 0 else 0, 2),
            "by_ward_type": ward_stats
        }
    
    async def update_bed_status(
        self,
        db: AsyncSession,
        bed_id: str,
        status: BedStatus
    ) -> Bed:
        """Update bed status"""
        bed = await self.get_bed_by_id(db, bed_id)
        if not bed:
            raise ValueError("Bed not found")
        
        try:
            bed.status = status
            await db.commit()
            await db.refresh(bed)
            return bed
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error updating bed status")


# Global instances
ipd_crud = IPDCRUD()
bed_crud = BedCRUD()
