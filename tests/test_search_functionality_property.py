"""
Property-based tests for search functionality

**Feature: hospital-management-system, Property 10: Search Functionality Completeness**
**Validates: Requirements 1.7, 13.1**
"""

import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Set

from app.models.patient import Patient, Gender
from app.crud.patient import patient_crud


# Strategy for generating valid patient data
@st.composite
def patient_data_strategy(draw):
    """Generate valid patient data for testing"""
    return {
        "name": draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        "age": draw(st.integers(min_value=0, max_value=150)),
        "gender": draw(st.sampled_from([Gender.MALE, Gender.FEMALE, Gender.OTHER])),
        "address": draw(st.text(min_size=1, max_size=500).filter(lambda x: x.strip())),
        "mobile_number": draw(st.from_regex(r'^[6-9]\d{9}$', fullmatch=True))
    }


class TestSearchFunctionalityProperty:
    """Property-based tests for patient search functionality"""
    
    @given(
        num_patients=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_search_by_patient_id_property(
        self,
        db_session: AsyncSession,
        num_patients: int
    ):
        """
        Property: For any patient search operation by Patient_ID,
        the system should return the correct patient when searching by their exact ID.
        
        **Validates: Requirements 1.7, 13.1**
        """
        # Create multiple patients
        created_patients = []
        import time
        import random
        base_number = int(f"9{int(time.time() * 1000) % 100000000:08d}"[-9:] + f"{random.randint(10, 99):02d}")
        
        for i in range(num_patients):
            unique_mobile = str(base_number + i)
            if len(unique_mobile) != 10:
                unique_mobile = f"9{(base_number + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=30 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=unique_mobile
            )
            created_patients.append(patient)
        
        # Test search by each patient's ID
        for patient in created_patients:
            # Search by exact patient ID
            results = await patient_crud.search_patients(db_session, patient.patient_id)
            
            # Verify the correct patient is returned
            assert len(results) >= 1, (
                f"Search by patient ID '{patient.patient_id}' should return at least one result"
            )
            
            # Verify the searched patient is in the results
            found_patient_ids = [p.patient_id for p in results]
            assert patient.patient_id in found_patient_ids, (
                f"Search by patient ID '{patient.patient_id}' should return that patient"
            )
    
    @given(
        num_patients=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_search_by_mobile_number_property(
        self,
        db_session: AsyncSession,
        num_patients: int
    ):
        """
        Property: For any patient search operation by Mobile_Number,
        the system should return the correct patient when searching by their mobile number.
        
        **Validates: Requirements 1.7, 13.1**
        """
        # Create multiple patients
        created_patients = []
        import time
        import random
        base_number = int(f"9{int(time.time() * 1000) % 100000000:08d}"[-9:] + f"{random.randint(10, 99):02d}")
        
        for i in range(num_patients):
            unique_mobile = str(base_number + i)
            if len(unique_mobile) != 10:
                unique_mobile = f"9{(base_number + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=30 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=unique_mobile
            )
            created_patients.append(patient)
        
        # Test search by each patient's mobile number
        for patient in created_patients:
            # Search by exact mobile number
            results = await patient_crud.search_patients(db_session, patient.mobile_number)
            
            # Verify the correct patient is returned
            assert len(results) >= 1, (
                f"Search by mobile number '{patient.mobile_number}' should return at least one result"
            )
            
            # Verify the searched patient is in the results
            found_mobiles = [p.mobile_number for p in results]
            assert patient.mobile_number in found_mobiles, (
                f"Search by mobile number '{patient.mobile_number}' should return that patient"
            )
    
    @given(
        num_patients=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_search_by_patient_name_property(
        self,
        db_session: AsyncSession,
        num_patients: int
    ):
        """
        Property: For any patient search operation by Patient_Name,
        the system should return the correct patient(s) when searching by their name.
        
        **Validates: Requirements 1.7, 13.1**
        """
        # Create multiple patients with unique names
        created_patients = []
        import time
        import random
        base_number = int(f"9{int(time.time() * 1000) % 100000000:08d}"[-9:] + f"{random.randint(10, 99):02d}")
        
        # Use unique name prefixes to ensure we can test name search
        unique_prefix = f"TestPatient{random.randint(10000, 99999)}"
        
        for i in range(num_patients):
            unique_mobile = str(base_number + i)
            if len(unique_mobile) != 10:
                unique_mobile = f"9{(base_number + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"{unique_prefix} {i}",
                age=30 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=unique_mobile
            )
            created_patients.append(patient)
        
        # Test search by each patient's name
        for patient in created_patients:
            # Search by exact name
            results = await patient_crud.search_patients(db_session, patient.name)
            
            # Verify the correct patient is returned
            assert len(results) >= 1, (
                f"Search by patient name '{patient.name}' should return at least one result"
            )
            
            # Verify the searched patient is in the results
            found_names = [p.name for p in results]
            assert patient.name in found_names, (
                f"Search by patient name '{patient.name}' should return that patient"
            )
    
    @given(
        num_patients=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_search_partial_name_property(
        self,
        db_session: AsyncSession,
        num_patients: int
    ):
        """
        Property: For any patient search operation with partial name,
        the system should return all patients whose names contain the search term.
        
        **Validates: Requirements 1.7, 13.1**
        """
        # Create multiple patients with a common name pattern
        # Use a highly unique prefix to avoid collisions with other test data
        created_patients = []
        import time
        import random
        import uuid
        base_number = int(f"9{int(time.time() * 1000) % 100000000:08d}"[-9:] + f"{random.randint(10, 99):02d}")
        
        # Use a UUID-based prefix to ensure uniqueness across test runs
        common_prefix = f"UniqueSmith{uuid.uuid4().hex[:8]}"
        
        for i in range(num_patients):
            unique_mobile = str(base_number + i)
            if len(unique_mobile) != 10:
                unique_mobile = f"9{(base_number + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"{common_prefix} Patient {i}",
                age=30 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=unique_mobile
            )
            created_patients.append(patient)
        
        # Search by the common prefix (case-insensitive)
        results = await patient_crud.search_patients(db_session, common_prefix)
        
        # Verify all created patients are in the results
        result_ids = {p.patient_id for p in results}
        
        for patient in created_patients:
            assert patient.patient_id in result_ids, (
                f"Patient '{patient.name}' with ID '{patient.patient_id}' should be in search results. "
                f"Searched for '{common_prefix}', found {len(result_ids)} results"
            )
    
    @given(
        num_patients=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_search_case_insensitive_property(
        self,
        db_session: AsyncSession,
        num_patients: int
    ):
        """
        Property: For any patient search operation,
        the search should be case-insensitive for patient names.
        
        **Validates: Requirements 1.7, 13.1**
        """
        # Create multiple patients
        created_patients = []
        import time
        import random
        import uuid
        base_number = int(f"9{int(time.time() * 1000) % 100000000:08d}"[-9:] + f"{random.randint(10, 99):02d}")
        
        # Use a UUID-based prefix to ensure uniqueness
        unique_prefix = f"UniqueCase{uuid.uuid4().hex[:8]}"
        
        for i in range(num_patients):
            unique_mobile = str(base_number + i)
            if len(unique_mobile) != 10:
                unique_mobile = f"9{(base_number + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"{unique_prefix} Patient {i}",
                age=30 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=unique_mobile
            )
            created_patients.append(patient)
        
        # Test case-insensitive search
        # Search with lowercase
        results_lower = await patient_crud.search_patients(db_session, unique_prefix.lower())
        
        # Search with uppercase
        results_upper = await patient_crud.search_patients(db_session, unique_prefix.upper())
        
        # Search with mixed case
        results_mixed = await patient_crud.search_patients(db_session, unique_prefix)
        
        # Verify the same patient IDs are returned regardless of case
        ids_lower = {p.patient_id for p in results_lower}
        ids_upper = {p.patient_id for p in results_upper}
        ids_mixed = {p.patient_id for p in results_mixed}
        
        # Verify all created patients are found with all case variations
        for patient in created_patients:
            assert patient.patient_id in ids_lower, (
                f"Patient '{patient.name}' (ID: {patient.patient_id}) should be found with lowercase search. "
                f"Searched for '{unique_prefix.lower()}', found {len(ids_lower)} results"
            )
            assert patient.patient_id in ids_upper, (
                f"Patient '{patient.name}' (ID: {patient.patient_id}) should be found with uppercase search. "
                f"Searched for '{unique_prefix.upper()}', found {len(ids_upper)} results"
            )
            assert patient.patient_id in ids_mixed, (
                f"Patient '{patient.name}' (ID: {patient.patient_id}) should be found with mixed case search. "
                f"Searched for '{unique_prefix}', found {len(ids_mixed)} results"
            )
    
    @given(
        num_patients=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_search_empty_term_returns_empty_property(
        self,
        db_session: AsyncSession,
        num_patients: int
    ):
        """
        Property: For any patient search operation with empty search term,
        the system should return an empty list.
        
        **Validates: Requirements 1.7, 13.1**
        """
        # Create multiple patients
        import time
        import random
        base_number = int(f"9{int(time.time() * 1000) % 100000000:08d}"[-9:] + f"{random.randint(10, 99):02d}")
        
        for i in range(num_patients):
            unique_mobile = str(base_number + i)
            if len(unique_mobile) != 10:
                unique_mobile = f"9{(base_number + i) % 1000000000:09d}"
            
            await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=30 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=unique_mobile
            )
        
        # Test search with empty string
        results_empty = await patient_crud.search_patients(db_session, "")
        assert len(results_empty) == 0, "Search with empty string should return empty list"
        
        # Test search with whitespace only
        results_whitespace = await patient_crud.search_patients(db_session, "   ")
        assert len(results_whitespace) == 0, "Search with whitespace should return empty list"
    
    @given(
        num_patients=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_search_nonexistent_returns_empty_property(
        self,
        db_session: AsyncSession,
        num_patients: int
    ):
        """
        Property: For any patient search operation with non-existent search term,
        the system should return an empty list.
        
        **Validates: Requirements 1.7, 13.1**
        """
        # Create multiple patients
        import time
        import random
        base_number = int(f"9{int(time.time() * 1000) % 100000000:08d}"[-9:] + f"{random.randint(10, 99):02d}")
        
        for i in range(num_patients):
            unique_mobile = str(base_number + i)
            if len(unique_mobile) != 10:
                unique_mobile = f"9{(base_number + i) % 1000000000:09d}"
            
            await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=30 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=unique_mobile
            )
        
        # Search for a non-existent patient
        nonexistent_search = f"NonExistent{random.randint(100000, 999999)}"
        results = await patient_crud.search_patients(db_session, nonexistent_search)
        
        assert len(results) == 0, (
            f"Search for non-existent term '{nonexistent_search}' should return empty list"
        )
    
    @given(
        num_patients=st.integers(min_value=10, max_value=30)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_search_all_criteria_property(
        self,
        db_session: AsyncSession,
        num_patients: int
    ):
        """
        Property: For any patient in the system,
        searching by their Patient_ID, Mobile_Number, or Patient_Name should all return that patient.
        
        **Validates: Requirements 1.7, 13.1**
        """
        # Create multiple patients
        created_patients = []
        import time
        import random
        import uuid
        base_number = int(f"9{int(time.time() * 1000) % 100000000:08d}"[-9:] + f"{random.randint(10, 99):02d}")
        
        # Use a UUID-based prefix to ensure uniqueness
        unique_prefix = f"UniqueCrit{uuid.uuid4().hex[:8]}"
        
        for i in range(num_patients):
            unique_mobile = str(base_number + i)
            if len(unique_mobile) != 10:
                unique_mobile = f"9{(base_number + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"{unique_prefix} Patient {i}",
                age=30 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=unique_mobile
            )
            created_patients.append(patient)
        
        # Test that each patient can be found by all three criteria
        for patient in created_patients:
            # Search by patient ID
            results_by_id = await patient_crud.search_patients(db_session, patient.patient_id)
            id_found = any(p.patient_id == patient.patient_id for p in results_by_id)
            assert id_found, (
                f"Patient '{patient.name}' should be found by patient ID '{patient.patient_id}'"
            )
            
            # Search by mobile number
            results_by_mobile = await patient_crud.search_patients(db_session, patient.mobile_number)
            mobile_found = any(p.patient_id == patient.patient_id for p in results_by_mobile)
            assert mobile_found, (
                f"Patient '{patient.name}' should be found by mobile number '{patient.mobile_number}'"
            )
            
            # Search by name
            results_by_name = await patient_crud.search_patients(db_session, patient.name)
            name_found = any(p.patient_id == patient.patient_id for p in results_by_name)
            assert name_found, (
                f"Patient '{patient.name}' (ID: {patient.patient_id}) should be found by name. "
                f"Searched for '{patient.name}', found {len(results_by_name)} results: "
                f"{[p.name for p in results_by_name]}"
            )


