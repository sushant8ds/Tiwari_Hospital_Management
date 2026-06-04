"""
Property-based tests for audit trail completeness

**Feature: hospital-management-system**

Property 18: Audit Trail Completeness

**Validates: Requirements 18.1, 18.2**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json

from app.crud.audit import audit_crud
from app.crud.billing import billing_crud
from app.crud.patient import patient_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.models.patient import Gender
from app.models.bed import WardType
from app.models.audit import ActionType


def generate_unique_mobile():
    """Generate a unique 10-digit mobile number starting with 9"""
    return "9" + str(uuid.uuid4().int)[:9]


# Strategies
charge_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" "),
    min_size=5,
    max_size=30
).filter(lambda x: x.strip() != "")

charge_rate_strategy = st.decimals(
    min_value=100,
    max_value=5000,
    places=2,
    allow_nan=False,
    allow_infinity=False
)

quantity_strategy = st.integers(min_value=1, max_value=5)


class TestAuditTrailCompleteness:
    """Property 18: Audit Trail Completeness"""
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        charge_name=charge_name_strategy,
        charge_rate=charge_rate_strategy,
        quantity=quantity_strategy
    )
    async def test_manual_charge_add_creates_audit_log(
        self,
        db_session: AsyncSession,
        charge_name: str,
        charge_rate: Decimal,
        quantity: int
    ):
        """
        Property: Every manual charge addition should create a complete audit log
        with user_id, timestamp, action_type, and new_value
        """
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
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
        charge_rate = charge_rate.quantize(Decimal("0.01"))
        user_id = "admin_user_test"
        
        charges = await billing_crud.add_manual_charges(
            db=db_session,
            visit_id=None,
            ipd_id=ipd.ipd_id,
            manual_charges=[{
                "name": charge_name.strip(),
                "rate": float(charge_rate),
                "quantity": quantity
            }],
            created_by=user_id
        )
        
        assert len(charges) == 1
        charge = charges[0]
        
        # Verify audit log was created
        audit_logs = await audit_crud.get_audit_logs_by_record(
            db=db_session,
            table_name="billing_charges",
            record_id=charge.charge_id
        )
        
        # Property: Audit log must exist
        assert len(audit_logs) >= 1
        
        # Find the manual charge add log
        add_log = next(
            (log for log in audit_logs if log.action_type == ActionType.MANUAL_CHARGE_ADD),
            None
        )
        assert add_log is not None, "Manual charge add audit log must exist"
        
        # Property: Audit log must have user_id
        assert add_log.user_id == user_id
        
        # Property: Audit log must have timestamp
        assert add_log.timestamp is not None
        
        # Property: Audit log must have correct action_type
        assert add_log.action_type == ActionType.MANUAL_CHARGE_ADD
        
        # Property: Audit log must have new_value with charge details
        assert add_log.new_value is not None
        new_value = json.loads(add_log.new_value)
        assert "charge_name" in new_value
        assert "rate" in new_value
        assert "quantity" in new_value
        assert new_value["charge_name"] == charge_name.strip()
        assert Decimal(str(new_value["rate"])) == charge_rate
        assert new_value["quantity"] == quantity
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        old_rate=charge_rate_strategy,
        new_rate=charge_rate_strategy
    )
    async def test_manual_charge_edit_creates_audit_log(
        self,
        db_session: AsyncSession,
        old_rate: Decimal,
        new_rate: Decimal
    ):
        """
        Property: Every manual charge edit should create a complete audit log
        with user_id, timestamp, action_type, old_value, and new_value
        """
        # Ensure rates are different
        old_rate = old_rate.quantize(Decimal("0.01"))
        new_rate = new_rate.quantize(Decimal("0.01"))
        if old_rate == new_rate:
            new_rate = old_rate + Decimal("100.00")
        
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Add manual charge with old rate
        user_id = "admin_user_test"
        charges = await billing_crud.add_manual_charges(
            db=db_session,
            visit_id=None,
            ipd_id=ipd.ipd_id,
            manual_charges=[{
                "name": "Test Charge",
                "rate": float(old_rate),
                "quantity": 1
            }],
            created_by=user_id
        )
        
        charge = charges[0]
        
        # Update the charge with new rate
        updated_charge = await billing_crud.update_charge(
            db=db_session,
            charge_id=charge.charge_id,
            rate=new_rate,
            updated_by=user_id
        )
        
        assert updated_charge.rate == new_rate
        
        # Verify audit logs
        audit_logs = await audit_crud.get_audit_logs_by_record(
            db=db_session,
            table_name="billing_charges",
            record_id=charge.charge_id
        )
        
        # Property: Should have both add and edit logs
        assert len(audit_logs) >= 2
        
        # Find the edit log
        edit_log = next(
            (log for log in audit_logs if log.action_type == ActionType.MANUAL_CHARGE_EDIT),
            None
        )
        assert edit_log is not None, "Manual charge edit audit log must exist"
        
        # Property: Edit log must have user_id
        assert edit_log.user_id == user_id
        
        # Property: Edit log must have timestamp
        assert edit_log.timestamp is not None
        
        # Property: Edit log must have correct action_type
        assert edit_log.action_type == ActionType.MANUAL_CHARGE_EDIT
        
        # Property: Edit log must have old_value
        assert edit_log.old_value is not None
        old_value = json.loads(edit_log.old_value)
        assert "rate" in old_value
        assert Decimal(str(old_value["rate"])) == old_rate
        
        # Property: Edit log must have new_value
        assert edit_log.new_value is not None
        new_value = json.loads(edit_log.new_value)
        assert "rate" in new_value
        assert Decimal(str(new_value["rate"])) == new_rate
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_charges=st.integers(min_value=2, max_value=5),
        charge_rate=charge_rate_strategy
    )
    async def test_multiple_manual_charges_create_multiple_audit_logs(
        self,
        db_session: AsyncSession,
        num_charges: int,
        charge_rate: Decimal
    ):
        """
        Property: Multiple manual charge operations should create
        corresponding multiple audit log entries
        """
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
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
        charge_rate = charge_rate.quantize(Decimal("0.01"))
        user_id = "admin_user_test"
        
        manual_charges = [
            {
                "name": f"Charge {i+1}",
                "rate": float(charge_rate + Decimal(str(i * 10))),
                "quantity": 1
            }
            for i in range(num_charges)
        ]
        
        charges = await billing_crud.add_manual_charges(
            db=db_session,
            visit_id=None,
            ipd_id=ipd.ipd_id,
            manual_charges=manual_charges,
            created_by=user_id
        )
        
        assert len(charges) == num_charges
        
        # Verify audit logs for each charge
        for charge in charges:
            audit_logs = await audit_crud.get_audit_logs_by_record(
                db=db_session,
                table_name="billing_charges",
                record_id=charge.charge_id
            )
            
            # Property: Each charge must have at least one audit log
            assert len(audit_logs) >= 1
            
            # Property: Each charge must have a manual charge add log
            add_log = next(
                (log for log in audit_logs if log.action_type == ActionType.MANUAL_CHARGE_ADD),
                None
            )
            assert add_log is not None
            assert add_log.user_id == user_id
            assert add_log.timestamp is not None
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(charge_rate=charge_rate_strategy)
    async def test_audit_log_preserves_complete_charge_data(
        self,
        db_session: AsyncSession,
        charge_rate: Decimal
    ):
        """
        Property: Audit log should preserve complete charge data
        including all fields (name, rate, quantity, total)
        """
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Add manual charge with specific data
        charge_rate = charge_rate.quantize(Decimal("0.01"))
        charge_name = "Complete Test Charge"
        quantity = 3
        user_id = "admin_user_test"
        
        charges = await billing_crud.add_manual_charges(
            db=db_session,
            visit_id=None,
            ipd_id=ipd.ipd_id,
            manual_charges=[{
                "name": charge_name,
                "rate": float(charge_rate),
                "quantity": quantity
            }],
            created_by=user_id
        )
        
        charge = charges[0]
        expected_total = charge_rate * quantity
        
        # Get audit log
        audit_logs = await audit_crud.get_audit_logs_by_record(
            db=db_session,
            table_name="billing_charges",
            record_id=charge.charge_id
        )
        
        add_log = next(
            (log for log in audit_logs if log.action_type == ActionType.MANUAL_CHARGE_ADD),
            None
        )
        assert add_log is not None
        
        # Property: Audit log must preserve all charge data
        new_value = json.loads(add_log.new_value)
        
        # Verify all fields are present
        assert "charge_name" in new_value
        assert "rate" in new_value
        assert "quantity" in new_value
        assert "total_amount" in new_value
        
        # Verify values match
        assert new_value["charge_name"] == charge_name
        assert Decimal(str(new_value["rate"])) == charge_rate
        assert new_value["quantity"] == quantity
        assert Decimal(str(new_value["total_amount"])) == expected_total.quantize(Decimal("0.01"))
        
        # Property: Audit log must be retrievable by user
        user_logs = await audit_crud.get_audit_logs_by_user(
            db=db_session,
            user_id=user_id
        )
        
        assert len(user_logs) >= 1
        assert any(log.log_id == add_log.log_id for log in user_logs)
