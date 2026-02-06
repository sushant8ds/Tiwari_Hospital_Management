"""
Script to add doctors to the system
"""
import asyncio
from decimal import Decimal

# Import all models first to avoid relationship issues
from app.models import user, patient, doctor, visit, ipd, bed, billing, employee, audit, ot, payment, slip

from app.core.database import AsyncSessionLocal
from app.crud.doctor import doctor_crud
from app.crud.user import user_crud
from app.models.user import UserRole


async def main():
    async with AsyncSessionLocal() as db:
        # Create admin user if not exists
        admin = await user_crud.get_user_by_username(db, 'admin')
        if not admin:
            admin = await user_crud.create_user(
                db=db,
                username='admin',
                email='admin@hospital.com',
                password='admin123',
                full_name='System Administrator',
                role=UserRole.ADMIN
            )
            print(f'✅ Created admin user: {admin.username} (password: admin123)')
        else:
            print(f'✅ Admin user already exists: {admin.username}')
        
        # Add Dr. Nitish Tiwari (Orthopedic)
        doctor1 = await doctor_crud.create_doctor(
            db=db,
            name="Dr. Nitish Tiwari",
            department="Orthopedic",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        print(f'✅ Added doctor: {doctor1.name} - {doctor1.department} (ID: {doctor1.doctor_id})')
        
        # Add Dr. Muskan Tiwari (Dentist)
        doctor2 = await doctor_crud.create_doctor(
            db=db,
            name="Dr. Muskan Tiwari",
            department="Dentist",
            new_patient_fee=Decimal("400.00"),
            followup_fee=Decimal("250.00")
        )
        print(f'✅ Added doctor: {doctor2.name} - {doctor2.department} (ID: {doctor2.doctor_id})')
        
        # List all doctors
        print("\n📋 All Doctors in System:")
        doctors = await doctor_crud.get_all_doctors(db)
        for doc in doctors:
            print(f"   - {doc.name} ({doc.department}) - New: ₹{doc.new_patient_fee}, Follow-up: ₹{doc.followup_fee}")


if __name__ == "__main__":
    asyncio.run(main())
