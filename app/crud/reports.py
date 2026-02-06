"""
CRUD operations for reporting and patient history
"""

from typing import Optional, List, Dict
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.patient import Patient
from app.models.visit import Visit, VisitType
from app.models.ipd import IPD, IPDStatus
from app.models.billing import BillingCharge, ChargeType
from app.models.payment import Payment, PaymentType
from app.models.doctor import Doctor
from app.models.bed import Bed, BedStatus
from app.models.employee import Employee, EmployeeStatus


class ReportsCRUD:
    """CRUD operations for reports and patient history"""
    
    async def get_patient_history(
        self,
        db: AsyncSession,
        patient_id: str
    ) -> Optional[Dict]:
        """
        Get comprehensive patient history including all visits, charges, and services
        """
        # Get patient with all related data
        patient_result = await db.execute(
            select(Patient)
            .options(
                selectinload(Patient.visits).selectinload(Visit.doctor),
                selectinload(Patient.visits).selectinload(Visit.billing_charges),
                selectinload(Patient.ipd_admissions).selectinload(IPD.bed),
                selectinload(Patient.ipd_admissions).selectinload(IPD.billing_charges)
            )
            .where(Patient.patient_id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        
        if not patient:
            return None
        
        # Get all payments for this patient
        payments_result = await db.execute(
            select(Payment)
            .where(Payment.patient_id == patient_id)
            .order_by(Payment.payment_date.desc())
        )
        payments = payments_result.scalars().all()
        
        # Build comprehensive history
        history = {
            "patient": {
                "patient_id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender.value,
                "address": patient.address,
                "mobile_number": patient.mobile_number,
                "created_date": patient.created_date.isoformat()
            },
            "visits": [],
            "ipd_admissions": [],
            "payments": [],
            "summary": {
                "total_visits": 0,
                "total_ipd_admissions": 0,
                "total_charges": Decimal("0.00"),
                "total_paid": Decimal("0.00"),
                "balance_due": Decimal("0.00")
            }
        }
        
        # Process visits
        for visit in patient.visits:
            visit_charges = []
            visit_total = Decimal(str(visit.opd_fee))
            
            for charge in visit.billing_charges:
                charge_data = {
                    "charge_id": charge.charge_id,
                    "charge_type": charge.charge_type.value,
                    "charge_name": charge.charge_name,
                    "quantity": charge.quantity,
                    "rate": float(charge.rate),
                    "total_amount": float(charge.total_amount),
                    "charge_date": charge.charge_date.isoformat()
                }
                visit_charges.append(charge_data)
                visit_total += charge.total_amount
            
            visit_data = {
                "visit_id": visit.visit_id,
                "visit_type": visit.visit_type.value,
                "visit_date": visit.visit_date.isoformat(),
                "visit_time": visit.visit_time.isoformat(),
                "doctor": {
                    "doctor_id": visit.doctor.doctor_id,
                    "name": visit.doctor.name,
                    "department": visit.doctor.department
                } if visit.doctor else None,
                "serial_number": visit.serial_number,
                "opd_fee": float(visit.opd_fee),
                "payment_mode": visit.payment_mode.value,
                "status": visit.status.value,
                "charges": visit_charges,
                "total_charges": float(visit_total)
            }
            history["visits"].append(visit_data)
            history["summary"]["total_charges"] += visit_total
        
        history["summary"]["total_visits"] = len(patient.visits)
        
        # Process IPD admissions
        for ipd in patient.ipd_admissions:
            ipd_charges = []
            ipd_total = Decimal(str(ipd.file_charge))
            
            for charge in ipd.billing_charges:
                charge_data = {
                    "charge_id": charge.charge_id,
                    "charge_type": charge.charge_type.value,
                    "charge_name": charge.charge_name,
                    "quantity": charge.quantity,
                    "rate": float(charge.rate),
                    "total_amount": float(charge.total_amount),
                    "charge_date": charge.charge_date.isoformat()
                }
                ipd_charges.append(charge_data)
                ipd_total += charge.total_amount
            
            ipd_data = {
                "ipd_id": ipd.ipd_id,
                "admission_date": ipd.admission_date.isoformat(),
                "discharge_date": ipd.discharge_date.isoformat() if ipd.discharge_date else None,
                "file_charge": float(ipd.file_charge),
                "bed": {
                    "bed_id": ipd.bed.bed_id,
                    "bed_number": ipd.bed.bed_number,
                    "ward_type": ipd.bed.ward_type.value,
                    "per_day_charge": float(ipd.bed.per_day_charge)
                } if ipd.bed else None,
                "status": ipd.status.value,
                "charges": ipd_charges,
                "total_charges": float(ipd_total)
            }
            history["ipd_admissions"].append(ipd_data)
            history["summary"]["total_charges"] += ipd_total
        
        history["summary"]["total_ipd_admissions"] = len(patient.ipd_admissions)
        
        # Process payments
        for payment in payments:
            payment_data = {
                "payment_id": payment.payment_id,
                "payment_type": payment.payment_type.value,
                "amount": float(payment.amount),
                "payment_mode": payment.payment_mode,
                "payment_date": payment.payment_date.isoformat(),
                "payment_status": payment.payment_status.value,
                "transaction_reference": payment.transaction_reference,
                "notes": payment.notes,
                "visit_id": payment.visit_id,
                "ipd_id": payment.ipd_id
            }
            history["payments"].append(payment_data)
            history["summary"]["total_paid"] += payment.amount
        
        # Calculate balance
        history["summary"]["balance_due"] = history["summary"]["total_charges"] - history["summary"]["total_paid"]
        
        # Convert Decimals to floats for JSON serialization
        history["summary"]["total_charges"] = float(history["summary"]["total_charges"])
        history["summary"]["total_paid"] = float(history["summary"]["total_paid"])
        history["summary"]["balance_due"] = float(history["summary"]["balance_due"])
        
        return history
    
    async def get_daily_opd_report(
        self,
        db: AsyncSession,
        report_date: date,
        doctor_id: Optional[str] = None
    ) -> Dict:
        """
        Get daily OPD report with patient count and collections
        """
        # Build query
        query = select(Visit).where(Visit.visit_date == report_date)
        
        if doctor_id:
            query = query.where(Visit.doctor_id == doctor_id)
        
        # Get visits
        result = await db.execute(
            query.options(selectinload(Visit.doctor))
        )
        visits = result.scalars().all()
        
        # Calculate statistics
        total_patients = len(visits)
        new_patients = sum(1 for v in visits if v.visit_type == VisitType.OPD_NEW)
        followup_patients = sum(1 for v in visits if v.visit_type == VisitType.OPD_FOLLOWUP)
        total_opd_collection = sum(Decimal(str(v.opd_fee)) for v in visits)
        
        # Group by doctor
        doctor_wise = {}
        for visit in visits:
            if visit.doctor:
                doc_id = visit.doctor.doctor_id
                if doc_id not in doctor_wise:
                    doctor_wise[doc_id] = {
                        "doctor_id": doc_id,
                        "doctor_name": visit.doctor.name,
                        "department": visit.doctor.department,
                        "total_patients": 0,
                        "new_patients": 0,
                        "followup_patients": 0,
                        "collection": Decimal("0.00")
                    }
                
                doctor_wise[doc_id]["total_patients"] += 1
                if visit.visit_type == VisitType.OPD_NEW:
                    doctor_wise[doc_id]["new_patients"] += 1
                else:
                    doctor_wise[doc_id]["followup_patients"] += 1
                doctor_wise[doc_id]["collection"] += Decimal(str(visit.opd_fee))
        
        # Convert to list and format
        doctor_list = []
        for doc_data in doctor_wise.values():
            doc_data["collection"] = float(doc_data["collection"])
            doctor_list.append(doc_data)
        
        return {
            "report_date": report_date.isoformat(),
            "summary": {
                "total_patients": total_patients,
                "new_patients": new_patients,
                "followup_patients": followup_patients,
                "total_collection": float(total_opd_collection)
            },
            "doctor_wise": doctor_list
        }
    
    async def get_doctor_revenue_report(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date,
        doctor_id: Optional[str] = None
    ) -> Dict:
        """
        Get doctor-wise revenue report for a date range
        """
        # Build query
        query = select(Visit).where(
            and_(
                Visit.visit_date >= start_date,
                Visit.visit_date <= end_date
            )
        )
        
        if doctor_id:
            query = query.where(Visit.doctor_id == doctor_id)
        
        # Get visits
        result = await db.execute(
            query.options(selectinload(Visit.doctor))
        )
        visits = result.scalars().all()
        
        # Group by doctor
        doctor_revenue = {}
        for visit in visits:
            if visit.doctor:
                doc_id = visit.doctor.doctor_id
                if doc_id not in doctor_revenue:
                    doctor_revenue[doc_id] = {
                        "doctor_id": doc_id,
                        "doctor_name": visit.doctor.name,
                        "department": visit.doctor.department,
                        "total_patients": 0,
                        "new_patients": 0,
                        "followup_patients": 0,
                        "opd_revenue": Decimal("0.00")
                    }
                
                doctor_revenue[doc_id]["total_patients"] += 1
                if visit.visit_type == VisitType.OPD_NEW:
                    doctor_revenue[doc_id]["new_patients"] += 1
                else:
                    doctor_revenue[doc_id]["followup_patients"] += 1
                doctor_revenue[doc_id]["opd_revenue"] += Decimal(str(visit.opd_fee))
        
        # Convert to list and format
        revenue_list = []
        total_revenue = Decimal("0.00")
        for doc_data in doctor_revenue.values():
            doc_data["opd_revenue"] = float(doc_data["opd_revenue"])
            total_revenue += Decimal(str(doc_data["opd_revenue"]))
            revenue_list.append(doc_data)
        
        # Sort by revenue (descending)
        revenue_list.sort(key=lambda x: x["opd_revenue"], reverse=True)
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_revenue": float(total_revenue),
            "doctor_wise_revenue": revenue_list
        }
    
    async def get_ipd_occupancy_report(
        self,
        db: AsyncSession
    ) -> Dict:
        """
        Get IPD bed occupancy report
        """
        # Get all beds with current IPD admissions
        beds_result = await db.execute(
            select(Bed).order_by(Bed.ward_type, Bed.bed_number)
        )
        beds = beds_result.scalars().all()
        
        # Get active IPD admissions
        ipd_result = await db.execute(
            select(IPD)
            .options(
                selectinload(IPD.patient),
                selectinload(IPD.bed)
            )
            .where(IPD.status == IPDStatus.ADMITTED)
        )
        active_ipds = ipd_result.scalars().all()
        
        # Create bed to IPD mapping
        bed_ipd_map = {ipd.bed_id: ipd for ipd in active_ipds}
        
        # Build occupancy data
        occupancy_data = []
        for bed in beds:
            bed_data = {
                "bed_id": bed.bed_id,
                "bed_number": bed.bed_number,
                "ward_type": bed.ward_type.value,
                "per_day_charge": float(bed.per_day_charge),
                "status": bed.status.value,
                "patient": None
            }
            
            if bed.bed_id in bed_ipd_map:
                ipd = bed_ipd_map[bed.bed_id]
                bed_data["patient"] = {
                    "patient_id": ipd.patient.patient_id,
                    "name": ipd.patient.name,
                    "age": ipd.patient.age,
                    "gender": ipd.patient.gender.value,
                    "ipd_id": ipd.ipd_id,
                    "admission_date": ipd.admission_date.isoformat(),
                    "days_admitted": (datetime.now() - ipd.admission_date).days + 1
                }
            
            occupancy_data.append(bed_data)
        
        # Calculate statistics
        total_beds = len(beds)
        occupied_beds = sum(1 for b in beds if b.status == BedStatus.OCCUPIED)
        available_beds = sum(1 for b in beds if b.status == BedStatus.AVAILABLE)
        maintenance_beds = sum(1 for b in beds if b.status == BedStatus.MAINTENANCE)
        
        return {
            "report_date": datetime.now().isoformat(),
            "summary": {
                "total_beds": total_beds,
                "occupied": occupied_beds,
                "available": available_beds,
                "maintenance": maintenance_beds,
                "occupancy_rate": round((occupied_beds / total_beds * 100) if total_beds > 0 else 0, 2)
            },
            "beds": occupancy_data
        }
    
    async def get_salary_report(
        self,
        db: AsyncSession,
        month: int,
        year: int
    ) -> Dict:
        """
        Get salary report for all active employees
        """
        # Validate month and year
        if month < 1 or month > 12:
            raise ValueError("Invalid month")
        
        if year < 2000 or year > 2100:
            raise ValueError("Invalid year")
        
        # Get all active employees
        employees_result = await db.execute(
            select(Employee)
            .where(Employee.status == EmployeeStatus.ACTIVE)
            .order_by(Employee.name)
        )
        employees = employees_result.scalars().all()
        
        # Build salary report
        salary_data = []
        total_salary = Decimal("0.00")
        
        for employee in employees:
            employee_data = {
                "employee_id": employee.employee_id,
                "name": employee.name,
                "post": employee.post,
                "employment_status": employee.employment_status.value,
                "duty_hours": employee.duty_hours,
                "monthly_salary": float(employee.monthly_salary),
                "joining_date": employee.joining_date.isoformat()
            }
            salary_data.append(employee_data)
            total_salary += employee.monthly_salary
        
        return {
            "month": month,
            "year": year,
            "total_employees": len(employees),
            "total_salary": float(total_salary),
            "employees": salary_data
        }


# Global instance
reports_crud = ReportsCRUD()
