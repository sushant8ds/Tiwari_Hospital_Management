"""
CRUD operations for database backup and recovery
"""

import os
import json
import shutil
from typing import Optional, Dict, List
from datetime import datetime, date, time
from decimal import Decimal
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.patient import Patient, Gender
from app.models.doctor import Doctor, DoctorStatus
from app.models.visit import Visit, VisitType, PaymentMode as VisitPaymentMode, VisitStatus
from app.models.ipd import IPD, IPDStatus
from app.models.bed import Bed, WardType, BedStatus
from app.models.billing import BillingCharge, ChargeType
from app.models.payment import Payment, PaymentType, PaymentStatus
from app.models.employee import Employee, EmploymentStatus, EmployeeStatus
from app.models.salary_payment import SalaryPayment, PaymentStatus as SalaryPaymentStatus
from app.models.audit import AuditLog, ActionType
from app.models.ot import OTProcedure
from app.models.slip import Slip, SlipType, PrinterFormat
from app.models.user import User, UserRole
from app.core.security import get_password_hash


class BackupCRUD:
    """CRUD operations for backup and recovery"""
    
    def __init__(self):
        # Create backup directory if it doesn't exist
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_backup(
        self,
        db: AsyncSession,
        backup_name: Optional[str] = None
    ) -> Dict:
        """
        Create a complete database backup
        
        Returns backup metadata including filename and timestamp
        """
        # Generate backup filename
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"hospital_backup_{timestamp}"
        
        backup_file = self.backup_dir / f"{backup_name}.json"
        
        # Collect all data from database
        backup_data = {
            "backup_metadata": {
                "backup_name": backup_name,
                "backup_date": datetime.now().isoformat(),
                "version": "1.0"
            },
            "patients": [],
            "doctors": [],
            "visits": [],
            "ipd": [],
            "beds": [],
            "billing_charges": [],
            "payments": [],
            "employees": [],
            "salary_payments": [],
            "audit_logs": [],
            "ot_procedures": [],
            "slips": [],
            "users": []
        }
        
        # Export patients
        patients_result = await db.execute(select(Patient))
        patients = patients_result.scalars().all()
        for patient in patients:
            backup_data["patients"].append({
                "patient_id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender.value,
                "address": patient.address,
                "mobile_number": patient.mobile_number,
                "created_date": patient.created_date.isoformat(),
                "updated_date": patient.updated_date.isoformat()
            })
        
        # Export doctors
        doctors_result = await db.execute(select(Doctor))
        doctors = doctors_result.scalars().all()
        for doctor in doctors:
            backup_data["doctors"].append({
                "doctor_id": doctor.doctor_id,
                "name": doctor.name,
                "department": doctor.department,
                "new_patient_fee": float(doctor.new_patient_fee),
                "followup_fee": float(doctor.followup_fee),
                "status": doctor.status.value,
                "created_date": doctor.created_date.isoformat()
            })
        
        # Export visits
        visits_result = await db.execute(select(Visit))
        visits = visits_result.scalars().all()
        for visit in visits:
            backup_data["visits"].append({
                "visit_id": visit.visit_id,
                "patient_id": visit.patient_id,
                "visit_type": visit.visit_type.value,
                "doctor_id": visit.doctor_id,
                "department": visit.department,
                "serial_number": visit.serial_number,
                "visit_date": visit.visit_date.isoformat(),
                "visit_time": visit.visit_time.isoformat(),
                "opd_fee": float(visit.opd_fee),
                "payment_mode": visit.payment_mode.value,
                "status": visit.status.value,
                "created_date": visit.created_date.isoformat()
            })
        
        # Export IPD
        ipd_result = await db.execute(select(IPD))
        ipd_records = ipd_result.scalars().all()
        for ipd in ipd_records:
            backup_data["ipd"].append({
                "ipd_id": ipd.ipd_id,
                "patient_id": ipd.patient_id,
                "visit_id": ipd.visit_id,
                "admission_date": ipd.admission_date.isoformat(),
                "discharge_date": ipd.discharge_date.isoformat() if ipd.discharge_date else None,
                "file_charge": float(ipd.file_charge),
                "bed_id": ipd.bed_id,
                "referred_by": ipd.referred_by,
                "diagnosis": ipd.diagnosis,
                "procedure_performed": ipd.procedure_performed,
                "operation_date": ipd.operation_date.isoformat() if ipd.operation_date else None,
                "discount": float(ipd.discount),
                "status": ipd.status.value,
                "created_date": ipd.created_date.isoformat()
            })
        
        # Export beds
        beds_result = await db.execute(select(Bed))
        beds = beds_result.scalars().all()
        for bed in beds:
            backup_data["beds"].append({
                "bed_id": bed.bed_id,
                "bed_number": bed.bed_number,
                "ward_type": bed.ward_type.value,
                "per_day_charge": float(bed.per_day_charge),
                "status": bed.status.value,
                "created_date": bed.created_date.isoformat()
            })
        
        # Export billing charges
        charges_result = await db.execute(select(BillingCharge))
        charges = charges_result.scalars().all()
        for charge in charges:
            backup_data["billing_charges"].append({
                "charge_id": charge.charge_id,
                "visit_id": charge.visit_id,
                "ipd_id": charge.ipd_id,
                "charge_type": charge.charge_type.value,
                "charge_name": charge.charge_name,
                "quantity": charge.quantity,
                "rate": float(charge.rate),
                "total_amount": float(charge.total_amount),
                "charge_date": charge.charge_date.isoformat(),
                "created_by": charge.created_by
            })
        
        # Export payments
        payments_result = await db.execute(select(Payment))
        payments = payments_result.scalars().all()
        for payment in payments:
            backup_data["payments"].append({
                "payment_id": payment.payment_id,
                "patient_id": payment.patient_id,
                "visit_id": payment.visit_id,
                "ipd_id": payment.ipd_id,
                "payment_type": payment.payment_type.value,
                "amount": float(payment.amount),
                "payment_mode": payment.payment_mode,
                "payment_status": payment.payment_status.value,
                "payment_date": payment.payment_date.isoformat(),
                "transaction_reference": payment.transaction_reference,
                "notes": payment.notes,
                "created_by": payment.created_by
            })
        
        # Export employees
        employees_result = await db.execute(select(Employee))
        employees = employees_result.scalars().all()
        for employee in employees:
            backup_data["employees"].append({
                "employee_id": employee.employee_id,
                "name": employee.name,
                "post": employee.post,
                "qualification": employee.qualification,
                "employment_status": employee.employment_status.value,
                "duty_hours": employee.duty_hours,
                "joining_date": employee.joining_date.isoformat(),
                "monthly_salary": float(employee.monthly_salary),
                "status": employee.status.value,
                "created_date": employee.created_date.isoformat()
            })
        
        # Export salary payments
        salary_payments_result = await db.execute(select(SalaryPayment))
        salary_payments = salary_payments_result.scalars().all()
        for payment in salary_payments:
            backup_data["salary_payments"].append({
                "payment_id": payment.payment_id,
                "employee_id": payment.employee_id,
                "month": payment.month,
                "year": payment.year,
                "amount": float(payment.amount),
                "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
                "status": payment.status.value,
                "notes": payment.notes,
                "created_date": payment.created_date.isoformat(),
                "updated_date": payment.updated_date.isoformat() if payment.updated_date else None
            })
        
        # Export audit logs
        audit_result = await db.execute(select(AuditLog))
        audit_logs = audit_result.scalars().all()
        for log in audit_logs:
            backup_data["audit_logs"].append({
                "log_id": log.log_id,
                "user_id": log.user_id,
                "action_type": log.action_type.value,
                "table_name": log.table_name,
                "record_id": log.record_id,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "timestamp": log.timestamp.isoformat()
            })
        
        # Export OT procedures
        ot_result = await db.execute(select(OTProcedure))
        ot_procedures = ot_result.scalars().all()
        for ot in ot_procedures:
            backup_data["ot_procedures"].append({
                "ot_id": ot.ot_id,
                "ipd_id": ot.ipd_id,
                "operation_name": ot.operation_name,
                "operation_date": ot.operation_date.isoformat(),
                "duration_minutes": ot.duration_minutes,
                "surgeon_name": ot.surgeon_name,
                "anesthesia_type": ot.anesthesia_type,
                "notes": ot.notes,
                "created_by": ot.created_by,
                "created_date": ot.created_date.isoformat()
            })
        
        # Export slips
        slips_result = await db.execute(select(Slip))
        slips = slips_result.scalars().all()
        for slip in slips:
            backup_data["slips"].append({
                "slip_id": slip.slip_id,
                "slip_type": slip.slip_type.value,
                "patient_id": slip.patient_id,
                "visit_id": slip.visit_id,
                "ipd_id": slip.ipd_id,
                "slip_content": slip.slip_content,
                "barcode_data": slip.barcode_data,
                "printer_format": slip.printer_format.value,
                "created_date": slip.generated_date.isoformat()
            })
        
        # Export users (with passwords for security, and email/full_name)
        users_result = await db.execute(select(User))
        users = users_result.scalars().all()
        for user in users:
            backup_data["users"].append({
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "hashed_password": user.hashed_password,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_date": user.created_date.isoformat()
            })
        
        # Write backup to file
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        # Calculate file size
        file_size = os.path.getsize(backup_file)
        
        return {
            "backup_name": backup_name,
            "backup_file": str(backup_file),
            "backup_date": backup_data["backup_metadata"]["backup_date"],
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "record_counts": {
                "patients": len(backup_data["patients"]),
                "doctors": len(backup_data["doctors"]),
                "visits": len(backup_data["visits"]),
                "ipd": len(backup_data["ipd"]),
                "beds": len(backup_data["beds"]),
                "billing_charges": len(backup_data["billing_charges"]),
                "payments": len(backup_data["payments"]),
                "employees": len(backup_data["employees"]),
                "salary_payments": len(backup_data["salary_payments"]),
                "audit_logs": len(backup_data["audit_logs"]),
                "ot_procedures": len(backup_data["ot_procedures"]),
                "slips": len(backup_data["slips"]),
                "users": len(backup_data["users"])
            }
        }
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.json"):
            file_stat = backup_file.stat()
            backups.append({
                "backup_name": backup_file.stem,
                "backup_file": str(backup_file),
                "file_size_bytes": file_stat.st_size,
                "file_size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                "created_date": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            })
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x["created_date"], reverse=True)
        
        return backups
    
    def validate_backup(self, backup_name: str) -> Dict:
        """
        Validate backup file integrity
        
        Returns validation results including record counts and any errors
        """
        backup_file = self.backup_dir / f"{backup_name}.json"
        
        if not backup_file.exists():
            raise ValueError(f"Backup file not found: {backup_name}")
        
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Validate structure
            required_keys = [
                "backup_metadata", "patients", "doctors", "visits", "ipd",
                "beds", "billing_charges", "payments", "employees",
                "audit_logs", "ot_procedures", "slips", "users"
            ]
            
            missing_keys = [key for key in required_keys if key not in backup_data]
            
            if missing_keys:
                return {
                    "valid": False,
                    "error": f"Missing required keys: {', '.join(missing_keys)}"
                }
            
            # Validate metadata
            if "backup_date" not in backup_data["backup_metadata"]:
                return {
                    "valid": False,
                    "error": "Missing backup_date in metadata"
                }
            
            return {
                "valid": True,
                "backup_name": backup_name,
                "backup_date": backup_data["backup_metadata"]["backup_date"],
                "record_counts": {
                    "patients": len(backup_data["patients"]),
                    "doctors": len(backup_data["doctors"]),
                    "visits": len(backup_data["visits"]),
                    "ipd": len(backup_data["ipd"]),
                    "beds": len(backup_data["beds"]),
                    "billing_charges": len(backup_data["billing_charges"]),
                    "payments": len(backup_data["payments"]),
                    "employees": len(backup_data["employees"]),
                    "salary_payments": len(backup_data.get("salary_payments", [])),
                    "audit_logs": len(backup_data["audit_logs"]),
                    "ot_procedures": len(backup_data["ot_procedures"]),
                    "slips": len(backup_data["slips"]),
                    "users": len(backup_data["users"])
                }
            }
        
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"Invalid JSON format: {str(e)}"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
    
    async def restore_backup(
        self,
        db: AsyncSession,
        backup_name: str,
        clear_existing: bool = False
    ) -> Dict:
        """
        Restore database from backup
        
        WARNING: This will overwrite existing data if clear_existing=True
        """
        backup_file = self.backup_dir / f"{backup_name}.json"
        
        if not backup_file.exists():
            raise ValueError(f"Backup file not found: {backup_name}")
        
        # Validate backup first
        validation = self.validate_backup(backup_name)
        if not validation["valid"]:
            raise ValueError(f"Backup validation failed: {validation['error']}")
        
        # Load backup data
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Clear existing data if requested
        if clear_existing:
            try:
                # Delete in reverse order of dependencies
                await db.execute(text("DELETE FROM slips"))
                await db.execute(text("DELETE FROM ot_procedures"))
                await db.execute(text("DELETE FROM audit_logs"))
                await db.execute(text("DELETE FROM payments"))
                await db.execute(text("DELETE FROM billing_charges"))
                await db.execute(text("DELETE FROM ipd"))
                await db.execute(text("DELETE FROM visits"))
                await db.execute(text("DELETE FROM salary_payments"))
                await db.execute(text("DELETE FROM beds"))
                await db.execute(text("DELETE FROM employees"))
                await db.execute(text("DELETE FROM doctors"))
                await db.execute(text("DELETE FROM patients"))
                await db.execute(text("DELETE FROM users"))
                await db.commit()
            except Exception as e:
                await db.rollback()
                raise ValueError(f"Clearing existing data failed: {str(e)}")
        
        try:
            # 1. Restore Users
            for u in backup_data.get("users", []):
                created_date = datetime.fromisoformat(u["created_date"]) if u.get("created_date") else datetime.now()
                updated_date = datetime.fromisoformat(u["updated_date"]) if u.get("updated_date") else created_date
                
                # Fallbacks for older backup formats:
                email = u.get("email") or f"{u['username']}@example.com"
                hashed_password = u.get("hashed_password") or get_password_hash("default_password")
                full_name = u.get("full_name") or u["username"].capitalize()
                
                user = User(
                    user_id=u["user_id"],
                    username=u["username"],
                    email=email,
                    hashed_password=hashed_password,
                    full_name=full_name,
                    role=UserRole(u["role"]),
                    is_active=u["is_active"],
                    created_date=created_date,
                    updated_date=updated_date
                )
                db.add(user)
            
            # 2. Restore Doctors
            for d in backup_data.get("doctors", []):
                created_date = datetime.fromisoformat(d["created_date"]) if d.get("created_date") else datetime.now()
                doctor = Doctor(
                    doctor_id=d["doctor_id"],
                    name=d["name"],
                    department=d["department"],
                    new_patient_fee=Decimal(str(d["new_patient_fee"])),
                    followup_fee=Decimal(str(d["followup_fee"])),
                    status=DoctorStatus(d["status"]),
                    created_date=created_date
                )
                db.add(doctor)
            
            # 3. Restore Beds
            for b in backup_data.get("beds", []):
                created_date = datetime.fromisoformat(b["created_date"]) if b.get("created_date") else datetime.now()
                bed = Bed(
                    bed_id=b["bed_id"],
                    bed_number=b["bed_number"],
                    ward_type=WardType(b["ward_type"]),
                    per_day_charge=Decimal(str(b["per_day_charge"])),
                    status=BedStatus(b["status"]),
                    created_date=created_date
                )
                db.add(bed)
            
            # 4. Restore Employees
            for e in backup_data.get("employees", []):
                created_date = datetime.fromisoformat(e["created_date"]) if e.get("created_date") else datetime.now()
                joining_date = date.fromisoformat(e["joining_date"]) if e.get("joining_date") else date.today()
                employee = Employee(
                    employee_id=e["employee_id"],
                    name=e["name"],
                    post=e["post"],
                    qualification=e.get("qualification"),
                    employment_status=EmploymentStatus(e["employment_status"]),
                    duty_hours=e["duty_hours"],
                    joining_date=joining_date,
                    monthly_salary=Decimal(str(e["monthly_salary"])),
                    status=EmployeeStatus(e["status"]),
                    created_date=created_date
                )
                db.add(employee)
            
            # 5. Restore Patients
            for p in backup_data.get("patients", []):
                created_date = datetime.fromisoformat(p["created_date"]) if p.get("created_date") else datetime.now()
                updated_date = datetime.fromisoformat(p["updated_date"]) if p.get("updated_date") else created_date
                patient = Patient(
                    patient_id=p["patient_id"],
                    name=p["name"],
                    age=p["age"],
                    gender=Gender(p["gender"]),
                    address=p["address"],
                    mobile_number=p["mobile_number"],
                    created_date=created_date,
                    updated_date=updated_date
                )
                db.add(patient)
            
            await db.flush()
            
            # 6. Restore Salary Payments
            for sp in backup_data.get("salary_payments", []):
                created_date = datetime.fromisoformat(sp["created_date"]) if sp.get("created_date") else datetime.now()
                updated_date = datetime.fromisoformat(sp["updated_date"]) if sp.get("updated_date") else created_date
                payment_date = date.fromisoformat(sp["payment_date"]) if sp.get("payment_date") else None
                
                salary_payment = SalaryPayment(
                    payment_id=sp["payment_id"],
                    employee_id=sp["employee_id"],
                    month=sp["month"],
                    year=sp["year"],
                    amount=Decimal(str(sp["amount"])),
                    payment_date=payment_date,
                    status=SalaryPaymentStatus(sp["status"]),
                    notes=sp.get("notes"),
                    created_date=created_date,
                    updated_date=updated_date
                )
                db.add(salary_payment)
            
            # 7. Restore Visits
            for v in backup_data.get("visits", []):
                created_date = datetime.fromisoformat(v["created_date"]) if v.get("created_date") else datetime.now()
                visit_date = date.fromisoformat(v["visit_date"]) if v.get("visit_date") else date.today()
                visit_time = time.fromisoformat(v["visit_time"]) if v.get("visit_time") else time(0, 0)
                visit = Visit(
                    visit_id=v["visit_id"],
                    patient_id=v["patient_id"],
                    visit_type=VisitType(v["visit_type"]),
                    doctor_id=v["doctor_id"],
                    department=v["department"],
                    serial_number=v["serial_number"],
                    visit_date=visit_date,
                    visit_time=visit_time,
                    opd_fee=Decimal(str(v["opd_fee"])),
                    payment_mode=VisitPaymentMode(v["payment_mode"]),
                    status=VisitStatus(v["status"]),
                    created_date=created_date
                )
                db.add(visit)
            
            await db.flush()
            
            # 8. Restore IPD
            for ipd_data in backup_data.get("ipd", []):
                created_date = datetime.fromisoformat(ipd_data["created_date"]) if ipd_data.get("created_date") else datetime.now()
                admission_date = datetime.fromisoformat(ipd_data["admission_date"]) if ipd_data.get("admission_date") else datetime.now()
                discharge_date = datetime.fromisoformat(ipd_data["discharge_date"]) if ipd_data.get("discharge_date") else None
                
                ipd = IPD(
                    ipd_id=ipd_data["ipd_id"],
                    patient_id=ipd_data["patient_id"],
                    visit_id=ipd_data.get("visit_id"),
                    admission_date=admission_date,
                    discharge_date=discharge_date,
                    file_charge=Decimal(str(ipd_data.get("file_charge", 0.0))),
                    bed_id=ipd_data["bed_id"],
                    attending_doctor_id=ipd_data.get("attending_doctor_id"),
                    referred_by=ipd_data.get("referred_by"),
                    diagnosis=ipd_data.get("diagnosis"),
                    procedure_performed=ipd_data.get("procedure_performed"),
                    operation_date=datetime.fromisoformat(ipd_data["operation_date"]) if ipd_data.get("operation_date") else None,
                    discount=Decimal(str(ipd_data.get("discount", 0.0))),
                    status=IPDStatus(ipd_data["status"]) if ipd_data.get("status") else IPDStatus.ADMITTED,
                    created_date=created_date
                )
                db.add(ipd)
            
            await db.flush()
            
            # 9. Restore Billing Charges
            for c in backup_data.get("billing_charges", []):
                charge_date = datetime.fromisoformat(c["charge_date"]) if c.get("charge_date") else datetime.now()
                charge = BillingCharge(
                    charge_id=c["charge_id"],
                    visit_id=c.get("visit_id"),
                    ipd_id=c.get("ipd_id"),
                    charge_type=ChargeType(c["charge_type"]),
                    charge_name=c["charge_name"],
                    quantity=c.get("quantity", 1),
                    rate=Decimal(str(c["rate"])),
                    total_amount=Decimal(str(c["total_amount"])),
                    charge_date=charge_date,
                    created_by=c.get("created_by", "SYSTEM")
                )
                db.add(charge)
            
            # 10. Restore Payments
            for pay in backup_data.get("payments", []):
                payment_date = datetime.fromisoformat(pay["payment_date"]) if pay.get("payment_date") else datetime.now()
                payment = Payment(
                    payment_id=pay["payment_id"],
                    patient_id=pay["patient_id"],
                    visit_id=pay.get("visit_id"),
                    ipd_id=pay.get("ipd_id"),
                    payment_type=PaymentType(pay["payment_type"]),
                    amount=Decimal(str(pay["amount"])),
                    payment_mode=pay["payment_mode"],
                    payment_status=PaymentStatus(pay["payment_status"]),
                    transaction_reference=pay.get("transaction_reference"),
                    notes=pay.get("notes"),
                    payment_date=payment_date,
                    created_by=pay.get("created_by", "SYSTEM")
                )
                db.add(payment)
            
            # 11. Restore OT Procedures
            for ot in backup_data.get("ot_procedures", []):
                operation_date = datetime.fromisoformat(ot["operation_date"]) if ot.get("operation_date") else datetime.now()
                created_date = datetime.fromisoformat(ot["created_date"]) if ot.get("created_date") else datetime.now()
                ot_proc = OTProcedure(
                    ot_id=ot["ot_id"],
                    ipd_id=ot["ipd_id"],
                    operation_name=ot["operation_name"],
                    operation_date=operation_date,
                    duration_minutes=ot["duration_minutes"],
                    surgeon_name=ot["surgeon_name"],
                    anesthesia_type=ot.get("anesthesia_type"),
                    notes=ot.get("notes"),
                    created_by=ot.get("created_by", "SYSTEM"),
                    created_date=created_date
                )
                db.add(ot_proc)
            
            # 12. Restore Slips
            for s in backup_data.get("slips", []):
                created_date_str = s.get("created_date") or s.get("generated_date")
                created_date = datetime.fromisoformat(created_date_str) if created_date_str else datetime.now()
                slip = Slip(
                    slip_id=s["slip_id"],
                    slip_type=SlipType(s["slip_type"]),
                    patient_id=s["patient_id"],
                    visit_id=s.get("visit_id"),
                    ipd_id=s.get("ipd_id"),
                    slip_content=s["slip_content"],
                    barcode_data=s["barcode_data"],
                    printer_format=PrinterFormat(s["printer_format"]) if s.get("printer_format") else PrinterFormat.A4,
                    generated_date=created_date,
                    generated_by=s.get("generated_by", "SYSTEM")
                )
                db.add(slip)
            
            # 13. Restore Audit Logs
            for log in backup_data.get("audit_logs", []):
                timestamp = datetime.fromisoformat(log["timestamp"]) if log.get("timestamp") else datetime.now()
                audit_log = AuditLog(
                    log_id=log["log_id"],
                    user_id=log["user_id"],
                    action_type=ActionType(log["action_type"]),
                    table_name=log["table_name"],
                    record_id=log["record_id"],
                    old_value=log.get("old_value"),
                    new_value=log.get("new_value"),
                    timestamp=timestamp
                )
                db.add(audit_log)
                
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise ValueError(f"Restore failed: {str(e)}")
        
        return {
            "restored": True,
            "backup_name": backup_name,
            "backup_date": backup_data["backup_metadata"]["backup_date"],
            "restore_date": datetime.now().isoformat(),
            "record_counts": validation["record_counts"]
        }
    
    async def export_data(
        self,
        db: AsyncSession,
        export_type: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Export specific data for Admin users
        
        export_type: "all", "patients", "billing", "visits", "ipd"
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = f"export_{export_type}_{timestamp}"
        export_file = self.backup_dir / f"{export_name}.json"
        
        export_data = {
            "export_metadata": {
                "export_name": export_name,
                "export_type": export_type,
                "export_date": datetime.now().isoformat(),
                "start_date": start_date,
                "end_date": end_date
            },
            "data": {}
        }
        
        # Export based on type
        if export_type in ["all", "patients"]:
            patients_result = await db.execute(select(Patient))
            patients = patients_result.scalars().all()
            export_data["data"]["patients"] = [
                {
                    "patient_id": p.patient_id,
                    "name": p.name,
                    "age": p.age,
                    "gender": p.gender.value,
                    "mobile_number": p.mobile_number,
                    "created_date": p.created_date.isoformat()
                }
                for p in patients
            ]
        
        if export_type in ["all", "billing"]:
            charges_result = await db.execute(select(BillingCharge))
            charges = charges_result.scalars().all()
            export_data["data"]["billing_charges"] = [
                {
                    "charge_id": c.charge_id,
                    "charge_type": c.charge_type.value,
                    "charge_name": c.charge_name,
                    "total_amount": float(c.total_amount),
                    "charge_date": c.charge_date.isoformat()
                }
                for c in charges
            ]
        
        # Write export to file
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        file_size = os.path.getsize(export_file)
        
        return {
            "export_name": export_name,
            "export_file": str(export_file),
            "export_date": export_data["export_metadata"]["export_date"],
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }


# Global instance
backup_crud = BackupCRUD()
