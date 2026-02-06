"""
Initialize database for Render deployment
This script creates tables, adds doctors, and adds beds
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import Base
from app.core.config import settings
from app.models.doctor import Doctor
from app.models.bed import Bed
from app.services.id_generator import generate_doctor_id, generate_bed_id


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
        from sqlalchemy import select
        result = await session.execute(select(Doctor))
        existing_doctors = result.scalars().all()
        
        if not existing_doctors:
            doctors_data = [
                {"name": "Dr. Rajesh Kumar", "specialization": "General Physician", "department": "OPD"},
                {"name": "Dr. Priya Sharma", "specialization": "Pediatrician", "department": "OPD"},
                {"name": "Dr. Amit Singh", "specialization": "Surgeon", "department": "Surgery"},
                {"name": "Dr. Sunita Verma", "specialization": "Gynecologist", "department": "OPD"},
                {"name": "Dr. Vikram Patel", "specialization": "Orthopedic", "department": "Orthopedics"},
            ]
            
            for doc_data in doctors_data:
                doctor = Doctor(
                    doctor_id=generate_doctor_id(),
                    name=doc_data["name"],
                    specialization=doc_data["specialization"],
                    department=doc_data["department"],
                    phone="9999999999",
                    email=f"{doc_data['name'].lower().replace(' ', '').replace('.', '')}@hospital.com",
                    is_active=True
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
            wards = ["General Ward", "ICU", "Private Ward", "Emergency"]
            beds_per_ward = 5
            
            for ward in wards:
                for i in range(1, beds_per_ward + 1):
                    bed = Bed(
                        bed_id=generate_bed_id(),
                        bed_number=f"{ward[:3].upper()}-{i:02d}",
                        ward=ward,
                        bed_type="Standard" if ward == "General Ward" else "Special",
                        is_occupied=False
                    )
                    session.add(bed)
            
            await session.commit()
            total_beds = len(wards) * beds_per_ward
            print(f"✅ Added {total_beds} beds successfully")
        else:
            print(f"ℹ️  {len(existing_beds)} beds already exist")
    
    await engine.dispose()
    print("\n🎉 Database initialization completed successfully!")


if __name__ == "__main__":
    asyncio.run(init_database())
