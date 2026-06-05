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
                new_patient_fee=300.00,
                followup_fee=150.00,
                status=DoctorStatus.ACTIVE
            ),
            Doctor(
                doctor_id="D002",
                name="Dr. Priya Sharma",
                department="Pediatrics",
                new_patient_fee=300.00,
                followup_fee=150.00,
                status=DoctorStatus.ACTIVE
            ),
            Doctor(
                doctor_id="D003",
                name="Dr. Amit Singh",
                department="Orthopedics",
                new_patient_fee=300.00,
                followup_fee=150.00,
                status=DoctorStatus.ACTIVE
            ),
            Doctor(
                doctor_id="D004",
                name="Dr. Sunita Patel",
                department="Gynecology",
                new_patient_fee=300.00,
                followup_fee=150.00,
                status=DoctorStatus.ACTIVE
            ),
            Doctor(
                doctor_id="D005",
                name="Dr. Vikram Gupta",
                department="General Medicine",
                new_patient_fee=300.00,
                followup_fee=150.00,
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
        
        # General ward beds (1-20) - General: 500
        for i in range(1, 21):
            beds.append(Bed(
                bed_id=f"B{i:03d}",
                bed_number=f"GEN-{i:02d}",
                ward_type=WardType.GENERAL,
                per_day_charge=500.00,
                status=BedStatus.AVAILABLE
            ))
        
        # Double sharing non-AC (21-25) - charge 700
        for i in range(21, 26):
            beds.append(Bed(
                bed_id=f"B{i:03d}",
                bed_number=f"DNAC-{i-20:02d}",
                ward_type=WardType.SEMI_PRIVATE,
                per_day_charge=700.00,
                status=BedStatus.AVAILABLE
            ))
            
        # Double sharing AC (26-30) - charge 1100
        for i in range(26, 31):
            beds.append(Bed(
                bed_id=f"B{i:03d}",
                bed_number=f"DAC-{i-25:02d}",
                ward_type=WardType.SEMI_PRIVATE,
                per_day_charge=1100.00,
                status=BedStatus.AVAILABLE
            ))
        
        # Single private non-AC (31-35) - charge 1000
        for i in range(31, 36):
            beds.append(Bed(
                bed_id=f"B{i:03d}",
                bed_number=f"SNAC-{i-30:02d}",
                ward_type=WardType.PRIVATE,
                per_day_charge=1000.00,
                status=BedStatus.AVAILABLE
            ))
            
        # Single private AC (36-40) - charge 1500
        for i in range(36, 41):
            beds.append(Bed(
                bed_id=f"B{i:03d}",
                bed_number=f"SAC-{i-35:02d}",
                ward_type=WardType.PRIVATE,
                per_day_charge=1500.00,
                status=BedStatus.AVAILABLE
            ))
        
        session.add_all(beds)
        await session.commit()
    
    print("✓ Sample beds created")
    print("  - General ward: 20 beds (₹500/day)")
    print("  - Double sharing Non-AC: 5 beds (₹700/day)")
    print("  - Double sharing AC: 5 beds (₹1100/day)")
    print("  - Single Private Non-AC: 5 beds (₹1000/day)")
    print("  - Single Private AC: 5 beds (₹1500/day)")


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