"""
Quick database diagnostic script
Run this in Render Shell to check database status
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, text
from app.core.config import settings
from app.models.doctor import Doctor
from app.models.bed import Bed
from app.models.patient import Patient
from app.models.visit import Visit


async def check_database():
    """Check database status and contents"""
    
    print("\n" + "="*60)
    print("DATABASE DIAGNOSTIC CHECK")
    print("="*60)
    
    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    try:
        # Check if database file exists and is accessible
        print("\n1. DATABASE CONNECTION")
        print(f"   Database URL: {settings.DATABASE_URL}")
        
        async with async_session() as session:
            # Test connection
            result = await session.execute(text("SELECT 1"))
            print("   ✅ Database connection successful")
        
        # Check tables exist
        print("\n2. TABLES CHECK")
        async with engine.begin() as conn:
            result = await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            )
            tables = result.fetchall()
            print(f"   Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table[0]}")
        
        # Check doctors
        print("\n3. DOCTORS TABLE")
        async with async_session() as session:
            result = await session.execute(select(func.count(Doctor.doctor_id)))
            count = result.scalar()
            print(f"   Total doctors: {count}")
            
            if count > 0:
                result = await session.execute(select(Doctor).limit(5))
                doctors = result.scalars().all()
                print("   Sample doctors:")
                for doc in doctors:
                    print(f"   - {doc.doctor_id}: {doc.name} ({doc.department})")
                    print(f"     Fees: ₹{doc.new_patient_fee} / ₹{doc.followup_fee}")
                    print(f"     Status: {doc.status.value}")
            else:
                print("   ⚠️  NO DOCTORS FOUND - Database is empty!")
                print("   → You need to run: python init_render_db.py")
        
        # Check beds
        print("\n4. BEDS TABLE")
        async with async_session() as session:
            result = await session.execute(select(func.count(Bed.bed_id)))
            count = result.scalar()
            print(f"   Total beds: {count}")
            
            if count > 0:
                result = await session.execute(select(Bed).limit(5))
                beds = result.scalars().all()
                print("   Sample beds:")
                for bed in beds:
                    print(f"   - {bed.bed_id}: {bed.bed_number} ({bed.ward_type.value})")
                    print(f"     Charge: ₹{bed.per_day_charge}/day, Status: {bed.status.value}")
            else:
                print("   ⚠️  NO BEDS FOUND - Database is empty!")
                print("   → You need to run: python init_render_db.py")
        
        # Check patients
        print("\n5. PATIENTS TABLE")
        async with async_session() as session:
            result = await session.execute(select(func.count(Patient.patient_id)))
            count = result.scalar()
            print(f"   Total patients: {count}")
        
        # Check visits
        print("\n6. VISITS TABLE")
        async with async_session() as session:
            result = await session.execute(select(func.count(Visit.visit_id)))
            count = result.scalar()
            print(f"   Total visits: {count}")
        
        print("\n" + "="*60)
        print("DIAGNOSIS COMPLETE")
        print("="*60)
        
        # Provide recommendations
        async with async_session() as session:
            result = await session.execute(select(func.count(Doctor.doctor_id)))
            doctor_count = result.scalar()
            result = await session.execute(select(func.count(Bed.bed_id)))
            bed_count = result.scalar()
        
        if doctor_count == 0 or bed_count == 0:
            print("\n⚠️  ACTION REQUIRED:")
            print("   Your database is empty. Run this command:")
            print("   → python init_render_db.py")
        else:
            print("\n✅ DATABASE IS POPULATED")
            print(f"   - {doctor_count} doctors")
            print(f"   - {bed_count} beds")
            print("\n   If data still not showing in browser:")
            print("   1. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)")
            print("   2. Check browser console for errors (F12)")
            print("   3. Check Render logs for API errors")
        
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nPossible issues:")
        print("1. Database file doesn't exist")
        print("2. Tables not created")
        print("3. Permission issues")
        print("\nTry running: python init_render_db.py")
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_database())
