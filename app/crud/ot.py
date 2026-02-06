"""
CRUD operations for Operation Theater (OT) management
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from app.models.ot import OTProcedure
from app.models.ipd import IPD
from app.models.billing import BillingCharge, ChargeType
from app.services.id_generator import generate_id


class OTCrud:
    """CRUD operations for OT procedures"""
    
    async def create_ot_procedure(
        self,
        db: AsyncSession,
        ipd_id: str,
        operation_name: str,
        operation_date: datetime,
        duration_minutes: int,
        surgeon_name: str,
        created_by: str,
        anesthesia_type: Optional[str] = None,
        notes: Optional[str] = None
    ) -> OTProcedure:
        """Create a new OT procedure record"""
        # Validate IPD exists
        ipd_result = await db.execute(
            select(IPD).where(IPD.ipd_id == ipd_id)
        )
        ipd = ipd_result.scalar_one_or_none()
        if not ipd:
            raise ValueError("IPD record not found")
        
        # Validate input
        if not operation_name or not operation_name.strip():
            raise ValueError("Operation name is required")
        
        if not surgeon_name or not surgeon_name.strip():
            raise ValueError("Surgeon name is required")
        
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive")
        
        try:
            # Generate OT ID
            ot_id = await generate_id("OT")
            
            # Create OT procedure
            ot_procedure = OTProcedure(
                ot_id=ot_id,
                ipd_id=ipd_id,
                operation_name=operation_name.strip(),
                operation_date=operation_date,
                duration_minutes=duration_minutes,
                surgeon_name=surgeon_name.strip(),
                anesthesia_type=anesthesia_type.strip() if anesthesia_type else None,
                notes=notes.strip() if notes else None,
                created_by=created_by
            )
            
            db.add(ot_procedure)
            await db.commit()
            await db.refresh(ot_procedure)
            
            return ot_procedure
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def add_ot_charges(
        self,
        db: AsyncSession,
        ipd_id: str,
        ot_id: str,
        surgeon_charge: Decimal,
        anesthesia_charge: Decimal,
        facility_charge: Decimal,
        created_by: str,
        assistant_charge: Optional[Decimal] = None
    ) -> List[BillingCharge]:
        """Add OT charges to billing"""
        # Validate IPD exists
        ipd_result = await db.execute(
            select(IPD).where(IPD.ipd_id == ipd_id)
        )
        ipd = ipd_result.scalar_one_or_none()
        if not ipd:
            raise ValueError("IPD record not found")
        
        # Validate OT procedure exists
        ot_result = await db.execute(
            select(OTProcedure).where(OTProcedure.ot_id == ot_id)
        )
        ot_procedure = ot_result.scalar_one_or_none()
        if not ot_procedure:
            raise ValueError("OT procedure not found")
        
        # Validate charges
        if surgeon_charge < 0:
            raise ValueError("Surgeon charge cannot be negative")
        if anesthesia_charge < 0:
            raise ValueError("Anesthesia charge cannot be negative")
        if facility_charge < 0:
            raise ValueError("Facility charge cannot be negative")
        if assistant_charge and assistant_charge < 0:
            raise ValueError("Assistant charge cannot be negative")
        
        try:
            charges = []
            
            # Quantize all charges to 2 decimal places
            surgeon_charge = Decimal(str(surgeon_charge)).quantize(Decimal("0.01"))
            anesthesia_charge = Decimal(str(anesthesia_charge)).quantize(Decimal("0.01"))
            facility_charge = Decimal(str(facility_charge)).quantize(Decimal("0.01"))
            
            # Add surgeon charge
            if surgeon_charge > 0:
                surgeon_charge_id = await generate_id("CHG")
                surgeon_billing = BillingCharge(
                    charge_id=surgeon_charge_id,
                    ipd_id=ipd_id,
                    charge_type=ChargeType.OT,
                    charge_name=f"OT Surgeon Charge - {ot_procedure.operation_name}",
                    quantity=1,
                    rate=surgeon_charge,
                    total_amount=surgeon_charge,
                    created_by=created_by
                )
                db.add(surgeon_billing)
                charges.append(surgeon_billing)
            
            # Add anesthesia charge
            if anesthesia_charge > 0:
                anesthesia_charge_id = await generate_id("CHG")
                anesthesia_billing = BillingCharge(
                    charge_id=anesthesia_charge_id,
                    ipd_id=ipd_id,
                    charge_type=ChargeType.OT,
                    charge_name=f"OT Anesthesia Charge - {ot_procedure.operation_name}",
                    quantity=1,
                    rate=anesthesia_charge,
                    total_amount=anesthesia_charge,
                    created_by=created_by
                )
                db.add(anesthesia_billing)
                charges.append(anesthesia_billing)
            
            # Add facility charge
            if facility_charge > 0:
                facility_charge_id = await generate_id("CHG")
                facility_billing = BillingCharge(
                    charge_id=facility_charge_id,
                    ipd_id=ipd_id,
                    charge_type=ChargeType.OT,
                    charge_name=f"OT Facility Charge - {ot_procedure.operation_name}",
                    quantity=1,
                    rate=facility_charge,
                    total_amount=facility_charge,
                    created_by=created_by
                )
                db.add(facility_billing)
                charges.append(facility_billing)
            
            # Add assistant charge if provided
            if assistant_charge and assistant_charge > 0:
                assistant_charge = Decimal(str(assistant_charge)).quantize(Decimal("0.01"))
                assistant_charge_id = await generate_id("CHG")
                assistant_billing = BillingCharge(
                    charge_id=assistant_charge_id,
                    ipd_id=ipd_id,
                    charge_type=ChargeType.OT,
                    charge_name=f"OT Assistant Charge - {ot_procedure.operation_name}",
                    quantity=1,
                    rate=assistant_charge,
                    total_amount=assistant_charge,
                    created_by=created_by
                )
                db.add(assistant_billing)
                charges.append(assistant_billing)
            
            await db.commit()
            
            # Refresh all charges
            for charge in charges:
                await db.refresh(charge)
            
            return charges
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def get_ot_procedure_by_id(
        self,
        db: AsyncSession,
        ot_id: str
    ) -> Optional[OTProcedure]:
        """Get OT procedure by ID"""
        result = await db.execute(
            select(OTProcedure).where(OTProcedure.ot_id == ot_id)
        )
        return result.scalar_one_or_none()
    
    async def get_ot_procedures_by_ipd(
        self,
        db: AsyncSession,
        ipd_id: str
    ) -> List[OTProcedure]:
        """Get all OT procedures for an IPD admission"""
        result = await db.execute(
            select(OTProcedure)
            .where(OTProcedure.ipd_id == ipd_id)
            .order_by(OTProcedure.operation_date.desc())
        )
        return result.scalars().all()
    
    async def get_ot_charges_by_ipd(
        self,
        db: AsyncSession,
        ipd_id: str
    ) -> List[BillingCharge]:
        """Get all OT charges for an IPD admission"""
        result = await db.execute(
            select(BillingCharge)
            .where(
                BillingCharge.ipd_id == ipd_id,
                BillingCharge.charge_type == ChargeType.OT
            )
            .order_by(BillingCharge.charge_date.desc())
        )
        return result.scalars().all()


# Create singleton instance
ot_crud = OTCrud()
