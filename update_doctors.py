"""
Script to update doctors in the database
Run this on Render to update existing doctors or add new ones
"""
import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete
import os

# Import models
from app.core.database import Base
from app.models.doctor import Doctor, DoctorStatus


async def update_doctors():
    """Update doctors in database"""
    
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./hospital.db")
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    
    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        print("🔄 Updating doctors...")
        
        # Delete all existing doctors
        await session.execute(delete(Doctor))
        await session.commit()
        print("✅ Cleared existing doctors")
        
        # Add new doctors
        doctors_data = [
            {"name": "Dr. Nitish Tiwari", "department": "Orthopedics", "new_fee": 500, "followup_fee": 300},
            {"name": "Dr. Muskan Tiwari", "department": "Dentist", "new_fee": 400, "followup_fee": 250},
            {"name": "Dr. Rajesh Kumar", "department": "General Medicine", "new_fee": 300, "followup_fee": 200},
            {"name": "Dr. Priya Sharma", "department": "Pediatrics", "new_fee": 350, "followup_fee": 250},
            {"name": "Dr. Amit Singh", "department": "Surgery", "new_fee": 500, "followup_fee": 300},
        ]
        
        for idx, doc_data in enumerate(doctors_data, start=1):
            doctor = Doctor(
                doctor_id=f"DOC{idx:05d}",
                name=doc_data["name"],
                department=doc_data["department"],
                new_patient_fee=Decimal(str(doc_data["new_fee"])),
                followup_fee=Decimal(str(doc_data["followup_fee"])),
                status=DoctorStatus.ACTIVE
            )
            session.add(doctor)
        
        await session.commit()
        print(f"✅ Added {len(doctors_data)} doctors successfully")
        
        # Verify
        result = await session.execute(select(Doctor))
        doctors = result.scalars().all()
        
        print("\n📋 Current doctors in database:")
        for doctor in doctors:
            print(f"  - {doctor.name} ({doctor.department}) - ₹{doctor.new_patient_fee}/₹{doctor.followup_fee}")
    
    await engine.dispose()
    print("\n🎉 Doctor update completed!")


if __name__ == "__main__":
    asyncio.run(update_doctors())
