"""
Initialize database for Render deployment
This script creates tables, adds doctors, and adds beds
"""
import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.core.database import Base
from app.core.config import settings
from app.models.doctor import Doctor, DoctorStatus
from app.models.bed import Bed, WardType, BedStatus


def generate_doctor_id(index: int) -> str:
    """Generate doctor ID"""
    return f"DOC{index:05d}"


def generate_bed_id(index: int) -> str:
    """Generate bed ID"""
    return f"BED{index:05d}"


async def init_database():
    """Initialize database with tables, doctors, and beds"""
    
    # Create engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully")
    
    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Add doctors
    async with async_session() as session:
        # Check if doctors already exist
        result = await session.execute(select(Doctor))
        existing_doctors = result.scalars().all()
        
        if not existing_doctors:
            doctors_data = [
                {"name": "Dr. Nitish Tiwari", "department": "Orthopedics", "new_fee": 500, "followup_fee": 300},
                {"name": "Dr. Muskan Tiwari", "department": "Dentist", "new_fee": 400, "followup_fee": 250},
                {"name": "Dr. Rajesh Kumar", "department": "General Medicine", "new_fee": 300, "followup_fee": 200},
                {"name": "Dr. Priya Sharma", "department": "Pediatrics", "new_fee": 350, "followup_fee": 250},
                {"name": "Dr. Amit Singh", "department": "Surgery", "new_fee": 500, "followup_fee": 300},
            ]
            
            for idx, doc_data in enumerate(doctors_data, start=1):
                doctor = Doctor(
                    doctor_id=generate_doctor_id(idx),
                    name=doc_data["name"],
                    department=doc_data["department"],
                    new_patient_fee=Decimal(str(doc_data["new_fee"])),
                    followup_fee=Decimal(str(doc_data["followup_fee"])),
                    status=DoctorStatus.ACTIVE
                )
                session.add(doctor)
            
            await session.commit()
            print(f"✅ Added {len(doctors_data)} doctors successfully")
        else:
            print(f"ℹ️  {len(existing_doctors)} doctors already exist")
    
    # Add beds
    async with async_session() as session:
        # Check if beds already exist
        result = await session.execute(select(Bed))
        existing_beds = result.scalars().all()
        
        if not existing_beds:
            beds_data = [
                {"ward": WardType.GENERAL, "count": 10, "charge": 500},
                {"ward": WardType.SEMI_PRIVATE, "count": 5, "charge": 1000},
                {"ward": WardType.PRIVATE, "count": 5, "charge": 2000},
            ]
            
            bed_counter = 1
            for ward_info in beds_data:
                for i in range(1, ward_info["count"] + 1):
                    bed = Bed(
                        bed_id=generate_bed_id(bed_counter),
                        bed_number=f"{ward_info['ward'].value[:3]}-{i:02d}",
                        ward_type=ward_info["ward"],
                        per_day_charge=Decimal(str(ward_info["charge"])),
                        status=BedStatus.AVAILABLE
                    )
                    session.add(bed)
                    bed_counter += 1
            
            await session.commit()
            total_beds = sum(w["count"] for w in beds_data)
            print(f"✅ Added {total_beds} beds successfully")
        else:
            print(f"ℹ️  {len(existing_beds)} beds already exist")
    
    await engine.dispose()
    print("\n🎉 Database initialization completed successfully!")


if __name__ == "__main__":
    asyncio.run(init_database())
