#!/usr/bin/env python3
"""
Script to add a test payment for today
"""

import asyncio
import sys
from datetime import datetime
from decimal import Decimal

# Add the app directory to the path
sys.path.insert(0, '.')

from app.core.database import AsyncSessionLocal
from app.crud.payment import payment_crud
from app.models.payment import PaymentType


async def add_test_payment():
    """Add a test payment for today"""
    async with AsyncSessionLocal() as db:
        try:
            # Create payment for the first visit
            payment1 = await payment_crud.create_payment(
                db=db,
                patient_id="P202602060001",
                visit_id="V20260206160514001",
                amount=Decimal("400.00"),
                payment_mode="CASH",
                payment_type=PaymentType.OPD_FEE,
                created_by="SYSTEM",
                notes="OPD consultation fee"
            )
            print(f"✓ Created payment 1: {payment1.payment_id} - ₹{payment1.amount}")
            
            # Create payment for the second visit
            payment2 = await payment_crud.create_payment(
                db=db,
                patient_id="P202602060002",
                visit_id="V20260206160532001",
                amount=Decimal("500.00"),
                payment_mode="UPI",
                payment_type=PaymentType.OPD_FEE,
                created_by="SYSTEM",
                notes="OPD consultation fee"
            )
            print(f"✓ Created payment 2: {payment2.payment_id} - ₹{payment2.amount}")
            
            # Create payment for the third visit
            payment3 = await payment_crud.create_payment(
                db=db,
                patient_id="P202602060003",
                visit_id="V20260206172339001",
                amount=Decimal("400.00"),
                payment_mode="CASH",
                payment_type=PaymentType.OPD_FEE,
                created_by="SYSTEM",
                notes="OPD consultation fee"
            )
            print(f"✓ Created payment 3: {payment3.payment_id} - ₹{payment3.amount}")
            
            print(f"\n✓ Total collection: ₹{payment1.amount + payment2.amount + payment3.amount}")
            
        except Exception as e:
            print(f"✗ Error creating payment: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(add_test_payment())
