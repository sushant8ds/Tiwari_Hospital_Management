"""
Property-based tests for doctor-department consistency

**Feature: hospital-management-system, Property 4: Doctor-Department Consistency**
**Validates: Requirements 1.4**
"""

import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from decimal import Decimal
from datetime import date, time, datetime

from app.models.doctor import Doctor, DoctorStatus
from app.models.patient import Patient, Gender
from app.models.visit import Visit, VisitType, PaymentMode
from app.crud.doctor import doctor_crud
from app.crud.patient import patient_crud
from app.crud.visit import visit_crud


# Strategy for generating valid doctor data
@st.composite
def valid_doctor_data(draw):
    """Generate valid doctor data with department"""
    departments = ["Cardiology", "Neurology", "Orthopedics", "Pediatrics", "General Medicine"]
    return {
        "name": draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        "department": draw(st.sampled_from(departments)),
        "new_patient_fee": Decimal(str(draw(st.floats(min_value=100, max_value=5000, allow_nan=False, allow_infinity=False)))),
        "followup_fee": Decimal(str(draw(st.floats(min_value=50, max_value=2500, allow_nan=False, allow_infinity=False)))),
        "status": DoctorStatus.ACTIVE
    }


# Strategy for generating valid patient data
@st.composite
def valid_patient_data(draw):
    """Generate valid patient data"""
    # Generate valid Indian mobile number (10 digits starting with 6-9)
    first_digit = draw(st.sampled_from(['6', '7', '8', '9']))
    remaining_digits = draw(st.text(min_size=9, max_size=9, alphabet='0123456789'))
    mobile = first_digit + remaining_digits
    
    return {
        "name": draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        "age": draw(st.integers(min_value=0, max_value=150)),
        "gender": draw(st.sampled_from([Gender.MALE, Gender.FEMALE, Gender.OTHER])),
        "address": draw(st.text(min_size=1, max_size=500).filter(lambda x: x.strip())),
        "mobile_number": mobile
    }


