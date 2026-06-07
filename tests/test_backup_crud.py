"""
Unit tests for backup CRUD operations
"""

import pytest
import json
import os
from pathlib import Path
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.backup import backup_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.billing import billing_crud
from app.models.patient import Gender
from app.models.visit import VisitType, PaymentMode
from app.models.billing import ChargeType


@pytest.mark.asyncio
async def test_create_backup(db_session: AsyncSession):
    """Test creating a database backup"""
    # Create some test data
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="Test Address",
        mobile_number="9876543210"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
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
    
    # Create backup
    backup_result = await backup_crud.create_backup(
        db=db_session,
        backup_name="test_backup"
    )
    
    # Verify backup was created
    assert backup_result["backup_name"] == "test_backup"
    assert "backup_file" in backup_result
    assert "backup_date" in backup_result
    assert "file_size_bytes" in backup_result
    assert "record_counts" in backup_result
    
    # Verify backup file exists
    backup_file = Path(backup_result["backup_file"])
    assert backup_file.exists()
    
    # Verify backup contains data
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    
    assert "backup_metadata" in backup_data
    assert "patients" in backup_data
    assert "doctors" in backup_data
    assert "visits" in backup_data
    
    # Verify record counts
    assert backup_result["record_counts"]["patients"] >= 1
    assert backup_result["record_counts"]["doctors"] >= 1
    assert backup_result["record_counts"]["visits"] >= 1
    
    # Cleanup
    backup_file.unlink()


@pytest.mark.asyncio
async def test_list_backups(db_session: AsyncSession):
    """Test listing available backups"""
    # Create a backup
    backup_result = await backup_crud.create_backup(
        db=db_session,
        backup_name="test_list_backup"
    )
    
    # List backups
    backups = backup_crud.list_backups()
    
    # Verify backup is in the list
    assert len(backups) > 0
    backup_names = [b["backup_name"] for b in backups]
    assert "test_list_backup" in backup_names
    
    # Verify backup metadata
    test_backup = next(b for b in backups if b["backup_name"] == "test_list_backup")
    assert "backup_file" in test_backup
    assert "file_size_bytes" in test_backup
    assert "file_size_mb" in test_backup
    assert "created_date" in test_backup
    
    # Cleanup
    Path(backup_result["backup_file"]).unlink()


@pytest.mark.asyncio
async def test_validate_backup(db_session: AsyncSession):
    """Test validating backup file integrity"""
    # Create a backup
    backup_result = await backup_crud.create_backup(
        db=db_session,
        backup_name="test_validate_backup"
    )
    
    # Validate backup
    validation = backup_crud.validate_backup("test_validate_backup")
    
    # Verify validation passed
    assert validation["valid"] is True
    assert validation["backup_name"] == "test_validate_backup"
    assert "backup_date" in validation
    assert "record_counts" in validation
    
    # Cleanup
    Path(backup_result["backup_file"]).unlink()


@pytest.mark.asyncio
async def test_validate_nonexistent_backup():
    """Test validating a nonexistent backup"""
    with pytest.raises(ValueError, match="Backup file not found"):
        backup_crud.validate_backup("nonexistent_backup")


@pytest.mark.asyncio
async def test_validate_invalid_backup(db_session: AsyncSession):
    """Test validating an invalid backup file"""
    # Create an invalid backup file
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    invalid_backup = backup_dir / "invalid_backup.json"
    
    with open(invalid_backup, 'w') as f:
        json.dump({"invalid": "data"}, f)
    
    # Validate backup
    validation = backup_crud.validate_backup("invalid_backup")
    
    # Verify validation failed
    assert validation["valid"] is False
    assert "error" in validation
    
    # Cleanup
    invalid_backup.unlink()


@pytest.mark.asyncio
async def test_export_data_all(db_session: AsyncSession):
    """Test exporting all data"""
    # Create some test data
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Export Test Patient",
        age=25,
        gender=Gender.FEMALE,
        address="Export Address",
        mobile_number="9123456789"
    )
    
    # Export all data
    export_result = await backup_crud.export_data(
        db=db_session,
        export_type="all"
    )
    
    # Verify export was created
    assert "export_name" in export_result
    assert "export_file" in export_result
    assert "export_date" in export_result
    assert "file_size_bytes" in export_result
    
    # Verify export file exists
    export_file = Path(export_result["export_file"])
    assert export_file.exists()
    
    # Verify export contains data
    with open(export_file, 'r') as f:
        export_data = json.load(f)
    
    assert "export_metadata" in export_data
    assert "data" in export_data
    assert "patients" in export_data["data"]
    
    # Cleanup
    export_file.unlink()


@pytest.mark.asyncio
async def test_export_data_patients_only(db_session: AsyncSession):
    """Test exporting only patient data"""
    # Export patient data
    export_result = await backup_crud.export_data(
        db=db_session,
        export_type="patients"
    )
    
    # Verify export was created
    assert "export_name" in export_result
    
    # Verify export file exists
    export_file = Path(export_result["export_file"])
    assert export_file.exists()
    
    # Verify export contains only patient data
    with open(export_file, 'r') as f:
        export_data = json.load(f)
    
    assert "patients" in export_data["data"]
    assert "billing_charges" not in export_data["data"]
    
    # Cleanup
    export_file.unlink()


