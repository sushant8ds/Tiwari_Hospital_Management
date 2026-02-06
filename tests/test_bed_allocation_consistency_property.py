"""
Property-based tests for bed allocation consistency

**Feature: hospital-management-system, Property 13: Bed Allocation Consistency**
**Validates: Requirements 4.3, 4.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from decimal import Decimal
from datetime import datetime, timedelta

from app.models.patient import Patient, Gender
from app.models.bed import Bed, WardType, BedStatus
from app.models.ipd import IPD, IPDStatus
from app.crud.patient import patient_crud
from app.crud.ipd import ipd_crud, bed_crud


class TestBedAllocationConsistencyProperty:
    """Property-based tests for bed allocation consistency"""
    
    @given(
        num_admissions=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_bed_status_updated_on_admission_property(
        self,
        db_session: AsyncSession,
        num_admissions: int
    ):
        """
        Property: For any IPD admission, the allocated bed should be marked as occupied.
        
        **Validates: Requirements 4.3, 4.4**
        """
        import time
        base_timestamp = int(time.time() * 1000000)
        
        for i in range(num_admissions):
            # Create patient
            mobile = f"9{(base_timestamp + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Test Patient {i}",
                age=30,
                gender=Gender.MALE,
                address="Test Address",
                mobile_number=mobile
            )
            
            # Create bed with unique number using timestamp
            bed = await bed_crud.create_bed(
                db=db_session,
                bed_number=f"TEST{base_timestamp + i}",
                ward_type=WardType.GENERAL,
                per_day_charge=Decimal("500.00")
            )
            
            # CRITICAL PROPERTY 1: Bed should be available before admission
            assert bed.status == BedStatus.AVAILABLE, (
                f"Bed {bed.bed_number} should be available before admission"
            )
            
            # Admit patient
            ipd = await ipd_crud.admit_patient(
                db=db_session,
                patient_id=patient.patient_id,
                bed_id=bed.bed_id,
                file_charge=Decimal("1000.00")
            )
            
            # CRITICAL PROPERTY 2: Bed should be occupied after admission
            updated_bed = await bed_crud.get_bed_by_id(db_session, bed.bed_id)
            assert updated_bed.status == BedStatus.OCCUPIED, (
                f"Bed {bed.bed_number} should be occupied after admission"
            )
            
            # CRITICAL PROPERTY 3: IPD should reference the correct bed
            assert ipd.bed_id == bed.bed_id, (
                f"IPD {ipd.ipd_id} should reference bed {bed.bed_id}"
            )
    
    @given(
        num_bed_changes=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_bed_status_updated_on_bed_change_property(
        self,
        db_session: AsyncSession,
        num_bed_changes: int
    ):
        """
        Property: When changing beds, the old bed should become available 
        and the new bed should become occupied.
        
        **Validates: Requirements 4.3, 4.4**
        """
        import time
        base_timestamp = int(time.time() * 1000000)
        
        # Create patient
        mobile = f"9{base_timestamp % 1000000000:09d}"
        
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=mobile
        )
        
        # Create initial bed with unique number
        current_bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"INIT{base_timestamp}",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        # Admit patient
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=current_bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Perform bed changes
        for i in range(num_bed_changes):
            # Create new bed with unique number
            new_bed = await bed_crud.create_bed(
                db=db_session,
                bed_number=f"CHG{base_timestamp + i + 1}",
                ward_type=WardType.GENERAL,
                per_day_charge=Decimal("500.00")
            )
            
            # Store old bed ID
            old_bed_id = ipd.bed_id
            
            # Change bed
            ipd = await ipd_crud.change_bed(
                db=db_session,
                ipd_id=ipd.ipd_id,
                new_bed_id=new_bed.bed_id
            )
            
            # CRITICAL PROPERTY 1: Old bed should be available
            old_bed = await bed_crud.get_bed_by_id(db_session, old_bed_id)
            assert old_bed.status == BedStatus.AVAILABLE, (
                f"Old bed {old_bed.bed_number} should be available after bed change"
            )
            
            # CRITICAL PROPERTY 2: New bed should be occupied
            updated_new_bed = await bed_crud.get_bed_by_id(db_session, new_bed.bed_id)
            assert updated_new_bed.status == BedStatus.OCCUPIED, (
                f"New bed {new_bed.bed_number} should be occupied after bed change"
            )
            
            # CRITICAL PROPERTY 3: IPD should reference new bed
            assert ipd.bed_id == new_bed.bed_id, (
                f"IPD {ipd.ipd_id} should reference new bed {new_bed.bed_id}"
            )
    
    @given(
        num_patients=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_bed_status_updated_on_discharge_property(
        self,
        db_session: AsyncSession,
        num_patients: int
    ):
        """
        Property: When a patient is discharged, the bed should become available.
        
        **Validates: Requirements 4.3, 4.4**
        """
        import time
        base_timestamp = int(time.time() * 1000000)
        
        for i in range(num_patients):
            # Create patient
            mobile = f"9{(base_timestamp + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Test Patient {i}",
                age=30,
                gender=Gender.MALE,
                address="Test Address",
                mobile_number=mobile
            )
            
            # Create bed with unique number
            bed = await bed_crud.create_bed(
                db=db_session,
                bed_number=f"DISCH{base_timestamp + i}",
                ward_type=WardType.GENERAL,
                per_day_charge=Decimal("500.00")
            )
            
            # Admit patient
            ipd = await ipd_crud.admit_patient(
                db=db_session,
                patient_id=patient.patient_id,
                bed_id=bed.bed_id,
                file_charge=Decimal("1000.00")
            )
            
            # Verify bed is occupied
            occupied_bed = await bed_crud.get_bed_by_id(db_session, bed.bed_id)
            assert occupied_bed.status == BedStatus.OCCUPIED
            
            # Discharge patient
            discharged_ipd = await ipd_crud.discharge_patient(
                db=db_session,
                ipd_id=ipd.ipd_id
            )
            
            # CRITICAL PROPERTY 1: Bed should be available after discharge
            available_bed = await bed_crud.get_bed_by_id(db_session, bed.bed_id)
            assert available_bed.status == BedStatus.AVAILABLE, (
                f"Bed {bed.bed_number} should be available after discharge"
            )
            
            # CRITICAL PROPERTY 2: IPD status should be discharged
            assert discharged_ipd.status == IPDStatus.DISCHARGED, (
                f"IPD {ipd.ipd_id} should be discharged"
            )
    
    @given(
        num_beds=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_cannot_admit_to_occupied_bed_property(
        self,
        db_session: AsyncSession,
        num_beds: int
    ):
        """
        Property: Cannot admit a patient to an occupied bed.
        
        **Validates: Requirements 4.3, 4.4**
        """
        import time
        base_timestamp = int(time.time() * 1000000)
        
        # Create beds with unique numbers
        beds = []
        for i in range(num_beds):
            bed = await bed_crud.create_bed(
                db=db_session,
                bed_number=f"OCC{base_timestamp + i}",
                ward_type=WardType.GENERAL,
                per_day_charge=Decimal("500.00")
            )
            beds.append(bed)
        
        # Admit patients to all beds
        for i, bed in enumerate(beds):
            mobile = f"9{(base_timestamp + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Test Patient {i}",
                age=30,
                gender=Gender.MALE,
                address="Test Address",
                mobile_number=mobile
            )
            
            await ipd_crud.admit_patient(
                db=db_session,
                patient_id=patient.patient_id,
                bed_id=bed.bed_id,
                file_charge=Decimal("1000.00")
            )
        
        # Try to admit another patient to an occupied bed
        mobile = f"9{(base_timestamp + num_beds) % 1000000000:09d}"
        
        new_patient = await patient_crud.create_patient(
            db=db_session,
            name="New Patient",
            age=25,
            gender=Gender.FEMALE,
            address="Test Address",
            mobile_number=mobile
        )
        
        # CRITICAL PROPERTY: Should fail to admit to occupied bed
        with pytest.raises(ValueError, match="not available"):
            await ipd_crud.admit_patient(
                db=db_session,
                patient_id=new_patient.patient_id,
                bed_id=beds[0].bed_id,  # Try first bed which is occupied
                file_charge=Decimal("1000.00")
            )
    
    @given(
        num_admissions=st.integers(min_value=5, max_value=15)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_bed_occupancy_stats_consistency_property(
        self,
        db_session: AsyncSession,
        num_admissions: int
    ):
        """
        Property: Bed occupancy statistics should accurately reflect 
        the number of occupied and available beds.
        
        **Validates: Requirements 4.3, 4.4**
        """
        import time
        base_timestamp = int(time.time() * 1000000)
        
        # Create beds (more than admissions) with unique numbers
        total_beds = num_admissions + 5
        beds = []
        for i in range(total_beds):
            bed = await bed_crud.create_bed(
                db=db_session,
                bed_number=f"STAT{base_timestamp + i}",
                ward_type=WardType.GENERAL,
                per_day_charge=Decimal("500.00")
            )
            beds.append(bed)
        
        # Admit patients to some beds
        for i in range(num_admissions):
            mobile = f"9{(base_timestamp + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Test Patient {i}",
                age=30,
                gender=Gender.MALE,
                address="Test Address",
                mobile_number=mobile
            )
            
            await ipd_crud.admit_patient(
                db=db_session,
                patient_id=patient.patient_id,
                bed_id=beds[i].bed_id,
                file_charge=Decimal("1000.00")
            )
        
        # Get occupancy stats
        stats = await bed_crud.get_bed_occupancy_stats(db_session)
        
        # CRITICAL PROPERTY 1: Total beds should match
        assert stats["total_beds"] >= total_beds, (
            f"Total beds {stats['total_beds']} should be at least {total_beds}"
        )
        
        # CRITICAL PROPERTY 2: Occupied beds should match admissions
        assert stats["occupied"] >= num_admissions, (
            f"Occupied beds {stats['occupied']} should be at least {num_admissions}"
        )
        
        # CRITICAL PROPERTY 3: Available beds should be total - occupied
        expected_available = stats["total_beds"] - stats["occupied"]
        assert stats["available"] == expected_available, (
            f"Available beds {stats['available']} should equal "
            f"total {stats['total_beds']} - occupied {stats['occupied']} = {expected_available}"
        )
        
        # CRITICAL PROPERTY 4: Occupancy rate should be correct
        expected_rate = round((stats["occupied"] / stats["total_beds"] * 100), 2)
        assert stats["occupancy_rate"] == expected_rate, (
            f"Occupancy rate {stats['occupancy_rate']} should equal {expected_rate}"
        )


class TestBedAllocationConsistencyExamples:
    """Unit tests for specific bed allocation scenarios"""
    
    @pytest.mark.asyncio
    async def test_bed_marked_occupied_on_admission(self, db_session: AsyncSession):
        """Test that bed is marked occupied when patient is admitted"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543210"
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="TEST001",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        # Verify bed is available
        assert bed.status == BedStatus.AVAILABLE
        
        # Admit patient
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Verify bed is now occupied
        updated_bed = await bed_crud.get_bed_by_id(db_session, bed.bed_id)
        assert updated_bed.status == BedStatus.OCCUPIED
        assert ipd.bed_id == bed.bed_id
    
    @pytest.mark.asyncio
    async def test_bed_marked_available_on_discharge(self, db_session: AsyncSession):
        """Test that bed is marked available when patient is discharged"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543211"
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="TEST002",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        # Admit patient
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Verify bed is occupied
        occupied_bed = await bed_crud.get_bed_by_id(db_session, bed.bed_id)
        assert occupied_bed.status == BedStatus.OCCUPIED
        
        # Discharge patient
        await ipd_crud.discharge_patient(db_session, ipd.ipd_id)
        
        # Verify bed is now available
        available_bed = await bed_crud.get_bed_by_id(db_session, bed.bed_id)
        assert available_bed.status == BedStatus.AVAILABLE
    
    @pytest.mark.asyncio
    async def test_bed_change_updates_both_beds(self, db_session: AsyncSession):
        """Test that bed change updates both old and new bed statuses"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543212"
        )
        
        # Create two beds
        bed1 = await bed_crud.create_bed(
            db=db_session,
            bed_number="TEST003",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        bed2 = await bed_crud.create_bed(
            db=db_session,
            bed_number="TEST004",
            ward_type=WardType.PRIVATE,
            per_day_charge=Decimal("1500.00")
        )
        
        # Admit patient to first bed
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed1.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Change to second bed
        await ipd_crud.change_bed(db_session, ipd.ipd_id, bed2.bed_id)
        
        # Verify first bed is available
        bed1_updated = await bed_crud.get_bed_by_id(db_session, bed1.bed_id)
        assert bed1_updated.status == BedStatus.AVAILABLE
        
        # Verify second bed is occupied
        bed2_updated = await bed_crud.get_bed_by_id(db_session, bed2.bed_id)
        assert bed2_updated.status == BedStatus.OCCUPIED
    
    @pytest.mark.asyncio
    async def test_cannot_admit_to_occupied_bed(self, db_session: AsyncSession):
        """Test that cannot admit patient to an occupied bed"""
        # Create two patients
        patient1 = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient 1",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543213"
        )
        
        patient2 = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient 2",
            age=25,
            gender=Gender.FEMALE,
            address="Test Address",
            mobile_number="9876543214"
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="TEST005",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        # Admit first patient
        await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient1.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Try to admit second patient to same bed - should fail
        with pytest.raises(ValueError, match="not available"):
            await ipd_crud.admit_patient(
                db=db_session,
                patient_id=patient2.patient_id,
                bed_id=bed.bed_id,
                file_charge=Decimal("1000.00")
            )