class TestSearchFunctionalityExamples:
    """Unit tests for specific search functionality scenarios"""
    
    @pytest.mark.asyncio
    async def test_search_by_exact_patient_id(self, db_session: AsyncSession):
        """Test search by exact patient ID"""
        # Create a patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="John Doe",
            age=30,
            gender=Gender.MALE,
            address="123 Test St",
            mobile_number="9876543210"
        )
        
        # Search by exact patient ID
        results = await patient_crud.search_patients(db_session, patient.patient_id)
        
        assert len(results) >= 1
        assert patient.patient_id in [p.patient_id for p in results]
    
    @pytest.mark.asyncio
    async def test_search_by_exact_mobile(self, db_session: AsyncSession):
        """Test search by exact mobile number"""
        # Create a patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Jane Doe",
            age=25,
            gender=Gender.FEMALE,
            address="456 Test Ave",
            mobile_number="9876543211"
        )
        
        # Search by exact mobile number
        results = await patient_crud.search_patients(db_session, "9876543211")
        
        assert len(results) >= 1
        assert patient.patient_id in [p.patient_id for p in results]
    
    @pytest.mark.asyncio
    async def test_search_by_exact_name(self, db_session: AsyncSession):
        """Test search by exact patient name"""
        # Create a patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Alice Smith",
            age=28,
            gender=Gender.FEMALE,
            address="789 Test Blvd",
            mobile_number="9876543212"
        )
        
        # Search by exact name
        results = await patient_crud.search_patients(db_session, "Alice Smith")
        
        assert len(results) >= 1
        assert patient.patient_id in [p.patient_id for p in results]
    
    @pytest.mark.asyncio
    async def test_search_by_partial_name(self, db_session: AsyncSession):
        """Test search by partial patient name"""
        # Create patients
        patient1 = await patient_crud.create_patient(
            db=db_session,
            name="Robert Johnson",
            age=35,
            gender=Gender.MALE,
            address="111 Test St",
            mobile_number="9876543213"
        )
        
        patient2 = await patient_crud.create_patient(
            db=db_session,
            name="Robert Williams",
            age=40,
            gender=Gender.MALE,
            address="222 Test Ave",
            mobile_number="9876543214"
        )
        
        # Search by partial name "Robert"
        results = await patient_crud.search_patients(db_session, "Robert")
        
        result_ids = [p.patient_id for p in results]
        assert patient1.patient_id in result_ids
        assert patient2.patient_id in result_ids
    
    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, db_session: AsyncSession):
        """Test that search is case-insensitive"""
        # Create a patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Michael Brown",
            age=32,
            gender=Gender.MALE,
            address="333 Test Blvd",
            mobile_number="9876543215"
        )
        
        # Search with different cases
        results_lower = await patient_crud.search_patients(db_session, "michael")
        results_upper = await patient_crud.search_patients(db_session, "MICHAEL")
        results_mixed = await patient_crud.search_patients(db_session, "MiChAeL")
        
        # All should find the patient
        assert patient.patient_id in [p.patient_id for p in results_lower]
        assert patient.patient_id in [p.patient_id for p in results_upper]
        assert patient.patient_id in [p.patient_id for p in results_mixed]
    
    @pytest.mark.asyncio
    async def test_search_empty_string(self, db_session: AsyncSession):
        """Test search with empty string returns empty list"""
        # Create a patient
        await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543216"
        )
        
        # Search with empty string
        results = await patient_crud.search_patients(db_session, "")
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_whitespace_only(self, db_session: AsyncSession):
        """Test search with whitespace only returns empty list"""
        # Create a patient
        await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543217"
        )
        
        # Search with whitespace
        results = await patient_crud.search_patients(db_session, "   ")
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_nonexistent_patient(self, db_session: AsyncSession):
        """Test search for non-existent patient returns empty list"""
        # Create a patient
        await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543218"
        )
        
        # Search for non-existent patient
        results = await patient_crud.search_patients(db_session, "NonExistentPatient12345")
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_partial_mobile(self, db_session: AsyncSession):
        """Test search by partial mobile number"""
        # Create a patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Mobile Test",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543219"
        )
        
        # Search by partial mobile (last 4 digits)
        results = await patient_crud.search_patients(db_session, "3219")
        
        assert len(results) >= 1
        assert patient.patient_id in [p.patient_id for p in results]
    
    @pytest.mark.asyncio
    async def test_search_partial_patient_id(self, db_session: AsyncSession):
        """Test search by partial patient ID"""
        # Create a patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="ID Test",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543220"
        )
        
        # Search by partial patient ID (first few characters)
        partial_id = patient.patient_id[:5]
        results = await patient_crud.search_patients(db_session, partial_id)
        
        assert len(results) >= 1
        assert patient.patient_id in [p.patient_id for p in results]
    
    @pytest.mark.asyncio
    async def test_search_multiple_matches(self, db_session: AsyncSession):
        """Test search that returns multiple matching patients"""
        # Create multiple patients with similar names
        patient1 = await patient_crud.create_patient(
            db=db_session,
            name="Kumar Patel",
            age=30,
            gender=Gender.MALE,
            address="Address 1",
            mobile_number="9876543221"
        )
        
        patient2 = await patient_crud.create_patient(
            db=db_session,
            name="Kumar Singh",
            age=35,
            gender=Gender.MALE,
            address="Address 2",
            mobile_number="9876543222"
        )
        
        patient3 = await patient_crud.create_patient(
            db=db_session,
            name="Kumar Sharma",
            age=40,
            gender=Gender.MALE,
            address="Address 3",
            mobile_number="9876543223"
        )
        
        # Search by common name "Kumar"
        results = await patient_crud.search_patients(db_session, "Kumar")
        
        result_ids = [p.patient_id for p in results]
        assert len(results) >= 3
        assert patient1.patient_id in result_ids
        assert patient2.patient_id in result_ids
        assert patient3.patient_id in result_ids
    
    @pytest.mark.asyncio
    async def test_search_result_limit(self, db_session: AsyncSession):
        """Test that search respects the result limit"""
        # Create many patients with similar names
        import time
        import random
        base_number = int(f"9{int(time.time() * 1000) % 100000000:08d}"[-9:] + f"{random.randint(10, 99):02d}")
        
        for i in range(60):  # Create more than the default limit of 50
            unique_mobile = str(base_number + i)
            if len(unique_mobile) != 10:
                unique_mobile = f"9{(base_number + i) % 1000000000:09d}"
            
            await patient_crud.create_patient(
                db=db_session,
                name=f"LimitTest Patient {i}",
                age=30,
                gender=Gender.MALE,
                address=f"Address {i}",
                mobile_number=unique_mobile
            )
        
        # Search for all patients with "LimitTest"
        results = await patient_crud.search_patients(db_session, "LimitTest")
        
        # Should return at most 50 results (default limit)
        assert len(results) <= 50, "Search should respect the default limit of 50 results"