class TestDoctorDepartmentConsistencyProperty:
    """Property-based tests for doctor-department consistency"""
    
    @given(
        doctor_data=valid_doctor_data(),
        patient_data=valid_patient_data(),
        visit_type=st.sampled_from([VisitType.OPD_NEW, VisitType.OPD_FOLLOWUP]),
        payment_mode=st.sampled_from([PaymentMode.CASH, PaymentMode.UPI, PaymentMode.CARD])
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_doctor_department_consistency_property(
        self,
        db_session: AsyncSession,
        doctor_data: Dict[str, Any],
        patient_data: Dict[str, Any],
        visit_type: VisitType,
        payment_mode: PaymentMode
    ):
        """
        Property: For any doctor selection in OPD registration, the corresponding 
        department should be automatically populated and match the doctor's assigned department.
        
        **Validates: Requirements 1.4**
        """
        # Create a doctor with a specific department
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name=doctor_data["name"],
            department=doctor_data["department"],
            new_patient_fee=doctor_data["new_patient_fee"],
            followup_fee=doctor_data["followup_fee"],
            status=doctor_data["status"]
        )
        
        # Verify doctor was created with correct department
        assert doctor is not None, "Doctor should be created successfully"
        assert doctor.department is not None, "Doctor should have a department"
        expected_department = doctor_data["department"].strip().title()
        assert doctor.department == expected_department, (
            f"Doctor department should be '{expected_department}' but got '{doctor.department}'"
        )
        
        # Check if mobile number already exists and skip if it does
        existing = await patient_crud.get_patient_by_mobile(db_session, patient_data["mobile_number"])
        assume(existing is None)  # Skip this test case if mobile already exists
        
        # Create a patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name=patient_data["name"],
            age=patient_data["age"],
            gender=patient_data["gender"],
            address=patient_data["address"],
            mobile_number=patient_data["mobile_number"]
        )
        
        # Create a visit for this patient with the doctor
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=visit_type,
            payment_mode=payment_mode
        )
        
        # Verify the visit was created
        assert visit is not None, "Visit should be created successfully"
        
        # CRITICAL PROPERTY: The visit's department should automatically match the doctor's department
        assert visit.department == doctor.department, (
            f"Visit department '{visit.department}' should automatically match "
            f"doctor's department '{doctor.department}' when doctor is selected"
        )
        
        # Verify the department is not empty or null
        assert visit.department is not None, "Visit department should not be None"
        assert visit.department.strip() != "", "Visit department should not be empty"
        
        # Verify the doctor-visit relationship
        assert visit.doctor_id == doctor.doctor_id, (
            f"Visit should be linked to doctor {doctor.doctor_id}"
        )
    
    @given(
        num_doctors=st.integers(min_value=3, max_value=10),
        num_visits_per_doctor=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_multiple_doctors_department_consistency_property(
        self,
        db_session: AsyncSession,
        num_doctors: int,
        num_visits_per_doctor: int
    ):
        """
        Property: For any set of doctors with different departments, all visits 
        should consistently reflect the correct department for each doctor.
        
        **Validates: Requirements 1.4**
        """
        departments = ["Cardiology", "Neurology", "Orthopedics", "Pediatrics", "General Medicine"]
        doctors = []
        
        # Create multiple doctors with different departments
        for i in range(num_doctors):
            department = departments[i % len(departments)]
            doctor = await doctor_crud.create_doctor(
                db=db_session,
                name=f"Dr. Test {i}",
                department=department,
                new_patient_fee=Decimal("500.00"),
                followup_fee=Decimal("300.00"),
                status=DoctorStatus.ACTIVE
            )
            doctors.append(doctor)
        
        # Create patients and visits for each doctor
        import time
        import random
        base_timestamp = int(time.time() * 1000) % 100000000
        
        for doctor in doctors:
            for j in range(num_visits_per_doctor):
                # Create unique patient for each visit
                mobile = f"9{(base_timestamp + len(doctors) * j + doctors.index(doctor)) % 1000000000:09d}"
                
                patient = await patient_crud.create_patient(
                    db=db_session,
                    name=f"Patient {doctors.index(doctor)}-{j}",
                    age=30,
                    gender=Gender.MALE,
                    address="Test Address",
                    mobile_number=mobile
                )
                
                # Create visit
                visit = await visit_crud.create_visit(
                    db=db_session,
                    patient_id=patient.patient_id,
                    doctor_id=doctor.doctor_id,
                    visit_type=VisitType.OPD_NEW,
                    payment_mode=PaymentMode.CASH
                )
                
                # CRITICAL PROPERTY: Each visit's department must match its doctor's department
                assert visit.department == doctor.department, (
                    f"Visit {visit.visit_id} department '{visit.department}' should match "
                    f"doctor {doctor.doctor_id} department '{doctor.department}'"
                )
    
    @given(
        doctor_data=valid_doctor_data(),
        num_visits=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_single_doctor_multiple_visits_consistency_property(
        self,
        db_session: AsyncSession,
        doctor_data: Dict[str, Any],
        num_visits: int
    ):
        """
        Property: For any doctor, all visits created with that doctor should 
        consistently have the same department as the doctor.
        
        **Validates: Requirements 1.4**
        """
        # Create a doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name=doctor_data["name"],
            department=doctor_data["department"],
            new_patient_fee=doctor_data["new_patient_fee"],
            followup_fee=doctor_data["followup_fee"],
            status=doctor_data["status"]
        )
        
        expected_department = doctor.department
        visits = []
        
        # Create multiple visits for this doctor
        import time
        base_timestamp = int(time.time() * 1000) % 100000000
        
        for i in range(num_visits):
            # Create unique patient
            mobile = f"9{(base_timestamp + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=25 + (i % 50),
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=mobile
            )
            
            # Create visit
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                visit_type=VisitType.OPD_NEW if i % 3 == 0 else VisitType.OPD_FOLLOWUP,
                payment_mode=PaymentMode.CASH
            )
            visits.append(visit)
        
        # CRITICAL PROPERTY: All visits should have the same department as the doctor
        for visit in visits:
            assert visit.department == expected_department, (
                f"Visit {visit.visit_id} department '{visit.department}' should match "
                f"doctor's department '{expected_department}'"
            )
        
        # Verify all visits have the same department
        departments_in_visits = set(v.department for v in visits)
        assert len(departments_in_visits) == 1, (
            f"All visits for the same doctor should have the same department, "
            f"but found {len(departments_in_visits)} different departments: {departments_in_visits}"
        )
    
    @given(
        initial_department=st.sampled_from(["Cardiology", "Neurology", "Orthopedics"]),
        new_department=st.sampled_from(["Pediatrics", "General Medicine", "Surgery"])
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_department_change_consistency_property(
        self,
        db_session: AsyncSession,
        initial_department: str,
        new_department: str
    ):
        """
        Property: When a doctor's department is changed, new visits should reflect 
        the updated department while old visits retain the original department.
        
        **Validates: Requirements 1.4**
        """
        # Create a doctor with initial department
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Department Change",
            department=initial_department,
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00"),
            status=DoctorStatus.ACTIVE
        )
        
        # Create a patient and visit with initial department
        import time
        mobile1 = f"9{int(time.time() * 1000) % 1000000000:09d}"
        
        patient1 = await patient_crud.create_patient(
            db=db_session,
            name="Patient Before Change",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=mobile1
        )
        
        visit_before = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient1.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Verify visit has initial department
        assert visit_before.department == initial_department.strip().title(), (
            f"Visit before change should have department '{initial_department}'"
        )
        
        # Update doctor's department
        updated_doctor = await doctor_crud.update_doctor(
            db=db_session,
            doctor_id=doctor.doctor_id,
            department=new_department
        )
        
        assert updated_doctor is not None, "Doctor update should succeed"
        assert updated_doctor.department == new_department.strip().title(), (
            f"Doctor department should be updated to '{new_department}'"
        )
        
        # Create another patient and visit with new department
        mobile2 = f"9{(int(time.time() * 1000) + 1) % 1000000000:09d}"
        
        patient2 = await patient_crud.create_patient(
            db=db_session,
            name="Patient After Change",
            age=35,
            gender=Gender.FEMALE,
            address="Test Address 2",
            mobile_number=mobile2
        )
        
        visit_after = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient2.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # CRITICAL PROPERTY: New visit should have the updated department
        assert visit_after.department == new_department.strip().title(), (
            f"Visit after change should have new department '{new_department}', "
            f"but got '{visit_after.department}'"
        )
        
        # Verify the old visit still has the original department (historical data integrity)
        await db_session.refresh(visit_before)
        assert visit_before.department == initial_department.strip().title(), (
            f"Old visit should retain original department '{initial_department}'"
        )


