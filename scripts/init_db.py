#!/usr/bin/env python3
"""
Initialize database with sample data
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.models import Base
from app.models.user import User, UserRole
from app.models.doctor import Doctor, DoctorStatus
from app.models.bed import Bed, WardType, BedStatus
from app.core.security import get_password_hash


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables created")


async def create_sample_users():
    """Create sample users."""
    async with AsyncSessionLocal() as session:
        # Admin user
        admin_user = User(
            user_id="U001",
            username="admin",
            email="admin@hospital.com",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        # Reception user
        reception_user = User(
            user_id="U002",
            username="reception",
            email="reception@hospital.com",
            hashed_password=get_password_hash("reception123"),
            full_name="Reception Staff",
            role=UserRole.RECEPTION,
            is_active=True
        )
        
        session.add_all([admin_user, reception_user])
        await session.commit()
    
    print("✓ Sample users created")
    print("  - Admin: username=admin, password=admin123")
    print("  - Reception: username=reception, password=reception123")


async def create_sample_doctors():
    """Create sample doctors."""
    async with AsyncSessionLocal() as session:
        doctors = [
            Doctor(
                doctor_id="D001",
                name="Dr. Rajesh Kumar",
                department="Cardiology",
                new_patient_fee=500.00,
                followup_fee=300.00,
                status=DoctorStatus.ACTIVE
            ),
            Doctor(
                doctor_id="D002",
                name="Dr. Priya Sharma",
                department="Pediatrics",
                new_patient_fee=400.00,
                followup_fee=250.00,
                status=DoctorStatus.ACTIVE
            ),
            Doctor(
                doctor_id="D003",
                name="Dr. Amit Singh",
                department="Orthopedics",
                new_patient_fee=600.00,
                followup_fee=350.00,
                status=DoctorStatus.ACTIVE
            ),
            Doctor(
                doctor_id="D004",
                name="Dr. Sunita Patel",
                department="Gynecology",
                new_patient_fee=450.00,
                followup_fee=275.00,
                status=DoctorStatus.ACTIVE
            ),
            Doctor(
                doctor_id="D005",
                name="Dr. Vikram Gupta",
                department="General Medicine",
                new_patient_fee=350.00,
                followup_fee=200.00,
                status=DoctorStatus.ACTIVE
            )
        ]
        
        session.add_all(doctors)
        await session.commit()
    
    print("✓ Sample doctors created")


async def create_sample_beds():
    """Create sample beds."""
    async with AsyncSessionLocal() as session:
        beds = []
        
        # General ward beds (1-20)
        for i in range(1, 21):
            beds.append(Bed(
                bed_id=f"B{i:03d}",
                bed_number=f"G{i:02d}",
                ward_type=WardType.GENERAL,
                per_day_charge=500.00,
                status=BedStatus.AVAILABLE
            ))
        
        # Semi-private beds (21-30)
        for i in range(21, 31):
            beds.append(Bed(
                bed_id=f"B{i:03d}",
                bed_number=f"SP{i-20:02d}",
                ward_type=WardType.SEMI_PRIVATE,
                per_day_charge=1000.00,
                status=BedStatus.AVAILABLE
            ))
        
        # Private beds (31-40)
        for i in range(31, 41):
            beds.append(Bed(
                bed_id=f"B{i:03d}",
                bed_number=f"P{i-30:02d}",
                ward_type=WardType.PRIVATE,
                per_day_charge=2000.00,
                status=BedStatus.AVAILABLE
            ))
        
        session.add_all(beds)
        await session.commit()
    
    print("✓ Sample beds created")
    print("  - General ward: 20 beds (₹500/day)")
    print("  - Semi-private: 10 beds (₹1000/day)")
    print("  - Private: 10 beds (₹2000/day)")


async def main():
    """Main initialization function."""
    print("Initializing Hospital Management System Database...")
    print("=" * 50)
    
    try:
        await create_tables()
        await create_sample_users()
        await create_sample_doctors()
        await create_sample_beds()
        
        print("=" * 50)
        print("✓ Database initialization completed successfully!")
        print("\nYou can now start the application with:")
        print("  python run.py")
        print("\nAccess the application at: http://localhost:8000")
        
    except Exception as e:
        print(f"✗ Error during initialization: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())