"""
CRUD operations for Slip model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.slip import Slip, SlipType, PrinterFormat
from app.models.patient import Patient
from app.models.visit import Visit
from app.models.ipd import IPD
from app.models.doctor import Doctor
from app.models.billing import BillingCharge
from app.models.payment import Payment
from app.services.id_generator import generate_id
from app.services.barcode_service import barcode_service


class SlipCRUD:
    """CRUD operations for Slip model"""
    
    async def generate_opd_slip(
        self,
        db: AsyncSession,
        visit_id: str,
        printer_format: PrinterFormat,
        generated_by: str
    ) -> Slip:
        """Generate OPD slip"""
        # Get visit with patient and doctor details
        visit_result = await db.execute(
            select(Visit).where(Visit.visit_id == visit_id)
        )
        visit = visit_result.scalar_one_or_none()
        if not visit:
            raise ValueError("Visit not found")
        
        # Get patient
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == visit.patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        
        # Get doctor
        doctor_result = await db.execute(
            select(Doctor).where(Doctor.doctor_id == visit.doctor_id)
        )
        doctor = doctor_result.scalar_one_or_none()
        
        # Generate barcode data
        barcode_data = barcode_service.generate_barcode_data(
            patient.patient_id,
            visit.visit_id
        )
        barcode_image = barcode_service.generate_barcode_image(barcode_data)
        
        # Create slip content
        slip_content = {
            "hospital_name": "Hospital Management System",
            "slip_type": "OPD Registration",
            "patient": {
                "id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender.value,
                "mobile": patient.mobile_number,
                "address": patient.address
            },
            "visit": {
                "id": visit.visit_id,
                "type": visit.visit_type.value,
                "date": visit.visit_date.isoformat(),
                "time": visit.visit_time.isoformat(),
                "serial_number": visit.serial_number
            },
            "doctor": {
                "name": doctor.name if doctor else "N/A",
                "department": visit.department
            },
            "charges": {
                "opd_fee": float(visit.opd_fee),
                "payment_mode": visit.payment_mode.value
            },
            "barcode_data": barcode_data,
            "generated_date": datetime.now().isoformat()
        }
        
        # Generate slip ID
        slip_id = await generate_id("SLIP")
        
        # Create slip
        slip = Slip(
            slip_id=slip_id,
            patient_id=patient.patient_id,
            visit_id=visit.visit_id,
            slip_type=SlipType.OPD,
            barcode_data=barcode_data,
            barcode_image=barcode_image,
            slip_content=json.dumps(slip_content),
            printer_format=printer_format,
            generated_by=generated_by
        )
        
        db.add(slip)
        await db.commit()
        await db.refresh(slip)
        
        return slip

    async def generate_investigation_slip(
        self,
        db: AsyncSession,
        visit_id: Optional[str],
        ipd_id: Optional[str],
        printer_format: PrinterFormat,
        generated_by: str
    ) -> Slip:
        """Generate investigation slip"""
        if not visit_id and not ipd_id:
            raise ValueError("Either visit_id or ipd_id must be provided")
        
        # Get patient
        if visit_id:
            visit_result = await db.execute(
                select(Visit).where(Visit.visit_id == visit_id)
            )
            visit = visit_result.scalar_one_or_none()
            if not visit:
                raise ValueError("Visit not found")
            patient_id = visit.patient_id
        else:
            ipd_result = await db.execute(
                select(IPD).where(IPD.ipd_id == ipd_id)
            )
            ipd = ipd_result.scalar_one_or_none()
            if not ipd:
                raise ValueError("IPD record not found")
            patient_id = ipd.patient_id
            visit = None
        
        # Get patient
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        
        # Get investigation charges
        charges_result = await db.execute(
            select(BillingCharge).where(
                BillingCharge.visit_id == visit_id if visit_id else BillingCharge.ipd_id == ipd_id,
                BillingCharge.charge_type == "INVESTIGATION"
            )
        )
        charges = charges_result.scalars().all()
        
        # Generate barcode data
        record_id = visit_id if visit_id else ipd_id
        barcode_data = barcode_service.generate_barcode_data(patient.patient_id, record_id)
        barcode_image = barcode_service.generate_barcode_image(barcode_data)
        
        # Create slip content
        slip_content = {
            "hospital_name": "Hospital Management System",
            "slip_type": "Investigation",
            "patient": {
                "id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender.value,
                "mobile": patient.mobile_number
            },
            "investigations": [
                {
                    "name": charge.charge_name,
                    "quantity": charge.quantity,
                    "rate": float(charge.rate),
                    "total": float(charge.total_amount)
                }
                for charge in charges
            ],
            "total_amount": sum(float(charge.total_amount) for charge in charges),
            "barcode_data": barcode_data,
            "generated_date": datetime.now().isoformat()
        }
        
        # Generate slip ID
        slip_id = await generate_id("SLIP")
        
        # Create slip
        slip = Slip(
            slip_id=slip_id,
            patient_id=patient.patient_id,
            visit_id=visit_id,
            ipd_id=ipd_id,
            slip_type=SlipType.INVESTIGATION,
            barcode_data=barcode_data,
            barcode_image=barcode_image,
            slip_content=json.dumps(slip_content),
            printer_format=printer_format,
            generated_by=generated_by
        )
        
        db.add(slip)
        await db.commit()
        await db.refresh(slip)
        
        return slip
    
    async def generate_procedure_slip(
        self,
        db: AsyncSession,
        visit_id: Optional[str],
        ipd_id: Optional[str],
        printer_format: PrinterFormat,
        generated_by: str
    ) -> Slip:
        """Generate procedure slip"""
        if not visit_id and not ipd_id:
            raise ValueError("Either visit_id or ipd_id must be provided")
        
        # Get patient
        if visit_id:
            visit_result = await db.execute(
                select(Visit).where(Visit.visit_id == visit_id)
            )
            visit = visit_result.scalar_one_or_none()
            if not visit:
                raise ValueError("Visit not found")
            patient_id = visit.patient_id
        else:
            ipd_result = await db.execute(
                select(IPD).where(IPD.ipd_id == ipd_id)
            )
            ipd = ipd_result.scalar_one_or_none()
            if not ipd:
                raise ValueError("IPD record not found")
            patient_id = ipd.patient_id
        
        # Get patient
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        
        # Get procedure charges
        charges_result = await db.execute(
            select(BillingCharge).where(
                BillingCharge.visit_id == visit_id if visit_id else BillingCharge.ipd_id == ipd_id,
                BillingCharge.charge_type == "PROCEDURE"
            )
        )
        charges = charges_result.scalars().all()
        
        # Generate barcode data
        record_id = visit_id if visit_id else ipd_id
        barcode_data = barcode_service.generate_barcode_data(patient.patient_id, record_id)
        barcode_image = barcode_service.generate_barcode_image(barcode_data)
        
        # Create slip content
        slip_content = {
            "hospital_name": "Hospital Management System",
            "slip_type": "Procedure",
            "patient": {
                "id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender.value,
                "mobile": patient.mobile_number
            },
            "procedures": [
                {
                    "name": charge.charge_name,
                    "quantity": charge.quantity,
                    "rate": float(charge.rate),
                    "total": float(charge.total_amount)
                }
                for charge in charges
            ],
            "total_amount": sum(float(charge.total_amount) for charge in charges),
            "barcode_data": barcode_data,
            "generated_date": datetime.now().isoformat()
        }
        
        # Generate slip ID
        slip_id = await generate_id("SLIP")
        
        # Create slip
        slip = Slip(
            slip_id=slip_id,
            patient_id=patient.patient_id,
            visit_id=visit_id,
            ipd_id=ipd_id,
            slip_type=SlipType.PROCEDURE,
            barcode_data=barcode_data,
            barcode_image=barcode_image,
            slip_content=json.dumps(slip_content),
            printer_format=printer_format,
            generated_by=generated_by
        )
        
        db.add(slip)
        await db.commit()
        await db.refresh(slip)
        
        return slip
    
    async def generate_service_slip(
        self,
        db: AsyncSession,
        visit_id: Optional[str],
        ipd_id: Optional[str],
        printer_format: PrinterFormat,
        generated_by: str
    ) -> Slip:
        """Generate service slip"""
        if not visit_id and not ipd_id:
            raise ValueError("Either visit_id or ipd_id must be provided")
        
        # Get patient
        if visit_id:
            visit_result = await db.execute(
                select(Visit).where(Visit.visit_id == visit_id)
            )
            visit = visit_result.scalar_one_or_none()
            if not visit:
                raise ValueError("Visit not found")
            patient_id = visit.patient_id
        else:
            ipd_result = await db.execute(
                select(IPD).where(IPD.ipd_id == ipd_id)
            )
            ipd = ipd_result.scalar_one_or_none()
            if not ipd:
                raise ValueError("IPD record not found")
            patient_id = ipd.patient_id
        
        # Get patient
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        
        # Get service charges
        charges_result = await db.execute(
            select(BillingCharge).where(
                BillingCharge.visit_id == visit_id if visit_id else BillingCharge.ipd_id == ipd_id,
                BillingCharge.charge_type == "SERVICE"
            )
        )
        charges = charges_result.scalars().all()
        
        # Generate barcode data
        record_id = visit_id if visit_id else ipd_id
        barcode_data = barcode_service.generate_barcode_data(patient.patient_id, record_id)
        barcode_image = barcode_service.generate_barcode_image(barcode_data)
        
        # Create slip content
        slip_content = {
            "hospital_name": "Hospital Management System",
            "slip_type": "Service",
            "patient": {
                "id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender.value,
                "mobile": patient.mobile_number
            },
            "services": [
                {
                    "name": charge.charge_name,
                    "quantity": charge.quantity,
                    "rate": float(charge.rate),
                    "total": float(charge.total_amount)
                }
                for charge in charges
            ],
            "total_amount": sum(float(charge.total_amount) for charge in charges),
            "barcode_data": barcode_data,
            "generated_date": datetime.now().isoformat()
        }
        
        # Generate slip ID
        slip_id = await generate_id("SLIP")
        
        # Create slip
        slip = Slip(
            slip_id=slip_id,
            patient_id=patient.patient_id,
            visit_id=visit_id,
            ipd_id=ipd_id,
            slip_type=SlipType.SERVICE,
            barcode_data=barcode_data,
            barcode_image=barcode_image,
            slip_content=json.dumps(slip_content),
            printer_format=printer_format,
            generated_by=generated_by
        )
        
        db.add(slip)
        await db.commit()
        await db.refresh(slip)
        
        return slip

    async def generate_ot_slip(
        self,
        db: AsyncSession,
        ipd_id: str,
        printer_format: PrinterFormat,
        generated_by: str
    ) -> Slip:
        """Generate OT slip"""
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
        
        # Get OT charges
        charges_result = await db.execute(
            select(BillingCharge).where(
                BillingCharge.ipd_id == ipd_id,
                BillingCharge.charge_type == "OT"
            )
        )
        charges = charges_result.scalars().all()
        
        # Generate barcode data
        barcode_data = barcode_service.generate_barcode_data(patient.patient_id, ipd_id)
        barcode_image = barcode_service.generate_barcode_image(barcode_data)
        
        # Create slip content
        slip_content = {
            "hospital_name": "Hospital Management System",
            "slip_type": "Operation Theater",
            "patient": {
                "id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender.value,
                "mobile": patient.mobile_number
            },
            "ipd_id": ipd_id,
            "ot_charges": [
                {
                    "name": charge.charge_name,
                    "quantity": charge.quantity,
                    "rate": float(charge.rate),
                    "total": float(charge.total_amount)
                }
                for charge in charges
            ],
            "total_amount": sum(float(charge.total_amount) for charge in charges),
            "barcode_data": barcode_data,
            "generated_date": datetime.now().isoformat()
        }
        
        # Generate slip ID
        slip_id = await generate_id("SLIP")
        
        # Create slip
        slip = Slip(
            slip_id=slip_id,
            patient_id=patient.patient_id,
            ipd_id=ipd_id,
            slip_type=SlipType.OT,
            barcode_data=barcode_data,
            barcode_image=barcode_image,
            slip_content=json.dumps(slip_content),
            printer_format=printer_format,
            generated_by=generated_by
        )
        
        db.add(slip)
        await db.commit()
        await db.refresh(slip)
        
        return slip
    
    async def generate_discharge_slip(
        self,
        db: AsyncSession,
        ipd_id: str,
        printer_format: PrinterFormat,
        generated_by: str
    ) -> Slip:
        """Generate discharge slip with complete bill"""
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
        
        # Get all charges
        charges_result = await db.execute(
            select(BillingCharge).where(BillingCharge.ipd_id == ipd_id)
        )
        charges = charges_result.scalars().all()
        
        # Get all payments
        payments_result = await db.execute(
            select(Payment).where(Payment.ipd_id == ipd_id)
        )
        payments = payments_result.scalars().all()
        
        # Calculate totals
        total_charges = sum(float(charge.total_amount) for charge in charges) + float(ipd.file_charge)
        total_paid = sum(float(payment.amount) for payment in payments)
        balance_due = total_charges - total_paid
        
        # Group charges by type
        charges_by_type = {}
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
        
        # Generate barcode data
        barcode_data = barcode_service.generate_barcode_data(patient.patient_id, ipd_id)
        barcode_image = barcode_service.generate_barcode_image(barcode_data)
        
        # Create slip content
        slip_content = {
            "hospital_name": "Hospital Management System",
            "slip_type": "Discharge Bill",
            "patient": {
                "id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender.value,
                "mobile": patient.mobile_number,
                "address": patient.address
            },
            "ipd": {
                "id": ipd_id,
                "admission_date": ipd.admission_date.isoformat(),
                "discharge_date": ipd.discharge_date.isoformat() if ipd.discharge_date else None,
                "file_charge": float(ipd.file_charge)
            },
            "charges_by_type": charges_by_type,
            "payments": [
                {
                    "date": payment.payment_date.isoformat(),
                    "amount": float(payment.amount),
                    "mode": payment.payment_mode,
                    "type": payment.payment_type.value
                }
                for payment in payments
            ],
            "summary": {
                "total_charges": total_charges,
                "total_paid": total_paid,
                "balance_due": balance_due
            },
            "barcode_data": barcode_data,
            "generated_date": datetime.now().isoformat()
        }
        
        # Generate slip ID
        slip_id = await generate_id("SLIP")
        
        # Create slip
        slip = Slip(
            slip_id=slip_id,
            patient_id=patient.patient_id,
            ipd_id=ipd_id,
            slip_type=SlipType.DISCHARGE,
            barcode_data=barcode_data,
            barcode_image=barcode_image,
            slip_content=json.dumps(slip_content),
            printer_format=printer_format,
            generated_by=generated_by
        )
        
        db.add(slip)
        await db.commit()
        await db.refresh(slip)
        
        return slip
    
    async def reprint_slip(
        self,
        db: AsyncSession,
        original_slip_id: str,
        generated_by: str
    ) -> Slip:
        """Reprint an existing slip"""
        # Get original slip
        original_result = await db.execute(
            select(Slip).where(Slip.slip_id == original_slip_id)
        )
        original_slip = original_result.scalar_one_or_none()
        if not original_slip:
            raise ValueError("Original slip not found")
        
        # Generate new slip ID
        slip_id = await generate_id("SLIP")
        
        # Create reprinted slip
        slip = Slip(
            slip_id=slip_id,
            patient_id=original_slip.patient_id,
            visit_id=original_slip.visit_id,
            ipd_id=original_slip.ipd_id,
            slip_type=original_slip.slip_type,
            barcode_data=original_slip.barcode_data,
            barcode_image=original_slip.barcode_image,
            slip_content=original_slip.slip_content,
            printer_format=original_slip.printer_format,
            is_reprinted=True,
            original_slip_id=original_slip_id,
            generated_by=generated_by
        )
        
        db.add(slip)
        await db.commit()
        await db.refresh(slip)
        
        return slip
    
    async def get_slip_by_id(
        self,
        db: AsyncSession,
        slip_id: str
    ) -> Optional[Slip]:
        """Get slip by ID"""
        result = await db.execute(
            select(Slip).where(Slip.slip_id == slip_id)
        )
        return result.scalar_one_or_none()
    
    async def get_slips_by_patient(
        self,
        db: AsyncSession,
        patient_id: str
    ) -> List[Slip]:
        """Get all slips for a patient"""
        result = await db.execute(
            select(Slip)
            .where(Slip.patient_id == patient_id)
            .order_by(Slip.generated_date.desc())
        )
        return result.scalars().all()
    
    async def get_slips_by_visit(
        self,
        db: AsyncSession,
        visit_id: str
    ) -> List[Slip]:
        """Get all slips for a visit"""
        result = await db.execute(
            select(Slip)
            .where(Slip.visit_id == visit_id)
            .order_by(Slip.generated_date.desc())
        )
        return result.scalars().all()
    
    async def get_slips_by_ipd(
        self,
        db: AsyncSession,
        ipd_id: str
    ) -> List[Slip]:
        """Get all slips for an IPD admission"""
        result = await db.execute(
            select(Slip)
            .where(Slip.ipd_id == ipd_id)
            .order_by(Slip.generated_date.desc())
        )
        return result.scalars().all()


# Global instance
slip_crud = SlipCRUD()