class TestDoctorDepartmentConsistencyExamples:
    """Unit tests for specific doctor-department consistency scenarios"""
    
    @pytest.mark.asyncio
    async def test_opd_new_visit_department_matches_doctor(self, db_session: AsyncSession):
        """Test that new OPD visit automatically gets doctor's department"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Cardio",
            department="Cardiology",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="John Doe",
            age=45,
            gender=Gender.MALE,
            address="123 Test St",
            mobile_number="9876543210"
        )
        
        # Create visit
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Verify department consistency
        assert visit.department == "Cardiology"
        assert visit.department == doctor.department
    
    @pytest.mark.asyncio
    async def test_followup_visit_department_matches_doctor(self, db_session: AsyncSession):
        """Test that follow-up visit automatically gets doctor's department"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Neuro",
            department="Neurology",
            new_patient_fee=Decimal("600.00"),
            followup_fee=Decimal("400.00")
        )
        
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Jane Smith",
            age=35,
            gender=Gender.FEMALE,
            address="456 Test Ave",
            mobile_number="9876543211"
        )
        
        # Create follow-up visit
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_FOLLOWUP,
            payment_mode=PaymentMode.UPI
        )
        
        # Verify department consistency
        assert visit.department == "Neurology"
        assert visit.department == doctor.department
    
    @pytest.mark.asyncio
    async def test_multiple_doctors_different_departments(self, db_session: AsyncSession):
        """Test that visits to different doctors get correct departments"""
        # Create doctors in different departments
        doctor1 = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Ortho",
            department="Orthopedics",
            new_patient_fee=Decimal("700.00"),
            followup_fee=Decimal("500.00")
        )
        
        doctor2 = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Pedia",
            department="Pediatrics",
            new_patient_fee=Decimal("400.00"),
            followup_fee=Decimal("250.00")
        )
        
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Multi Visit Patient",
            age=40,
            gender=Gender.MALE,
            address="789 Test Blvd",
            mobile_number="9876543212"
        )
        
        # Create visits to different doctors
        visit1 = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor1.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        visit2 = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor2.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CARD
        )
        
        # Verify each visit has the correct department
        assert visit1.department == "Orthopedics"
        assert visit1.department == doctor1.department
        
        assert visit2.department == "Pediatrics"
        assert visit2.department == doctor2.department
        
        # Verify visits have different departments
        assert visit1.department != visit2.department
    
    @pytest.mark.asyncio
    async def test_department_not_empty_or_null(self, db_session: AsyncSession):
        """Test that visit department is never empty or null"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. General",
            department="General Medicine",
            new_patient_fee=Decimal("300.00"),
            followup_fee=Decimal("200.00")
        )
        
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=50,
            gender=Gender.OTHER,
            address="Test Address",
            mobile_number="9876543213"
        )
        
        # Create visit
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Verify department is not empty or null
        assert visit.department is not None
        assert visit.department.strip() != ""
        assert len(visit.department) > 0
    
    @pytest.mark.asyncio
    async def test_department_consistency_across_payment_modes(self, db_session: AsyncSession):
        """Test that department consistency holds regardless of payment mode"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Surgery",
            department="Surgery",
            new_patient_fee=Decimal("1000.00"),
            followup_fee=Decimal("700.00")
        )
        
        # Create patients and visits with different payment modes
        payment_modes = [PaymentMode.CASH, PaymentMode.UPI, PaymentMode.CARD]
        
        for i, payment_mode in enumerate(payment_modes):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=30 + i,
                gender=Gender.MALE,
                address=f"Address {i}",
                mobile_number=f"987654321{4+i}"
            )
            
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                visit_type=VisitType.OPD_NEW,
                payment_mode=payment_mode
            )
            
            # Verify department consistency regardless of payment mode
            assert visit.department == "Surgery"
            assert visit.department == doctor.department
    
    @pytest.mark.asyncio
    async def test_department_consistency_with_visit_retrieval(self, db_session: AsyncSession):
        """Test that department remains consistent when visit is retrieved from database"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Retrieve",
            department="Dermatology",
            new_patient_fee=Decimal("450.00"),
            followup_fee=Decimal("300.00")
        )
        
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Retrieve Patient",
            age=28,
            gender=Gender.FEMALE,
            address="Retrieve Address",
            mobile_number="9876543217"
        )
        
        # Create visit
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        original_department = visit.department
        visit_id = visit.visit_id
        
        # Retrieve visit from database
        retrieved_visit = await visit_crud.get_visit_by_id(db_session, visit_id)
        
        # Verify department consistency after retrieval
        assert retrieved_visit is not None
        assert retrieved_visit.department == original_department
        assert retrieved_visit.department == doctor.department
        assert retrieved_visit.department == "Dermatology"
