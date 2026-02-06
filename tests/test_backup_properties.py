"""
Property-based tests for backup and data export operations

**Feature: hospital-management-system**

Property 22: Backup Creation Consistency
Property 23: Data Export Completeness

**Validates: Requirements 19.1, 19.2**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json
from pathlib import Path

from app.crud.backup import backup_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.crud.billing import billing_crud
from app.crud.payment import payment_crud
from app.models.patient import Gender
from app.models.visit import VisitType, PaymentMode
from app.models.bed import WardType
from app.models.billing import ChargeType


def generate_unique_mobile():
    """Generate a unique 10-digit mobile number starting with 9"""
    return "9" + str(uuid.uuid4().int)[:9]


# Strategies
patient_count_strategy = st.integers(min_value=1, max_value=5)
charge_amount_strategy = st.decimals(
    min_value=100,
    max_value=5000,
    places=2,
    allow_nan=False,
    allow_infinity=False
)


class TestBackupCreationConsistency:
    """Property 22: Backup Creation Consistency"""
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(patient_count=patient_count_strategy)
    async def test_backup_includes_all_patient_data(
        self,
        db_session: AsyncSession,
        patient_count: int
    ):
        """
        Property: All patient data should be included in backup
        """
        # Create multiple patients
        created_patients = []
        for i in range(patient_count):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=20 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=generate_unique_mobile()
            )
            created_patients.append(patient)
        
        # Create backup
        backup_name = f"test_backup_{uuid.uuid4().hex[:8]}"
        backup_result = await backup_crud.create_backup(
            db=db_session,
            backup_name=backup_name
        )
        
        try:
            # Load backup file
            backup_file = Path(backup_result["backup_file"])
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Verify all patients are in backup
            backup_patient_ids = {p["patient_id"] for p in backup_data["patients"]}
            created_patient_ids = {p.patient_id for p in created_patients}
            
            # All created patients should be in backup
            assert created_patient_ids.issubset(backup_patient_ids)
            
            # Verify patient data completeness
            for created_patient in created_patients:
                backup_patient = next(
                    (p for p in backup_data["patients"] if p["patient_id"] == created_patient.patient_id),
                    None
                )
                assert backup_patient is not None
                assert backup_patient["name"] == created_patient.name
                assert backup_patient["age"] == created_patient.age
                assert backup_patient["gender"] == created_patient.gender.value
                assert backup_patient["mobile_number"] == created_patient.mobile_number
        
        finally:
            # Cleanup
            if backup_file.exists():
                backup_file.unlink()
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(charge_amount=charge_amount_strategy)
    async def test_backup_includes_all_billing_data(
        self,
        db_session: AsyncSession,
        charge_amount: Decimal
    ):
        """
        Property: All billing data should be included in backup
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Billing Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Test",
            department="General",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        # Create visit
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Create billing charges
        charge_amount = charge_amount.quantize(Decimal("0.01"))
        charge = await billing_crud.create_charge(
            db=db_session,
            visit_id=visit.visit_id,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="Test Investigation",
            rate=charge_amount,
            quantity=1,
            created_by="test_user"
        )
        
        # Create backup
        backup_name = f"test_backup_{uuid.uuid4().hex[:8]}"
        backup_result = await backup_crud.create_backup(
            db=db_session,
            backup_name=backup_name
        )
        
        try:
            # Load backup file
            backup_file = Path(backup_result["backup_file"])
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Verify billing charge is in backup
            backup_charges = backup_data["billing_charges"]
            charge_ids = {c["charge_id"] for c in backup_charges}
            assert charge.charge_id in charge_ids
            
            # Verify charge data completeness
            backup_charge = next(
                (c for c in backup_charges if c["charge_id"] == charge.charge_id),
                None
            )
            assert backup_charge is not None
            assert backup_charge["charge_type"] == charge.charge_type.value
            assert backup_charge["charge_name"] == charge.charge_name
            assert Decimal(str(backup_charge["total_amount"])) == charge.total_amount
        
        finally:
            # Cleanup
            if backup_file.exists():
                backup_file.unlink()
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(patient_count=patient_count_strategy)
    async def test_backup_includes_all_system_data(
        self,
        db_session: AsyncSession,
        patient_count: int
    ):
        """
        Property: All system data (doctors, beds, etc.) should be included in backup
        """
        # Create doctors
        created_doctors = []
        for i in range(patient_count):
            doctor = await doctor_crud.create_doctor(
                db=db_session,
                name=f"Dr. {i}",
                department=f"Department {i}",
                new_patient_fee=Decimal("500.00"),
                followup_fee=Decimal("300.00")
            )
            created_doctors.append(doctor)
        
        # Create beds
        created_beds = []
        for i in range(patient_count):
            bed = await bed_crud.create_bed(
                db=db_session,
                bed_number=f"BED{generate_unique_mobile()[:6]}",
                ward_type=WardType.GENERAL,
                per_day_charge=Decimal("500.00")
            )
            created_beds.append(bed)
        
        # Create backup
        backup_name = f"test_backup_{uuid.uuid4().hex[:8]}"
        backup_result = await backup_crud.create_backup(
            db=db_session,
            backup_name=backup_name
        )
        
        try:
            # Load backup file
            backup_file = Path(backup_result["backup_file"])
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Verify all doctors are in backup
            backup_doctor_ids = {d["doctor_id"] for d in backup_data["doctors"]}
            created_doctor_ids = {d.doctor_id for d in created_doctors}
            assert created_doctor_ids.issubset(backup_doctor_ids)
            
            # Verify all beds are in backup
            backup_bed_ids = {b["bed_id"] for b in backup_data["beds"]}
            created_bed_ids = {b.bed_id for b in created_beds}
            assert created_bed_ids.issubset(backup_bed_ids)
        
        finally:
            # Cleanup
            if backup_file.exists():
                backup_file.unlink()
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(charge_amount=charge_amount_strategy)
    async def test_backup_includes_payment_data(
        self,
        db_session: AsyncSession,
        charge_amount: Decimal
    ):
        """
        Property: All payment data should be included in backup
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Payment Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        # Admit patient to IPD
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Record advance payment
        charge_amount = charge_amount.quantize(Decimal("0.01"))
        payment = await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=charge_amount,
            payment_mode="CASH",
            created_by="test_user"
        )
        
        # Create backup
        backup_name = f"test_backup_{uuid.uuid4().hex[:8]}"
        backup_result = await backup_crud.create_backup(
            db=db_session,
            backup_name=backup_name
        )
        
        try:
            # Load backup file
            backup_file = Path(backup_result["backup_file"])
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Verify payment is in backup
            backup_payments = backup_data["payments"]
            payment_ids = {p["payment_id"] for p in backup_payments}
            assert payment.payment_id in payment_ids
            
            # Verify payment data completeness
            backup_payment = next(
                (p for p in backup_payments if p["payment_id"] == payment.payment_id),
                None
            )
            assert backup_payment is not None
            assert Decimal(str(backup_payment["amount"])) == payment.amount
            assert backup_payment["payment_mode"] == payment.payment_mode
        
        finally:
            # Cleanup
            if backup_file.exists():
                backup_file.unlink()


class TestDataExportCompleteness:
    """Property 23: Data Export Completeness"""
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(patient_count=patient_count_strategy)
    async def test_patient_export_includes_all_requested_data(
        self,
        db_session: AsyncSession,
        patient_count: int
    ):
        """
        Property: Patient export should include all patient data
        """
        # Create multiple patients
        created_patients = []
        for i in range(patient_count):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Export Patient {i}",
                age=25 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Export Address {i}",
                mobile_number=generate_unique_mobile()
            )
            created_patients.append(patient)
        
        # Export patient data
        export_name = f"test_export_{uuid.uuid4().hex[:8]}"
        export_result = await backup_crud.export_data(
            db=db_session,
            export_type="patients"
        )
        
        try:
            # Load export file
            export_file = Path(export_result["export_file"])
            with open(export_file, 'r') as f:
                export_data = json.load(f)
            
            # Verify all patients are in export
            export_patient_ids = {p["patient_id"] for p in export_data["data"]["patients"]}
            created_patient_ids = {p.patient_id for p in created_patients}
            
            # All created patients should be in export
            assert created_patient_ids.issubset(export_patient_ids)
            
            # Verify export contains only patient data (not billing)
            assert "patients" in export_data["data"]
            assert "billing_charges" not in export_data["data"]
        
        finally:
            # Cleanup
            if export_file.exists():
                export_file.unlink()
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(charge_amount=charge_amount_strategy)
    async def test_billing_export_includes_all_requested_data(
        self,
        db_session: AsyncSession,
        charge_amount: Decimal
    ):
        """
        Property: Billing export should include all billing data
        """
        # Create patient and visit
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Billing Export Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Export",
            department="General",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Create billing charge
        charge_amount = charge_amount.quantize(Decimal("0.01"))
        charge = await billing_crud.create_charge(
            db=db_session,
            visit_id=visit.visit_id,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="Export Investigation",
            rate=charge_amount,
            quantity=1,
            created_by="test_user"
        )
        
        # Export billing data
        export_result = await backup_crud.export_data(
            db=db_session,
            export_type="billing"
        )
        
        try:
            # Load export file
            export_file = Path(export_result["export_file"])
            with open(export_file, 'r') as f:
                export_data = json.load(f)
            
            # Verify billing charge is in export
            export_charges = export_data["data"]["billing_charges"]
            charge_ids = {c["charge_id"] for c in export_charges}
            assert charge.charge_id in charge_ids
            
            # Verify export contains only billing data (not patients)
            assert "billing_charges" in export_data["data"]
            assert "patients" not in export_data["data"]
        
        finally:
            # Cleanup
            if export_file.exists():
                export_file.unlink()
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(patient_count=patient_count_strategy)
    async def test_all_export_includes_all_data_types(
        self,
        db_session: AsyncSession,
        patient_count: int
    ):
        """
        Property: "all" export should include both patient and billing data
        """
        # Create patients
        created_patients = []
        for i in range(patient_count):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"All Export Patient {i}",
                age=30 + i,
                gender=Gender.MALE,
                address=f"Address {i}",
                mobile_number=generate_unique_mobile()
            )
            created_patients.append(patient)
        
        # Create doctor and visit with charges
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. All Export",
            department="General",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=created_patients[0].patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        charge = await billing_crud.create_charge(
            db=db_session,
            visit_id=visit.visit_id,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="All Export Investigation",
            rate=Decimal("1000.00"),
            quantity=1,
            created_by="test_user"
        )
        
        # Export all data
        export_result = await backup_crud.export_data(
            db=db_session,
            export_type="all"
        )
        
        try:
            # Load export file
            export_file = Path(export_result["export_file"])
            with open(export_file, 'r') as f:
                export_data = json.load(f)
            
            # Verify both patient and billing data are in export
            assert "patients" in export_data["data"]
            assert "billing_charges" in export_data["data"]
            
            # Verify patients are included
            export_patient_ids = {p["patient_id"] for p in export_data["data"]["patients"]}
            created_patient_ids = {p.patient_id for p in created_patients}
            assert created_patient_ids.issubset(export_patient_ids)
            
            # Verify billing charges are included
            export_charge_ids = {c["charge_id"] for c in export_data["data"]["billing_charges"]}
            assert charge.charge_id in export_charge_ids
        
        finally:
            # Cleanup
            if export_file.exists():
                export_file.unlink()
