"""
CRUD operations for Billing model
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError

from app.models.billing import BillingCharge, ChargeType
from app.models.visit import Visit
from app.models.ipd import IPD
from app.services.id_generator import generate_charge_id


class BillingCRUD:
    """CRUD operations for Billing model"""
    
    async def create_charge(
        self,
        db: AsyncSession,
        charge_type: ChargeType,
        charge_name: str,
        rate: Decimal,
        created_by: str,
        quantity: int = 1,
        visit_id: Optional[str] = None,
        ipd_id: Optional[str] = None
    ) -> BillingCharge:
        """Create a new billing charge with validation"""
        # Validate that either visit_id or ipd_id is provided
        if not visit_id and not ipd_id:
            raise ValueError("Either visit_id or ipd_id must be provided")
        
        # Validate visit or IPD exists
        if visit_id:
            visit_result = await db.execute(
                select(Visit).where(Visit.visit_id == visit_id)
            )
            visit = visit_result.scalar_one_or_none()
            if not visit:
                raise ValueError("Visit not found")
        
        if ipd_id:
            ipd_result = await db.execute(
                select(IPD).where(IPD.ipd_id == ipd_id)
            )
            ipd = ipd_result.scalar_one_or_none()
            if not ipd:
                raise ValueError("IPD record not found")
        
        # Validate input data
        if not charge_name or not charge_name.strip():
            raise ValueError("Charge name is required")
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if rate < 0:
            raise ValueError("Rate cannot be negative")
        
        try:
            # Generate unique charge ID
            charge_id = await generate_charge_id(db)
            
            # Ensure rate is quantized to 2 decimal places
            rate = Decimal(str(rate)).quantize(Decimal("0.01"))
            
            # Calculate total amount and quantize to 2 decimal places
            total_amount = (rate * quantity).quantize(Decimal("0.01"))
            
            charge = BillingCharge(
                charge_id=charge_id,
                visit_id=visit_id,
                ipd_id=ipd_id,
                charge_type=charge_type,
                charge_name=charge_name.strip(),
                quantity=quantity,
                rate=rate,
                total_amount=total_amount,
                created_by=created_by
            )
            
            db.add(charge)
            await db.commit()
            await db.refresh(charge)
            return charge
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error creating billing charge")
    
    async def add_investigation_charges(
        self,
        db: AsyncSession,
        visit_id: Optional[str],
        ipd_id: Optional[str],
        investigations: List[dict],
        created_by: str
    ) -> List[BillingCharge]:
        """Add multiple investigation charges"""
        charges = []
        
        for investigation in investigations:
            # Convert rate to Decimal and quantize to 2 decimal places
            rate = Decimal(str(investigation["rate"])).quantize(Decimal("0.01"))
            
            charge = await self.create_charge(
                db=db,
                charge_type=ChargeType.INVESTIGATION,
                charge_name=investigation["name"],
                rate=rate,
                quantity=investigation.get("quantity", 1),
                visit_id=visit_id,
                ipd_id=ipd_id,
                created_by=created_by
            )
            charges.append(charge)
        
        return charges
    
    async def add_procedure_charges(
        self,
        db: AsyncSession,
        visit_id: Optional[str],
        ipd_id: Optional[str],
        procedures: List[dict],
        created_by: str
    ) -> List[BillingCharge]:
        """Add multiple procedure charges"""
        charges = []
        
        for procedure in procedures:
            # Convert rate to Decimal and quantize to 2 decimal places
            rate = Decimal(str(procedure["rate"])).quantize(Decimal("0.01"))
            
            charge = await self.create_charge(
                db=db,
                charge_type=ChargeType.PROCEDURE,
                charge_name=procedure["name"],
                rate=rate,
                quantity=procedure.get("quantity", 1),
                visit_id=visit_id,
                ipd_id=ipd_id,
                created_by=created_by
            )
            charges.append(charge)
        
        return charges
    
    async def add_service_charges(
        self,
        db: AsyncSession,
        visit_id: Optional[str],
        ipd_id: Optional[str],
        services: List[dict],
        created_by: str
    ) -> List[BillingCharge]:
        """Add multiple service charges with time calculation"""
        charges = []
        
        for service in services:
            # Calculate hours if start_time and end_time are provided
            quantity = service.get("quantity", 1)
            
            if "start_time" in service and "end_time" in service:
                start_time = service["start_time"]
                end_time = service["end_time"]
                
                # Convert to datetime if they are strings
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time)
                
                # Calculate hours (rounded up)
                time_diff = end_time - start_time
                hours = time_diff.total_seconds() / 3600
                quantity = max(1, int(hours) if hours == int(hours) else int(hours) + 1)
            
            # Convert rate to Decimal and quantize to 2 decimal places
            rate = Decimal(str(service["rate"])).quantize(Decimal("0.01"))
            
            charge = await self.create_charge(
                db=db,
                charge_type=ChargeType.SERVICE,
                charge_name=service["name"],
                rate=rate,
                quantity=quantity,
                visit_id=visit_id,
                ipd_id=ipd_id,
                created_by=created_by
            )
            charges.append(charge)
        
        return charges
    
    async def add_manual_charges(
        self,
        db: AsyncSession,
        visit_id: Optional[str],
        ipd_id: Optional[str],
        manual_charges: List[dict],
        created_by: str
    ) -> List[BillingCharge]:
        """Add multiple manual charges (admin only) with audit logging"""
        from app.crud.audit import audit_crud
        from app.models.audit import ActionType
        
        charges = []
        
        for manual_charge in manual_charges:
            # Convert rate to Decimal and quantize to 2 decimal places
            rate = Decimal(str(manual_charge["rate"])).quantize(Decimal("0.01"))
            
            charge = await self.create_charge(
                db=db,
                charge_type=ChargeType.MANUAL,
                charge_name=manual_charge["name"],
                rate=rate,
                quantity=manual_charge.get("quantity", 1),
                visit_id=visit_id,
                ipd_id=ipd_id,
                created_by=created_by
            )
            charges.append(charge)
            
            # Log manual charge addition
            await audit_crud.log_manual_charge_add(
                db=db,
                user_id=created_by,
                charge_id=charge.charge_id,
                charge_data={
                    "charge_name": charge.charge_name,
                    "rate": float(charge.rate),
                    "quantity": charge.quantity,
                    "total_amount": float(charge.total_amount),
                    "visit_id": visit_id,
                    "ipd_id": ipd_id
                }
            )
        
        return charges
    
    async def get_charge_by_id(
        self, 
        db: AsyncSession, 
        charge_id: str
    ) -> Optional[BillingCharge]:
        """Get billing charge by ID"""
        result = await db.execute(
            select(BillingCharge).where(BillingCharge.charge_id == charge_id)
        )
        return result.scalar_one_or_none()
    
    async def get_charges_by_visit(
        self, 
        db: AsyncSession, 
        visit_id: str
    ) -> List[BillingCharge]:
        """Get all charges for a visit"""
        result = await db.execute(
            select(BillingCharge)
            .where(BillingCharge.visit_id == visit_id)
            .order_by(BillingCharge.charge_date)
        )
        return result.scalars().all()
    
    async def get_charges_by_ipd(
        self, 
        db: AsyncSession, 
        ipd_id: str
    ) -> List[BillingCharge]:
        """Get all charges for an IPD admission"""
        result = await db.execute(
            select(BillingCharge)
            .where(BillingCharge.ipd_id == ipd_id)
            .order_by(BillingCharge.charge_date)
        )
        return result.scalars().all()
    
    async def get_charges_by_type(
        self,
        db: AsyncSession,
        visit_id: Optional[str],
        ipd_id: Optional[str],
        charge_type: ChargeType
    ) -> List[BillingCharge]:
        """Get charges by type for a visit or IPD"""
        query = select(BillingCharge).where(
            BillingCharge.charge_type == charge_type
        )
        
        if visit_id:
            query = query.where(BillingCharge.visit_id == visit_id)
        elif ipd_id:
            query = query.where(BillingCharge.ipd_id == ipd_id)
        else:
            raise ValueError("Either visit_id or ipd_id must be provided")
        
        result = await db.execute(query.order_by(BillingCharge.charge_date))
        return result.scalars().all()
    
    async def calculate_total_charges(
        self,
        db: AsyncSession,
        visit_id: Optional[str] = None,
        ipd_id: Optional[str] = None
    ) -> Decimal:
        """Calculate total charges for a visit or IPD"""
        if visit_id:
            charges = await self.get_charges_by_visit(db, visit_id)
        elif ipd_id:
            charges = await self.get_charges_by_ipd(db, ipd_id)
        else:
            raise ValueError("Either visit_id or ipd_id must be provided")
        
        total = sum(charge.total_amount for charge in charges)
        return Decimal(str(total))
    
    async def delete_charge(
        self,
        db: AsyncSession,
        charge_id: str
    ) -> bool:
        """Delete a billing charge"""
        charge = await self.get_charge_by_id(db, charge_id)
        if not charge:
            return False
        
        await db.delete(charge)
        await db.commit()
        return True
    
    async def update_charge(
        self,
        db: AsyncSession,
        charge_id: str,
        charge_name: Optional[str] = None,
        rate: Optional[Decimal] = None,
        quantity: Optional[int] = None,
        updated_by: Optional[str] = None
    ) -> Optional[BillingCharge]:
        """Update a billing charge with audit logging for manual charges"""
        from app.crud.audit import audit_crud
        
        charge = await self.get_charge_by_id(db, charge_id)
        if not charge:
            return None
        
        # Validate updates
        if rate is not None and rate < 0:
            raise ValueError("Rate cannot be negative")
        
        if quantity is not None and quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        try:
            # Store old values for audit log (if manual charge)
            old_data = None
            if charge.charge_type == ChargeType.MANUAL and updated_by:
                old_data = {
                    "charge_name": charge.charge_name,
                    "rate": float(charge.rate),
                    "quantity": charge.quantity,
                    "total_amount": float(charge.total_amount)
                }
            
            # Update fields if provided
            if charge_name is not None:
                if not charge_name.strip():
                    raise ValueError("Charge name cannot be empty")
                charge.charge_name = charge_name.strip()
            
            if rate is not None:
                # Quantize rate to 2 decimal places
                charge.rate = Decimal(str(rate)).quantize(Decimal("0.01"))
            
            if quantity is not None:
                charge.quantity = quantity
            
            # Recalculate total amount and quantize to 2 decimal places
            charge.total_amount = (charge.rate * charge.quantity).quantize(Decimal("0.01"))
            
            await db.commit()
            await db.refresh(charge)
            
            # Log manual charge edit
            if charge.charge_type == ChargeType.MANUAL and updated_by and old_data:
                new_data = {
                    "charge_name": charge.charge_name,
                    "rate": float(charge.rate),
                    "quantity": charge.quantity,
                    "total_amount": float(charge.total_amount)
                }
                await audit_crud.log_manual_charge_edit(
                    db=db,
                    user_id=updated_by,
                    charge_id=charge_id,
                    old_data=old_data,
                    new_data=new_data
                )
            
            return charge
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("Error updating billing charge")


# Global instance
billing_crud = BillingCRUD()
