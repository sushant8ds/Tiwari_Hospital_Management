"""
CRUD operations for discharge bill generation and processing
"""

from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.ipd import IPD, IPDStatus
from app.models.patient import Patient
from app.models.visit import Visit
from app.models.billing import BillingCharge
from app.models.payment import Payment, PaymentType
from app.crud.payment import payment_crud
from app.crud.billing import billing_crud


class DischargeCRUD:
    """CRUD operations for discharge processing"""
    
    async def generate_discharge_bill(
        self,
        db: AsyncSession,
        ipd_id: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive discharge bill with all charges and payments
        """
        # Get IPD record
        ipd_result = await db.execute(
            select(IPD).where(IPD.ipd_id == ipd_id)
        )
        ipd = ipd_result.scalar_one_or_none()
        if not ipd:
            raise ValueError("IPD record not found")
        
        # Get patient
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == ipd.patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        
        # Get visit if exists
        visit = None
        if ipd.visit_id:
            visit_result = await db.execute(
                select(Visit).where(Visit.visit_id == ipd.visit_id)
            )
            visit = visit_result.scalar_one_or_none()
        
        # Get all billing charges (includes OT charges)
        charges_result = await db.execute(
            select(BillingCharge).where(BillingCharge.ipd_id == ipd_id)
        )
        charges = charges_result.scalars().all()
        
        # Get all payments
        payments_result = await db.execute(
            select(Payment).where(Payment.ipd_id == ipd_id)
        )
        payments = payments_result.scalars().all()
        
        # Calculate charges by type
        charges_by_type = {}
        total_charges = Decimal("0.00")
        
        # Add IPD file charge
        charges_by_type["FILE_CHARGE"] = [{
            "name": "IPD File Charge",
            "quantity": 1,
            "rate": float(ipd.file_charge),
            "total": float(ipd.file_charge)
        }]
        total_charges += ipd.file_charge
        
        # Add OPD fee if visit exists
        if visit:
            charges_by_type["OPD_FEE"] = [{
                "name": "OPD Consultation Fee",
                "quantity": 1,
                "rate": float(visit.opd_fee),
                "total": float(visit.opd_fee)
            }]
            total_charges += visit.opd_fee
        
        # Group billing charges by type
        for charge in charges:
            charge_type = charge.charge_type.value
            if charge_type not in charges_by_type:
                charges_by_type[charge_type] = []
            
            charges_by_type[charge_type].append({
                "name": charge.charge_name,
                "quantity": charge.quantity,
                "rate": float(charge.rate),
                "total": float(charge.total_amount)
            })
            total_charges += charge.total_amount
        
        # OT charges are already included in billing charges
        # No need to add them separately as they're stored in billing_charges table with ChargeType.OT
        
        # Calculate payments
        total_paid = Decimal("0.00")
        advance_paid = Decimal("0.00")
        payment_details = []
        
        for payment in payments:
            total_paid += payment.amount
            if payment.payment_type == PaymentType.IPD_ADVANCE:
                advance_paid += payment.amount
            
            payment_details.append({
                "payment_id": payment.payment_id,
                "date": payment.payment_date.isoformat(),
                "amount": float(payment.amount),
                "mode": payment.payment_mode,
                "type": payment.payment_type.value,
                "reference": payment.transaction_reference
            })
        
        # Calculate balance
        balance_due = total_charges - total_paid
        
        # Create discharge bill
        discharge_bill = {
            "ipd_id": ipd_id,
            "patient": {
                "id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender.value,
                "mobile": patient.mobile_number,
                "address": patient.address
            },
            "admission": {
                "admission_date": ipd.admission_date.isoformat(),
                "discharge_date": ipd.discharge_date.isoformat() if ipd.discharge_date else None,
                "days": self._calculate_days(ipd.admission_date, ipd.discharge_date or datetime.now())
            },
            "charges_by_type": charges_by_type,
            "payments": payment_details,
            "summary": {
                "total_charges": float(total_charges),
                "total_paid": float(total_paid),
                "advance_paid": float(advance_paid),
                "balance_due": float(balance_due)
            },
            "generated_date": datetime.now().isoformat()
        }
        
        return discharge_bill
    
    async def process_discharge(
        self,
        db: AsyncSession,
        ipd_id: str,
        discharge_date: datetime = None
    ) -> IPD:
        """
        Process patient discharge
        """
        # Get IPD record
        ipd_result = await db.execute(
            select(IPD).where(IPD.ipd_id == ipd_id)
        )
        ipd = ipd_result.scalar_one_or_none()
        if not ipd:
            raise ValueError("IPD record not found")
        
        if ipd.status == IPDStatus.DISCHARGED:
            raise ValueError("Patient already discharged")
        
        # Set discharge date
        if discharge_date is None:
            discharge_date = datetime.now()
        
        ipd.discharge_date = discharge_date
        ipd.status = IPDStatus.DISCHARGED
        
        await db.commit()
        await db.refresh(ipd)
        
        return ipd
    
    async def calculate_pending_amount(
        self,
        db: AsyncSession,
        ipd_id: str
    ) -> Decimal:
        """
        Calculate pending amount for IPD
        """
        bill = await self.generate_discharge_bill(db, ipd_id)
        return Decimal(str(bill["summary"]["balance_due"]))
    
    def _calculate_days(self, admission_date: datetime, discharge_date: datetime) -> int:
        """Calculate number of days between admission and discharge"""
        delta = discharge_date - admission_date
        return max(1, delta.days + 1)  # Minimum 1 day


# Global instance
discharge_crud = DischargeCRUD()