@pytest.mark.asyncio
async def test_export_data_billing_only(db_session: AsyncSession):
    """Test exporting only billing data"""
    # Export billing data
    export_result = await backup_crud.export_data(
        db=db_session,
        export_type="billing"
    )
    
    # Verify export was created
    assert "export_name" in export_result
    
    # Verify export file exists
    export_file = Path(export_result["export_file"])
    assert export_file.exists()
    
    # Verify export contains only billing data
    with open(export_file, 'r') as f:
        export_data = json.load(f)
    
    assert "billing_charges" in export_data["data"]
    assert "patients" not in export_data["data"]
    
    # Cleanup
    export_file.unlink()


@pytest.mark.asyncio
async def test_backup_includes_all_tables(db_session: AsyncSession):
    """Test that backup includes all required tables"""
    # Create backup
    backup_result = await backup_crud.create_backup(
        db=db_session,
        backup_name="test_all_tables"
    )
    
    # Load backup file
    backup_file = Path(backup_result["backup_file"])
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    
    # Verify all required tables are present
    required_tables = [
        "patients", "doctors", "visits", "ipd", "beds",
        "billing_charges", "payments", "employees", "audit_logs",
        "ot_procedures", "slips", "users"
    ]
    
    for table in required_tables:
        assert table in backup_data, f"Table {table} missing from backup"
        assert isinstance(backup_data[table], list), f"Table {table} is not a list"
    
    # Cleanup
    backup_file.unlink()


@pytest.mark.asyncio
async def test_restore_backup(db_session: AsyncSession):
    """Test restoring a database backup"""
    # Create test data
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Restore Patient",
        age=45,
        gender=Gender.FEMALE,
        address="Restore Address",
        mobile_number="9999999999"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Restore",
        department="Pediatrics",
        new_patient_fee=Decimal("600.00"),
        followup_fee=Decimal("400.00")
    )
    
    # Create backup
    backup_result = await backup_crud.create_backup(
        db=db_session,
        backup_name="test_restore_db"
    )
    
    backup_file = Path(backup_result["backup_file"])
    assert backup_file.exists()
    
    try:
        # Clear data and restore
        restore_result = await backup_crud.restore_backup(
            db=db_session,
            backup_name="test_restore_db",
            clear_existing=True
        )
        
        assert restore_result["restored"] is True
        assert restore_result["record_counts"]["patients"] >= 1
        
        # Verify database has the restored patient and doctor
        from sqlalchemy import select
        from app.models.patient import Patient
        from app.models.doctor import Doctor
        
        patient_res = await db_session.execute(
            select(Patient).where(Patient.patient_id == patient.patient_id)
        )
        restored_patient = patient_res.scalar()
        assert restored_patient is not None
        assert restored_patient.name == "Restore Patient"
        
        doctor_res = await db_session.execute(
            select(Doctor).where(Doctor.doctor_id == doctor.doctor_id)
        )
        restored_doctor = doctor_res.scalar()
        assert restored_doctor is not None
        assert restored_doctor.name == "Dr. Restore"
        
    finally:
        # Cleanup
        if backup_file.exists():
            backup_file.unlink()


@pytest.mark.asyncio
async def test_restore_legacy_backup(db_session: AsyncSession):
    """Test restoring a legacy backup (older version without user credentials or salary_payments)"""
    backup_name = "test_legacy_backup"
    backup_file = Path("backups") / f"{backup_name}.json"
    
    # Construct a legacy backup JSON
    legacy_data = {
        "backup_metadata": {
            "backup_name": backup_name,
            "backup_date": "2026-06-01T00:00:00",
            "version": "0.9"
        },
        "patients": [],
        "doctors": [],
        "visits": [],
        "ipd": [],
        "beds": [],
        "billing_charges": [],
        "payments": [],
        "employees": [],
        "audit_logs": [],
        "ot_procedures": [],
        "slips": [],
        "users": [
            {
                "user_id": "U20260601001",
                "username": "legacy_admin",
                "role": "ADMIN",
                "is_active": True,
                "created_date": "2026-06-01T00:00:00"
            }
        ]
    }
    
    # Write to file
    with open(backup_file, 'w') as f:
        json.dump(legacy_data, f)
        
    try:
        # Restore legacy backup
        restore_result = await backup_crud.restore_backup(
            db=db_session,
            backup_name=backup_name,
            clear_existing=True
        )
        
        assert restore_result["restored"] is True
        
        # Verify the user is restored and has fallback values populated
        from sqlalchemy import select
        from app.models.user import User
        
        res = await db_session.execute(
            select(User).where(User.user_id == "U20260601001")
        )
        restored_user = res.scalar()
        assert restored_user is not None
        assert restored_user.username == "legacy_admin"
        assert restored_user.email == "legacy_admin@example.com"
        assert restored_user.full_name == "Legacy_admin"
        assert restored_user.hashed_password is not None
        
    finally:
        # Cleanup
        if backup_file.exists():
            backup_file.unlink()
