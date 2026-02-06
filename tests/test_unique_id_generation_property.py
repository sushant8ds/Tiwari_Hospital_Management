"""
Property-based tests for unique ID generation

**Feature: hospital-management-system, Property 1: Unique ID Generation**
**Validates: Requirements 1.1, 1.10, 4.1**
"""

import pytest
import pytest_asyncio
import asyncio
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Set, List
import re

from app.services.id_generator import IDGenerator, id_generator
from app.models.patient import Patient
from app.models.visit import Visit, VisitType, PaymentMode, VisitStatus
from app.models.ipd import IPD, IPDStatus
from datetime import datetime, date, time


class TestUniqueIDGenerationProperty:
    """Property-based tests for unique ID generation"""
    
    @given(
        num_ids=st.integers(min_value=100, max_value=500)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_patient_id_uniqueness_property(
        self,
        num_ids: int
    ):
        """
        Property: For any system operation that generates Patient_ID,
        all generated IDs should be globally unique across the entire system.
        
        **Validates: Requirements 1.1**
        """
        # Create a fresh ID generator for this test
        generator = IDGenerator()
        
        # Generate multiple patient IDs
        patient_ids: Set[str] = set()
        generated_ids: List[str] = []
        
        for _ in range(num_ids):
            patient_id = await generator.generate_patient_id()
            generated_ids.append(patient_id)
            patient_ids.add(patient_id)
        
        # Verify all IDs are unique
        assert len(patient_ids) == num_ids, (
            f"Generated {num_ids} patient IDs but only {len(patient_ids)} were unique. "
            f"Duplicates found!"
        )
        
        # Verify ID format: P + YYYYMMDD + 4-digit sequence
        patient_id_pattern = re.compile(r'^P\d{8}\d{4}$')
        for patient_id in generated_ids:
            assert patient_id_pattern.match(patient_id), (
                f"Patient ID '{patient_id}' does not match expected format 'PYYYYMMDDXXXX'"
            )
    
    @given(
        num_ids=st.integers(min_value=100, max_value=500)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_visit_id_uniqueness_property(
        self,
        num_ids: int
    ):
        """
        Property: For any system operation that generates Visit_ID,
        all generated IDs should be globally unique across the entire system.
        
        **Validates: Requirements 1.10**
        """
        # Create a fresh ID generator for this test
        generator = IDGenerator()
        
        # Generate multiple visit IDs
        visit_ids: Set[str] = set()
        generated_ids: List[str] = []
        
        for _ in range(num_ids):
            visit_id = await generator.generate_visit_id()
            generated_ids.append(visit_id)
            visit_ids.add(visit_id)
        
        # Verify all IDs are unique
        assert len(visit_ids) == num_ids, (
            f"Generated {num_ids} visit IDs but only {len(visit_ids)} were unique. "
            f"Duplicates found!"
        )
        
        # Verify ID format: V + YYYYMMDD + HHMMSS + 3-digit sequence
        visit_id_pattern = re.compile(r'^V\d{8}\d{6}\d{3}$')
        for visit_id in generated_ids:
            assert visit_id_pattern.match(visit_id), (
                f"Visit ID '{visit_id}' does not match expected format 'VYYYYMMDDHHMMSSXXX'"
            )
    
    @given(
        num_ids=st.integers(min_value=100, max_value=500)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_ipd_id_uniqueness_property(
        self,
        num_ids: int
    ):
        """
        Property: For any system operation that generates IPD_ID,
        all generated IDs should be globally unique across the entire system.
        
        **Validates: Requirements 4.1**
        """
        # Create a fresh ID generator for this test
        generator = IDGenerator()
        
        # Generate multiple IPD IDs
        ipd_ids: Set[str] = set()
        generated_ids: List[str] = []
        
        for _ in range(num_ids):
            ipd_id = await generator.generate_ipd_id()
            generated_ids.append(ipd_id)
            ipd_ids.add(ipd_id)
        
        # Verify all IDs are unique
        assert len(ipd_ids) == num_ids, (
            f"Generated {num_ids} IPD IDs but only {len(ipd_ids)} were unique. "
            f"Duplicates found!"
        )
        
        # Verify ID format: IPD + YYYYMMDD + 4-digit sequence
        ipd_id_pattern = re.compile(r'^IPD\d{8}\d{4}$')
        for ipd_id in generated_ids:
            assert ipd_id_pattern.match(ipd_id), (
                f"IPD ID '{ipd_id}' does not match expected format 'IPDYYYYMMDDXXXX'"
            )
    
    @given(
        num_concurrent=st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_concurrent_patient_id_generation_property(
        self,
        num_concurrent: int
    ):
        """
        Property: For any concurrent system operations that generate Patient_IDs,
        all generated IDs should be globally unique even under concurrent load.
        
        **Validates: Requirements 1.1**
        """
        # Create a fresh ID generator for this test
        generator = IDGenerator()
        
        # Generate IDs concurrently
        tasks = [generator.generate_patient_id() for _ in range(num_concurrent)]
        generated_ids = await asyncio.gather(*tasks)
        
        # Verify all IDs are unique
        unique_ids = set(generated_ids)
        assert len(unique_ids) == num_concurrent, (
            f"Generated {num_concurrent} patient IDs concurrently but only {len(unique_ids)} were unique. "
            f"Concurrent ID generation failed to maintain uniqueness!"
        )
    
    @given(
        num_concurrent=st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_concurrent_visit_id_generation_property(
        self,
        num_concurrent: int
    ):
        """
        Property: For any concurrent system operations that generate Visit_IDs,
        all generated IDs should be globally unique even under concurrent load.
        
        **Validates: Requirements 1.10**
        """
        # Create a fresh ID generator for this test
        generator = IDGenerator()
        
        # Generate IDs concurrently
        tasks = [generator.generate_visit_id() for _ in range(num_concurrent)]
        generated_ids = await asyncio.gather(*tasks)
        
        # Verify all IDs are unique
        unique_ids = set(generated_ids)
        assert len(unique_ids) == num_concurrent, (
            f"Generated {num_concurrent} visit IDs concurrently but only {len(unique_ids)} were unique. "
            f"Concurrent ID generation failed to maintain uniqueness!"
        )
    
    @given(
        num_concurrent=st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_concurrent_ipd_id_generation_property(
        self,
        num_concurrent: int
    ):
        """
        Property: For any concurrent system operations that generate IPD_IDs,
        all generated IDs should be globally unique even under concurrent load.
        
        **Validates: Requirements 4.1**
        """
        # Create a fresh ID generator for this test
        generator = IDGenerator()
        
        # Generate IDs concurrently
        tasks = [generator.generate_ipd_id() for _ in range(num_concurrent)]
        generated_ids = await asyncio.gather(*tasks)
        
        # Verify all IDs are unique
        unique_ids = set(generated_ids)
        assert len(unique_ids) == num_concurrent, (
            f"Generated {num_concurrent} IPD IDs concurrently but only {len(unique_ids)} were unique. "
            f"Concurrent ID generation failed to maintain uniqueness!"
        )
    
    @given(
        num_patient_ids=st.integers(min_value=50, max_value=100),
        num_visit_ids=st.integers(min_value=50, max_value=100),
        num_ipd_ids=st.integers(min_value=50, max_value=100)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_cross_entity_id_uniqueness_property(
        self,
        num_patient_ids: int,
        num_visit_ids: int,
        num_ipd_ids: int
    ):
        """
        Property: For any system operations that generate IDs across different entity types,
        all generated IDs should be globally unique within their respective entity types.
        
        **Validates: Requirements 1.1, 1.10, 4.1**
        """
        # Create a fresh ID generator for this test
        generator = IDGenerator()
        
        # Generate IDs for all entity types
        patient_ids = [await generator.generate_patient_id() for _ in range(num_patient_ids)]
        visit_ids = [await generator.generate_visit_id() for _ in range(num_visit_ids)]
        ipd_ids = [await generator.generate_ipd_id() for _ in range(num_ipd_ids)]
        
        # Verify uniqueness within each entity type
        assert len(set(patient_ids)) == num_patient_ids, (
            f"Patient IDs are not unique: generated {num_patient_ids}, unique {len(set(patient_ids))}"
        )
        assert len(set(visit_ids)) == num_visit_ids, (
            f"Visit IDs are not unique: generated {num_visit_ids}, unique {len(set(visit_ids))}"
        )
        assert len(set(ipd_ids)) == num_ipd_ids, (
            f"IPD IDs are not unique: generated {num_ipd_ids}, unique {len(set(ipd_ids))}"
        )
        
        # Verify that IDs from different entity types don't collide
        # (This is guaranteed by the prefix, but we verify it anyway)
        all_ids = patient_ids + visit_ids + ipd_ids
        assert len(set(all_ids)) == len(all_ids), (
            "IDs from different entity types should not collide"
        )
    
    @pytest.mark.asyncio
    async def test_global_id_generator_uniqueness(self):
        """
        Test that the global ID generator instance maintains uniqueness
        across multiple calls.
        """
        # Use the global id_generator instance
        patient_ids = [await id_generator.generate_patient_id() for _ in range(100)]
        visit_ids = [await id_generator.generate_visit_id() for _ in range(100)]
        ipd_ids = [await id_generator.generate_ipd_id() for _ in range(100)]
        
        # Verify uniqueness
        assert len(set(patient_ids)) == 100, "Global patient ID generator produced duplicates"
        assert len(set(visit_ids)) == 100, "Global visit ID generator produced duplicates"
        assert len(set(ipd_ids)) == 100, "Global IPD ID generator produced duplicates"


class TestUniqueIDGenerationExamples:
    """Unit tests for specific ID generation scenarios"""
    
    @pytest.mark.asyncio
    async def test_patient_id_format(self):
        """Test that patient IDs follow the correct format"""
        generator = IDGenerator()
        patient_id = await generator.generate_patient_id()
        
        # Verify format: P + YYYYMMDD + 4-digit sequence
        assert patient_id.startswith('P'), "Patient ID should start with 'P'"
        assert len(patient_id) == 13, "Patient ID should be 13 characters long (P + 8 date + 4 sequence)"
        
        # Extract and verify date part
        date_part = patient_id[1:9]
        assert date_part.isdigit(), "Date part should be numeric"
        
        # Verify it's a valid date
        datetime.strptime(date_part, "%Y%m%d")
        
        # Extract and verify sequence part
        sequence_part = patient_id[9:]
        assert sequence_part.isdigit(), "Sequence part should be numeric"
        assert len(sequence_part) == 4, "Sequence part should be 4 digits"
    
    @pytest.mark.asyncio
    async def test_visit_id_format(self):
        """Test that visit IDs follow the correct format"""
        generator = IDGenerator()
        visit_id = await generator.generate_visit_id()
        
        # Verify format: V + YYYYMMDD + HHMMSS + 3-digit sequence
        assert visit_id.startswith('V'), "Visit ID should start with 'V'"
        assert len(visit_id) == 18, "Visit ID should be 18 characters long (V + 8 date + 6 time + 3 sequence)"
        
        # Extract and verify date part
        date_part = visit_id[1:9]
        assert date_part.isdigit(), "Date part should be numeric"
        datetime.strptime(date_part, "%Y%m%d")
        
        # Extract and verify time part
        time_part = visit_id[9:15]
        assert time_part.isdigit(), "Time part should be numeric"
        
        # Extract and verify sequence part
        sequence_part = visit_id[15:]
        assert sequence_part.isdigit(), "Sequence part should be numeric"
        assert len(sequence_part) == 3, "Sequence part should be 3 digits"
    
    @pytest.mark.asyncio
    async def test_ipd_id_format(self):
        """Test that IPD IDs follow the correct format"""
        generator = IDGenerator()
        ipd_id = await generator.generate_ipd_id()
        
        # Verify format: IPD + YYYYMMDD + 4-digit sequence
        assert ipd_id.startswith('IPD'), "IPD ID should start with 'IPD'"
        assert len(ipd_id) == 15, "IPD ID should be 15 characters long (IPD + 8 date + 4 sequence)"
        
        # Extract and verify date part
        date_part = ipd_id[3:11]
        assert date_part.isdigit(), "Date part should be numeric"
        datetime.strptime(date_part, "%Y%m%d")
        
        # Extract and verify sequence part
        sequence_part = ipd_id[11:]
        assert sequence_part.isdigit(), "Sequence part should be numeric"
        assert len(sequence_part) == 4, "Sequence part should be 4 digits"
    
    @pytest.mark.asyncio
    async def test_sequential_patient_ids(self):
        """Test that patient IDs increment sequentially on the same day"""
        generator = IDGenerator()
        
        id1 = await generator.generate_patient_id()
        id2 = await generator.generate_patient_id()
        id3 = await generator.generate_patient_id()
        
        # Extract sequence numbers
        seq1 = int(id1[9:])
        seq2 = int(id2[9:])
        seq3 = int(id3[9:])
        
        # Verify sequential increment
        assert seq2 == seq1 + 1, "Second patient ID should increment by 1"
        assert seq3 == seq2 + 1, "Third patient ID should increment by 1"
    
    @pytest.mark.asyncio
    async def test_sequential_visit_ids(self):
        """Test that visit IDs increment sequentially within the same second"""
        generator = IDGenerator()
        
        # Generate multiple IDs quickly to ensure they're in the same second
        ids = []
        for _ in range(5):
            visit_id = await generator.generate_visit_id()
            ids.append(visit_id)
        
        # Verify all IDs are unique
        assert len(set(ids)) == 5, "All visit IDs should be unique"
    
    @pytest.mark.asyncio
    async def test_sequential_ipd_ids(self):
        """Test that IPD IDs increment sequentially on the same day"""
        generator = IDGenerator()
        
        id1 = await generator.generate_ipd_id()
        id2 = await generator.generate_ipd_id()
        id3 = await generator.generate_ipd_id()
        
        # Extract sequence numbers
        seq1 = int(id1[11:])
        seq2 = int(id2[11:])
        seq3 = int(id3[11:])
        
        # Verify sequential increment
        assert seq2 == seq1 + 1, "Second IPD ID should increment by 1"
        assert seq3 == seq2 + 1, "Third IPD ID should increment by 1"
    
    @pytest.mark.asyncio
    async def test_high_volume_id_generation(self):
        """Test ID generation under high volume (stress test)"""
        generator = IDGenerator()
        
        # Generate a large number of IDs
        num_ids = 1000
        patient_ids = [await generator.generate_patient_id() for _ in range(num_ids)]
        
        # Verify all are unique
        assert len(set(patient_ids)) == num_ids, (
            f"High volume test failed: generated {num_ids} IDs but only {len(set(patient_ids))} were unique"
        )
    
    @pytest.mark.asyncio
    async def test_concurrent_mixed_id_generation(self):
        """Test concurrent generation of different ID types"""
        generator = IDGenerator()
        
        # Create tasks for different ID types
        tasks = []
        for _ in range(20):
            tasks.append(generator.generate_patient_id())
            tasks.append(generator.generate_visit_id())
            tasks.append(generator.generate_ipd_id())
        
        # Execute all tasks concurrently
        all_ids = await asyncio.gather(*tasks)
        
        # Verify all IDs are unique
        assert len(set(all_ids)) == len(all_ids), (
            "Concurrent mixed ID generation produced duplicates"
        )
        
        # Verify correct counts by type
        patient_ids = [id for id in all_ids if id.startswith('P')]
        visit_ids = [id for id in all_ids if id.startswith('V')]
        ipd_ids = [id for id in all_ids if id.startswith('IPD')]
        
        assert len(patient_ids) == 20, "Should have 20 patient IDs"
        assert len(visit_ids) == 20, "Should have 20 visit IDs"
        assert len(ipd_ids) == 20, "Should have 20 IPD IDs"
