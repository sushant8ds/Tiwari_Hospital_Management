"""
Tests for audit CRUD operations
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.crud.audit import audit_crud
from app.crud.billing import billing_crud
from app.crud.patient import patient_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.models.patient import Gender
from app.models.bed import WardType
from app.models.billing import ChargeType
from app.models.audit import ActionType


class TestAuditCRUD:
    """Test audit CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_log_manual_charge_add(self, db_session: AsyncSession):
        """Test logging manual charge addition"""
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543210"
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="BED001",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Add manual charge (this should create audit log)
        charges = await billing_crud.add_manual_charges(
            db=db_session,
            visit_id=None,
            ipd_id=ipd.ipd_id,
            manual_charges=[{
                "name": "Test Manual Charge",
                "rate": 500.00,
                "quantity": 1
            }],
            created_by="admin_user"
        )
        
        assert len(charges) == 1
        charge = charges[0]
        
        # Verify audit log was created
        audit_logs = await audit_crud.get_audit_logs_by_record(
            db=db_session,
            table_name="billing_charges",
            record_id=charge.charge_id
        )
        
        assert len(audit_logs) == 1
        audit_log = audit_logs[0]
        assert audit_log.action_type == ActionType.MANUAL_CHARGE_ADD
        assert audit_log.user_id == "admin_user"
        assert audit_log.new_value is not None
    
    @pytest.mark.asyncio
    async def test_log_manual_charge_edit(self, db_session: AsyncSession):
        """Test logging manual charge edit"""
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543211"
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="BED002",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Add manual charge
        charges = await billing_crud.add_manual_charges(
            db=db_session,
            visit_id=None,
            ipd_id=ipd.ipd_id,
            manual_charges=[{
                "name": "Test Manual Charge",
                "rate": 500.00,
                "quantity": 1
            }],
            created_by="admin_user"
        )
        
        charge = charges[0]
        
        # Update the charge
        updated_charge = await billing_crud.update_charge(
            db=db_session,
            charge_id=charge.charge_id,
            rate=Decimal("750.00"),
            updated_by="admin_user"
        )
        
        assert updated_charge.rate == Decimal("750.00")
        
        # Verify audit logs (should have 2: add and edit)
        audit_logs = await audit_crud.get_audit_logs_by_record(
            db=db_session,
            table_name="billing_charges",
            record_id=charge.charge_id
        )
        
        assert len(audit_logs) == 2
        # Check that we have both add and edit logs
        action_types = {log.action_type for log in audit_logs}
        assert ActionType.MANUAL_CHARGE_ADD in action_types
        assert ActionType.MANUAL_CHARGE_EDIT in action_types
        
        # Find the edit log
        edit_log = next(log for log in audit_logs if log.action_type == ActionType.MANUAL_CHARGE_EDIT)
        assert edit_log.old_value is not None
        assert edit_log.new_value is not None
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_by_user(self, db_session: AsyncSession):
        """Test getting audit logs by user"""
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543212"
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="BED003",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Add multiple manual charges
        await billing_crud.add_manual_charges(
            db=db_session,
            visit_id=None,
            ipd_id=ipd.ipd_id,
            manual_charges=[
                {"name": "Charge 1", "rate": 100.00, "quantity": 1},
                {"name": "Charge 2", "rate": 200.00, "quantity": 1}
            ],
            created_by="test_admin"
        )
        
        # Get audit logs for user
        logs = await audit_crud.get_audit_logs_by_user(
            db=db_session,
            user_id="test_admin"
        )
        
        assert len(logs) >= 2
        assert all(log.user_id == "test_admin" for log in logs)
