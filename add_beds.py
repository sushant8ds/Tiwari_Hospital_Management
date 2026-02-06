"""
Script to add beds to the hospital database
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud.ipd import bed_crud
from app.models.bed import WardType


async def add_beds():
    """Add sample beds to the database"""
    
    async for db in get_db():
        try:
            print("Adding beds to the database...")
            
            # General Ward Beds (10 beds)
            general_beds = [
                ("G101", WardType.GENERAL, 500),
                ("G102", WardType.GENERAL, 500),
                ("G103", WardType.GENERAL, 500),
                ("G104", WardType.GENERAL, 500),
                ("G105", WardType.GENERAL, 500),
                ("G106", WardType.GENERAL, 500),
                ("G107", WardType.GENERAL, 500),
                ("G108", WardType.GENERAL, 500),
                ("G109", WardType.GENERAL, 500),
                ("G110", WardType.GENERAL, 500),
            ]
            
            # Semi-Private Ward Beds (5 beds)
            semi_private_beds = [
                ("SP201", WardType.SEMI_PRIVATE, 1000),
                ("SP202", WardType.SEMI_PRIVATE, 1000),
                ("SP203", WardType.SEMI_PRIVATE, 1000),
                ("SP204", WardType.SEMI_PRIVATE, 1000),
                ("SP205", WardType.SEMI_PRIVATE, 1000),
            ]
            
            # Private Ward Beds (5 beds)
            private_beds = [
                ("P301", WardType.PRIVATE, 2000),
                ("P302", WardType.PRIVATE, 2000),
                ("P303", WardType.PRIVATE, 2000),
                ("P304", WardType.PRIVATE, 2000),
                ("P305", WardType.PRIVATE, 2000),
            ]
            
            all_beds = general_beds + semi_private_beds + private_beds
            
            for bed_number, ward_type, charge in all_beds:
                try:
                    bed = await bed_crud.create_bed(
                        db=db,
                        bed_number=bed_number,
                        ward_type=ward_type,
                        per_day_charge=charge
                    )
                    print(f"✓ Added bed: {bed_number} ({ward_type.value}) - ₹{charge}/day")
                except ValueError as e:
                    if "already exists" in str(e):
                        print(f"⊘ Bed {bed_number} already exists, skipping...")
                    else:
                        print(f"✗ Error adding bed {bed_number}: {e}")
            
            print(f"\n✓ Successfully added {len(all_beds)} beds!")
            print("\nBed Summary:")
            print(f"  - General Ward: 10 beds @ ₹500/day")
            print(f"  - Semi-Private Ward: 5 beds @ ₹1000/day")
            print(f"  - Private Ward: 5 beds @ ₹2000/day")
            print(f"  - Total: 20 beds")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            break


if __name__ == "__main__":
    asyncio.run(add_beds())
