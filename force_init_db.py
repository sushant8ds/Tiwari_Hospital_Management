"""
Force database reinitialization
This will delete existing database and create fresh one with data
"""
import asyncio
import os
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


async def force_init():
    """Force reinitialize database"""
    
    print("\n" + "="*60)
    print("FORCE DATABASE REINITIALIZATION")
    print("="*60)
    
    # Delete existing database if it exists
    db_file = "hospital.db"
    if os.path.exists(db_file):
        print(f"\n⚠️  Deleting existing database: {db_file}")
        os.remove(db_file)
        print("✅ Old database deleted")
    else:
        print(f"\nℹ️  No existing database found at: {db_file}")
    
    # Create engine
    print(f"\n📊 Creating new database...")
    print(f"   Database URL: {settings.DATABASE_URL}")
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )
    
    # Create all tables
    print("\n1. CREATING TABLES")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   ✅ All tables created successfully")
    
    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Add doctors
    print("\n2. ADDING DOCTORS")
    async with async_session() as session:
        doctors_data = [
            {"name": "Dr. Rajesh Kumar", "department": "General Medicine", "new_fee": 300, "followup_fee": 200},
            {"name": "Dr. Priya Sharma", "department": "Pediatrics", "new_fee": 350, "followup_fee": 250},
            {"name": "Dr. Amit Singh", "department": "Surgery", "new_fee": 500, "followup_fee": 300},
            {"name": "Dr. Sunita Verma", "department": "Gynecology", "new_fee": 400, "followup_fee": 250},
            {"name": "Dr. Vikram Patel", "department": "Orthopedics", "new_fee": 450, "followup_fee": 300},
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
            print(f"   + {doctor.name} ({doctor.department})")
        
        await session.commit()
        print(f"   ✅ Added {len(doctors_data)} doctors")
    
    # Add beds
    print("\n3. ADDING BEDS")
    async with async_session() as session:
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
                if bed_counter <= 3:  # Show first 3
                    print(f"   + {bed.bed_number} ({bed.ward_type.value}) - ₹{bed.per_day_charge}/day")
                bed_counter += 1
        
        print(f"   ... and {bed_counter - 4} more beds")
        await session.commit()
        total_beds = sum(w["count"] for w in beds_data)
        print(f"   ✅ Added {total_beds} beds")
    
    # Verify data
    print("\n4. VERIFICATION")
    async with async_session() as session:
        # Count doctors
        result = await session.execute(select(Doctor))
        doctors = result.scalars().all()
        print(f"   ✅ Verified {len(doctors)} doctors in database")
        
        # Count beds
        result = await session.execute(select(Bed))
        beds = result.scalars().all()
        print(f"   ✅ Verified {len(beds)} beds in database")
    
    await engine.dispose()
    
    print("\n" + "="*60)
    print("✅ DATABASE REINITIALIZATION COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Restart your Render service (if needed)")
    print("2. Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)")
    print("3. Visit OPD → New Patient")
    print("4. Doctors should now appear in dropdown!")
    print("\n")


if __name__ == "__main__":
    asyncio.run(force_init())
