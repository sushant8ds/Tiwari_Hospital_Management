"""
Property-based tests for data linkage integrity

**Feature: hospital-management-system, Property 8: Data Linkage Integrity**
**Validates: Requirements 2.4, 14.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from decimal import Decimal
from datetime import datetime

from app.models.patient import Patient, Gender
from app.models.doctor import Doctor, DoctorStatus
from app.models.visit import Visit, VisitType, PaymentMode
from app.models.billing import BillingCharge, ChargeType
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.billing import billing_crud


class TestDataLinkageIntegrityProperty:
    """Property-based tests for data linkage integrity"""
    
    @given(
        num_charges=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_charges_linked_to_valid_visit_property(
        self,
        db_session: AsyncSession,
        num_charges: int
    ):
        """
        Property: For any charge entry, the charge should be properly linked 
        to a valid Visit_ID.
        
        **Validates: Requirements 2.4, 14.3**
        """
        # Create patient, doctor, and visit
        import time
        mobile = f"9{int(time.time() * 1000) % 1000000000:09d}"
        
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=mobile
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
        
        # Create various charge types
        charge_types = [ChargeType.INVESTIGATION, ChargeType.PROCEDURE, ChargeType.SERVICE, ChargeType.MANUAL]
        
        for i in range(num_charges):
            charge_type = charge_types[i % len(charge_types)]
            
            charge = await billing_crud.create_charge(
                db=db_session,
                charge_type=charge_type,
                charge_name=f"Charge {i}",
                rate=Decimal("100.00"),
                quantity=1,
                visit_id=visit.visit_id,
                created_by="test_user"
            )
            
            # CRITICAL PROPERTY 1: Charge must have visit_id
            assert charge.visit_id is not None, (
                f"Charge {charge.charge_id} must have a visit_id"
            )
            
            # CRITICAL PROPERTY 2: Charge must be linked to the correct visit
            assert charge.visit_id == visit.visit_id, (
                f"Charge {charge.charge_id} visit_id {charge.visit_id} should match "
                f"created visit_id {visit.visit_id}"
            )
            
            # CRITICAL PROPERTY 3: Visit must exist in database
            retrieved_visit = await visit_crud.get_visit_by_id(db_session, charge.visit_id)
            assert retrieved_visit is not None, (
                f"Visit {charge.visit_id} linked to charge {charge.charge_id} must exist"
            )
            
            # CRITICAL PROPERTY 4: Visit must belong to the correct patient
            assert retrieved_visit.patient_id == patient.patient_id, (
                f"Visit {charge.visit_id} patient_id {retrieved_visit.patient_id} should match "
                f"patient_id {patient.patient_id}"
            )
    
    @given(
        num_investigation_charges=st.integers(min_value=1, max_value=5),
        num_manual_charges=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_investigation_and_manual_charges_linkage_property(
        self,
        db_session: AsyncSession,
        num_investigation_charges: int,
        num_manual_charges: int
    ):
        """
        Property: Investigation charges (Req 2.4) and manual charges (Req 14.3) 
        must be properly linked to valid visits.
        
        **Validates: Requirements 2.4, 14.3**
        """
        # Create patient, doctor, and visit
        import time
        mobile = f"9{int(time.time() * 1000) % 1000000000:09d}"
        
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=mobile
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
        
        # Add investigation charges
        investigations = [
            {"name": f"Investigation {i}", "rate": 100 + (i * 50), "quantity": 1}
            for i in range(num_investigation_charges)
        ]
        
        investigation_charges = await billing_crud.add_investigation_charges(
            db=db_session,
            visit_id=visit.visit_id,
            ipd_id=None,
            investigations=investigations,
            created_by="test_user"
        )
        
        # Add manual charges
        manual_charges_data = [
            {"name": f"Manual Charge {i}", "rate": 200 + (i * 100), "quantity": 1}
            for i in range(num_manual_charges)
        ]
        
        manual_charges = await billing_crud.add_manual_charges(
            db=db_session,
            visit_id=visit.visit_id,
            ipd_id=None,
            manual_charges=manual_charges_data,
            created_by="admin_user"
        )
        
        # CRITICAL PROPERTY: All investigation charges must be linked to visit
        for charge in investigation_charges:
            assert charge.visit_id == visit.visit_id, (
                f"Investigation charge {charge.charge_id} must be linked to visit {visit.visit_id}"
            )
            assert charge.charge_type == ChargeType.INVESTIGATION, (
                f"Charge {charge.charge_id} must be of type INVESTIGATION"
            )
        
        # CRITICAL PROPERTY: All manual charges must be linked to visit
        for charge in manual_charges:
            assert charge.visit_id == visit.visit_id, (
                f"Manual charge {charge.charge_id} must be linked to visit {visit.visit_id}"
            )
            assert charge.charge_type == ChargeType.MANUAL, (
                f"Charge {charge.charge_id} must be of type MANUAL"
            )
        
        # CRITICAL PROPERTY: All charges can be retrieved by visit_id
        all_visit_charges = await billing_crud.get_charges_by_visit(db_session, visit.visit_id)
        assert len(all_visit_charges) == num_investigation_charges + num_manual_charges, (
            f"Should retrieve all {num_investigation_charges + num_manual_charges} charges for visit"
        )
    
    @pytest.mark.asyncio
    async def test_charge_without_visit_or_ipd_fails(self, db_session: AsyncSession):
        """
        Property: Charges cannot be created without either visit_id or ipd_id.
        
        **Validates: Requirements 2.4, 14.3**
        """
        # Attempt to create charge without visit_id or ipd_id
        with pytest.raises(ValueError, match="Either visit_id or ipd_id must be provided"):
            await billing_crud.create_charge(
                db=db_session,
                charge_type=ChargeType.INVESTIGATION,
                charge_name="Test Charge",
                rate=Decimal("100.00"),
                quantity=1,
                visit_id=None,
                ipd_id=None,
                created_by="test_user"
            )
    
    @pytest.mark.asyncio
    async def test_charge_with_invalid_visit_fails(self, db_session: AsyncSession):
        """
        Property: Charges cannot be created with invalid visit_id.
        
        **Validates: Requirements 2.4, 14.3**
        """
        # Attempt to create charge with non-existent visit_id
        with pytest.raises(ValueError, match="Visit not found"):
            await billing_crud.create_charge(
                db=db_session,
                charge_type=ChargeType.INVESTIGATION,
                charge_name="Test Charge",
                rate=Decimal("100.00"),
                quantity=1,
                visit_id="V20260101000000999",  # Non-existent visit
                created_by="test_user"
            )
    
    @given(
        num_charges=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_charges_retrievable_by_visit_property(
        self,
        db_session: AsyncSession,
        num_charges: int
    ):
        """
        Property: All charges linked to a visit should be retrievable 
        using the visit_id.
        
        **Validates: Requirements 2.4, 14.3**
        """
        # Create patient, doctor, and visit
        import time
        mobile = f"9{int(time.time() * 1000) % 1000000000:09d}"
        
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=mobile
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
        
        # Create charges
        created_charge_ids = []
        charge_types = [ChargeType.INVESTIGATION, ChargeType.PROCEDURE, ChargeType.SERVICE, ChargeType.MANUAL]
        
        for i in range(num_charges):
            charge = await billing_crud.create_charge(
                db=db_session,
                charge_type=charge_types[i % len(charge_types)],
                charge_name=f"Charge {i}",
                rate=Decimal(str(100 + (i * 25))),
                quantity=1,
                visit_id=visit.visit_id,
                created_by="test_user"
            )
            created_charge_ids.append(charge.charge_id)
        
        # CRITICAL PROPERTY: All charges should be retrievable by visit_id
        retrieved_charges = await billing_crud.get_charges_by_visit(db_session, visit.visit_id)
        retrieved_charge_ids = [charge.charge_id for charge in retrieved_charges]
        
        assert len(retrieved_charges) == num_charges, (
            f"Should retrieve all {num_charges} charges for visit {visit.visit_id}"
        )
        
        # CRITICAL PROPERTY: All created charges should be in retrieved charges
        for charge_id in created_charge_ids:
            assert charge_id in retrieved_charge_ids, (
                f"Charge {charge_id} should be retrievable by visit_id {visit.visit_id}"
            )
    
    @given(
        num_charges_per_type=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_charges_retrievable_by_type_property(
        self,
        db_session: AsyncSession,
        num_charges_per_type: int
    ):
        """
        Property: Charges should be retrievable by both visit_id and charge_type.
        
        **Validates: Requirements 2.4, 14.3**
        """
        # Create patient, doctor, and visit
        import time
        mobile = f"9{int(time.time() * 1000) % 1000000000:09d}"
        
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=mobile
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
        
        # Create charges of each type
        charge_types = [ChargeType.INVESTIGATION, ChargeType.PROCEDURE, ChargeType.SERVICE, ChargeType.MANUAL]
        
        for charge_type in charge_types:
            for i in range(num_charges_per_type):
                await billing_crud.create_charge(
                    db=db_session,
                    charge_type=charge_type,
                    charge_name=f"{charge_type.value} {i}",
                    rate=Decimal("100.00"),
                    quantity=1,
                    visit_id=visit.visit_id,
                    created_by="test_user"
                )
        
        # CRITICAL PROPERTY: Charges should be retrievable by type
        for charge_type in charge_types:
            type_charges = await billing_crud.get_charges_by_type(
                db=db_session,
                visit_id=visit.visit_id,
                ipd_id=None,
                charge_type=charge_type
            )
            
            assert len(type_charges) == num_charges_per_type, (
                f"Should retrieve {num_charges_per_type} charges of type {charge_type.value}"
            )
            
            # CRITICAL PROPERTY: All retrieved charges should be of correct type
            for charge in type_charges:
                assert charge.charge_type == charge_type, (
                    f"Charge {charge.charge_id} should be of type {charge_type.value}"
                )
                assert charge.visit_id == visit.visit_id, (
                    f"Charge {charge.charge_id} should be linked to visit {visit.visit_id}"
                )


class TestDataLinkageIntegrityExamples:
    """Unit tests for specific data linkage scenarios"""
    
    @pytest.mark.asyncio
    async def test_investigation_charge_linked_to_visit(self, db_session: AsyncSession):
        """Test that investigation charges are properly linked to visits"""
        # Create patient, doctor, and visit
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
        
        # Create investigation charge
        charge = await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="X-Ray",
            rate=Decimal("500.00"),
            quantity=1,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
        
        # Verify linkage
        assert charge.visit_id == visit.visit_id
        assert charge.ipd_id is None
        
        # Verify charge is retrievable by visit
        visit_charges = await billing_crud.get_charges_by_visit(db_session, visit.visit_id)
        assert len(visit_charges) == 1
        assert visit_charges[0].charge_id == charge.charge_id
    
    @pytest.mark.asyncio
    async def test_manual_charge_linked_to_visit(self, db_session: AsyncSession):
        """Test that manual charges are properly linked to visits"""
        # Create patient, doctor, and visit
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543211"
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
        
        # Create manual charge
        charge = await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.MANUAL,
            charge_name="Custom Service",
            rate=Decimal("1000.00"),
            quantity=1,
            visit_id=visit.visit_id,
            created_by="admin_user"
        )
        
        # Verify linkage
        assert charge.visit_id == visit.visit_id
        assert charge.charge_type == ChargeType.MANUAL
        
        # Verify charge is retrievable by visit
        visit_charges = await billing_crud.get_charges_by_visit(db_session, visit.visit_id)
        assert len(visit_charges) == 1
        assert visit_charges[0].charge_id == charge.charge_id
    
    @pytest.mark.asyncio
    async def test_multiple_charge_types_linked_to_same_visit(self, db_session: AsyncSession):
        """Test that multiple charge types can be linked to the same visit"""
        # Create patient, doctor, and visit
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543212"
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
        
        # Create different charge types
        investigation_charge = await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="Blood Test",
            rate=Decimal("300.00"),
            quantity=1,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
        
        procedure_charge = await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.PROCEDURE,
            charge_name="Dressing",
            rate=Decimal("200.00"),
            quantity=1,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
        
        manual_charge = await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.MANUAL,
            charge_name="Special Service",
            rate=Decimal("500.00"),
            quantity=1,
            visit_id=visit.visit_id,
            created_by="admin_user"
        )
        
        # Verify all charges are linked to the same visit
        visit_charges = await billing_crud.get_charges_by_visit(db_session, visit.visit_id)
        assert len(visit_charges) == 3
        
        charge_ids = {charge.charge_id for charge in visit_charges}
        assert investigation_charge.charge_id in charge_ids
        assert procedure_charge.charge_id in charge_ids
        assert manual_charge.charge_id in charge_ids
        
        # Verify all have correct visit_id
        for charge in visit_charges:
            assert charge.visit_id == visit.visit_id
