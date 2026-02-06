"""
Property-based tests for required field validation

**Feature: hospital-management-system, Property 2: Required Field Validation**
**Validates: Requirements 1.2, 8.1, 16.1**
"""

import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import date, timedelta

from app.models.patient import Patient, Gender
from app.models.doctor import Doctor, DoctorStatus
from app.models.employee import Employee, EmploymentStatus, EmployeeStatus
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud


# Strategy for generating valid patient data
@st.composite
def valid_patient_data(draw):
    """Generate valid patient data"""
    return {
        "name": draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        "age": draw(st.integers(min_value=0, max_value=150)),
        "gender": draw(st.sampled_from([Gender.MALE, Gender.FEMALE, Gender.OTHER])),
        "address": draw(st.text(min_size=1, max_size=500).filter(lambda x: x.strip())),
        "mobile_number": draw(st.from_regex(r'^[6-9]\d{9}$', fullmatch=True))
    }


# Strategy for generating invalid patient data (missing required fields)
@st.composite
def invalid_patient_data(draw):
    """Generate invalid patient data with missing or invalid required fields"""
    # Start with valid data
    data = {
        "name": draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        "age": draw(st.integers(min_value=0, max_value=150)),
        "gender": draw(st.sampled_from([Gender.MALE, Gender.FEMALE, Gender.OTHER])),
        "address": draw(st.text(min_size=1, max_size=500).filter(lambda x: x.strip())),
        "mobile_number": draw(st.from_regex(r'^[6-9]\d{9}$', fullmatch=True))
    }
    
    # Choose which field to invalidate
    invalid_field = draw(st.sampled_from([
        "name_empty", "name_whitespace", "age_negative", "age_too_high",
        "address_empty", "address_whitespace", "mobile_invalid_format",
        "mobile_too_short", "mobile_too_long", "mobile_invalid_start"
    ]))
    
    if invalid_field == "name_empty":
        data["name"] = ""
    elif invalid_field == "name_whitespace":
        data["name"] = "   "
    elif invalid_field == "age_negative":
        data["age"] = draw(st.integers(max_value=-1))
    elif invalid_field == "age_too_high":
        data["age"] = draw(st.integers(min_value=151, max_value=1000))
    elif invalid_field == "address_empty":
        data["address"] = ""
    elif invalid_field == "address_whitespace":
        data["address"] = "   "
    elif invalid_field == "mobile_invalid_format":
        data["mobile_number"] = draw(st.text(min_size=1, max_size=20).filter(
            lambda x: not x.isdigit() or len(x) != 10
        ))
    elif invalid_field == "mobile_too_short":
        data["mobile_number"] = draw(st.from_regex(r'^\d{1,9}$', fullmatch=True))
    elif invalid_field == "mobile_too_long":
        data["mobile_number"] = draw(st.from_regex(r'^\d{11,15}$', fullmatch=True))
    elif invalid_field == "mobile_invalid_start":
        # Mobile numbers should start with 6-9
        data["mobile_number"] = draw(st.from_regex(r'^[0-5]\d{9}$', fullmatch=True))
    
    return data, invalid_field


# Strategy for generating valid doctor data
@st.composite
def valid_doctor_data(draw):
    """Generate valid doctor data"""
    return {
        "name": draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        "department": draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip())),
        "new_patient_fee": Decimal(str(draw(st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False)))),
        "followup_fee": Decimal(str(draw(st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False)))),
        "status": draw(st.sampled_from([DoctorStatus.ACTIVE, DoctorStatus.INACTIVE]))
    }


# Strategy for generating invalid doctor data
@st.composite
def invalid_doctor_data(draw):
    """Generate invalid doctor data with missing or invalid required fields"""
    data = {
        "name": draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        "department": draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip())),
        "new_patient_fee": Decimal(str(draw(st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False)))),
        "followup_fee": Decimal(str(draw(st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False)))),
        "status": draw(st.sampled_from([DoctorStatus.ACTIVE, DoctorStatus.INACTIVE]))
    }
    
    # Choose which field to invalidate
    invalid_field = draw(st.sampled_from([
        "name_empty", "name_whitespace", "department_empty", "department_whitespace",
        "new_patient_fee_negative", "followup_fee_negative"
    ]))
    
    if invalid_field == "name_empty":
        data["name"] = ""
    elif invalid_field == "name_whitespace":
        data["name"] = "   "
    elif invalid_field == "department_empty":
        data["department"] = ""
    elif invalid_field == "department_whitespace":
        data["department"] = "   "
    elif invalid_field == "new_patient_fee_negative":
        data["new_patient_fee"] = Decimal(str(draw(st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False))))
    elif invalid_field == "followup_fee_negative":
        data["followup_fee"] = Decimal(str(draw(st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False))))
    
    return data, invalid_field


# Strategy for generating valid employee data
@st.composite
def valid_employee_data(draw):
    """Generate valid employee data"""
    today = date.today()
    return {
        "name": draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        "post": draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip())),
        "qualification": draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
        "employment_status": draw(st.sampled_from([EmploymentStatus.PERMANENT, EmploymentStatus.PROBATION])),
        "duty_hours": draw(st.integers(min_value=1, max_value=24)),
        "joining_date": draw(st.dates(min_value=today - timedelta(days=365*50), max_value=today)),
        "monthly_salary": Decimal(str(draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)))),
        "status": draw(st.sampled_from([EmployeeStatus.ACTIVE, EmployeeStatus.INACTIVE]))
    }


# Strategy for generating invalid employee data
@st.composite
def invalid_employee_data(draw):
    """Generate invalid employee data with missing or invalid required fields"""
    today = date.today()
    data = {
        "name": draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        "post": draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip())),
        "qualification": draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
        "employment_status": draw(st.sampled_from([EmploymentStatus.PERMANENT, EmploymentStatus.PROBATION])),
        "duty_hours": draw(st.integers(min_value=1, max_value=24)),
        "joining_date": draw(st.dates(min_value=today - timedelta(days=365*50), max_value=today)),
        "monthly_salary": Decimal(str(draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)))),
        "status": draw(st.sampled_from([EmployeeStatus.ACTIVE, EmployeeStatus.INACTIVE]))
    }
    
    # Choose which field to invalidate
    invalid_field = draw(st.sampled_from([
        "name_empty", "name_whitespace", "post_empty", "post_whitespace",
        "duty_hours_zero", "duty_hours_negative", "monthly_salary_negative"
    ]))
    
    if invalid_field == "name_empty":
        data["name"] = ""
    elif invalid_field == "name_whitespace":
        data["name"] = "   "
    elif invalid_field == "post_empty":
        data["post"] = ""
    elif invalid_field == "post_whitespace":
        data["post"] = "   "
    elif invalid_field == "duty_hours_zero":
        data["duty_hours"] = 0
    elif invalid_field == "duty_hours_negative":
        data["duty_hours"] = draw(st.integers(max_value=-1))
    elif invalid_field == "monthly_salary_negative":
        data["monthly_salary"] = Decimal(str(draw(st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False))))
    
    return data, invalid_field


class TestRequiredFieldValidationProperty:
    """Property-based tests for required field validation"""
    
    @given(patient_data=valid_patient_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_valid_patient_data_accepted_property(
        self,
        db_session: AsyncSession,
        patient_data: Dict[str, Any]
    ):
        """
        Property: For any valid patient data with all required fields,
        the system should accept and create the patient record.
        
        **Validates: Requirements 1.2**
        """
        # Check if mobile number already exists and skip if it does
        existing = await patient_crud.get_patient_by_mobile(db_session, patient_data["mobile_number"])
        assume(existing is None)  # Skip this test case if mobile already exists
        
        try:
            patient = await patient_crud.create_patient(
                db=db_session,
                name=patient_data["name"],
                age=patient_data["age"],
                gender=patient_data["gender"],
                address=patient_data["address"],
                mobile_number=patient_data["mobile_number"]
            )
            
            # Verify patient was created successfully
            assert patient is not None, "Patient creation should succeed with valid data"
            assert patient.patient_id is not None, "Patient ID should be generated"
            # Names are sanitized with .title() formatting
            assert patient.name.strip().title() == patient_data["name"].strip().title(), "Patient name should match"
            assert patient.age == patient_data["age"], "Patient age should match"
            assert patient.gender == patient_data["gender"], "Patient gender should match"
            assert patient.mobile_number == patient_data["mobile_number"], "Mobile number should match"
            
        except Exception as e:
            pytest.fail(f"Valid patient data should be accepted but got error: {e}")
    
    @given(invalid_data=invalid_patient_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_invalid_patient_data_rejected_property(
        self,
        db_session: AsyncSession,
        invalid_data: tuple
    ):
        """
        Property: For any patient data with missing or invalid required fields,
        the system should reject the data and raise an appropriate error.
        
        **Validates: Requirements 1.2**
        """
        patient_data, invalid_field = invalid_data
        
        # Attempt to create patient with invalid data
        with pytest.raises((ValueError, Exception)) as exc_info:
            await patient_crud.create_patient(
                db=db_session,
                name=patient_data["name"],
                age=patient_data["age"],
                gender=patient_data["gender"],
                address=patient_data["address"],
                mobile_number=patient_data["mobile_number"]
            )
        
        # Verify that an error was raised
        assert exc_info.value is not None, (
            f"Invalid patient data (field: {invalid_field}) should be rejected"
        )
    
    @given(doctor_data=valid_doctor_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_valid_doctor_data_accepted_property(
        self,
        db_session: AsyncSession,
        doctor_data: Dict[str, Any]
    ):
        """
        Property: For any valid doctor data with all required fields,
        the system should accept and create the doctor record.
        
        **Validates: Requirements 16.1**
        """
        try:
            doctor = await doctor_crud.create_doctor(
                db=db_session,
                name=doctor_data["name"],
                department=doctor_data["department"],
                new_patient_fee=doctor_data["new_patient_fee"],
                followup_fee=doctor_data["followup_fee"],
                status=doctor_data["status"]
            )
            
            # Verify doctor was created successfully
            assert doctor is not None, "Doctor creation should succeed with valid data"
            assert doctor.doctor_id is not None, "Doctor ID should be generated"
            # Names are sanitized with .title() formatting
            assert doctor.name.strip().title() == doctor_data["name"].strip().title(), "Doctor name should match"
            assert doctor.department.strip().title() == doctor_data["department"].strip().title(), "Department should match"
            # Use quantize to compare decimal values with 2 decimal places
            assert doctor.new_patient_fee.quantize(Decimal('0.01')) == doctor_data["new_patient_fee"].quantize(Decimal('0.01')), "New patient fee should match"
            assert doctor.followup_fee.quantize(Decimal('0.01')) == doctor_data["followup_fee"].quantize(Decimal('0.01')), "Follow-up fee should match"
            
        except Exception as e:
            pytest.fail(f"Valid doctor data should be accepted but got error: {e}")
    
    @given(invalid_data=invalid_doctor_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_invalid_doctor_data_rejected_property(
        self,
        db_session: AsyncSession,
        invalid_data: tuple
    ):
        """
        Property: For any doctor data with missing or invalid required fields,
        the system should reject the data and raise an appropriate error.
        
        **Validates: Requirements 16.1**
        """
        doctor_data, invalid_field = invalid_data
        
        # Attempt to create doctor with invalid data
        with pytest.raises((ValueError, Exception)) as exc_info:
            await doctor_crud.create_doctor(
                db=db_session,
                name=doctor_data["name"],
                department=doctor_data["department"],
                new_patient_fee=doctor_data["new_patient_fee"],
                followup_fee=doctor_data["followup_fee"],
                status=doctor_data["status"]
            )
        
        # Verify that an error was raised
        assert exc_info.value is not None, (
            f"Invalid doctor data (field: {invalid_field}) should be rejected"
        )
    
    @given(
        patient_data=valid_patient_data(),
        num_patients=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_multiple_valid_patients_accepted_property(
        self,
        db_session: AsyncSession,
        patient_data: Dict[str, Any],
        num_patients: int
    ):
        """
        Property: For any sequence of valid patient data entries,
        all should be accepted and created successfully.
        
        **Validates: Requirements 1.2**
        """
        created_patients = []
        
        # Generate a unique base number for this test run using timestamp
        import time
        import random
        # Use timestamp + random to ensure uniqueness across test runs
        timestamp_part = int(time.time() * 1000) % 100000000  # 8 digits
        random_part = random.randint(10, 99)  # 2 digits
        base_number = int(f"9{timestamp_part:08d}"[-9:] + f"{random_part:02d}")  # Ensure 10 digits starting with 9
        
        for i in range(num_patients):
            # Create unique mobile number by incrementing from base
            unique_mobile = str(base_number + i)
            
            # Ensure mobile number is exactly 10 digits
            if len(unique_mobile) != 10:
                # Pad or truncate to 10 digits, ensuring it starts with 9
                unique_mobile = f"9{(base_number + i) % 1000000000:09d}"
            
            try:
                patient = await patient_crud.create_patient(
                    db=db_session,
                    name=f"{patient_data['name']} {i}",
                    age=patient_data["age"],
                    gender=patient_data["gender"],
                    address=patient_data["address"],
                    mobile_number=unique_mobile
                )
                created_patients.append(patient)
            except Exception as e:
                pytest.fail(f"Valid patient data should be accepted but got error: {e}")
        
        # Verify all patients were created
        assert len(created_patients) == num_patients, (
            f"All {num_patients} valid patients should be created"
        )
    
    @given(
        doctor_data=valid_doctor_data(),
        num_doctors=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_multiple_valid_doctors_accepted_property(
        self,
        db_session: AsyncSession,
        doctor_data: Dict[str, Any],
        num_doctors: int
    ):
        """
        Property: For any sequence of valid doctor data entries,
        all should be accepted and created successfully.
        
        **Validates: Requirements 16.1**
        """
        created_doctors = []
        
        for i in range(num_doctors):
            try:
                doctor = await doctor_crud.create_doctor(
                    db=db_session,
                    name=f"{doctor_data['name']} {i}",
                    department=doctor_data["department"],
                    new_patient_fee=doctor_data["new_patient_fee"],
                    followup_fee=doctor_data["followup_fee"],
                    status=doctor_data["status"]
                )
                created_doctors.append(doctor)
            except Exception as e:
                pytest.fail(f"Valid doctor data should be accepted but got error: {e}")
        
        # Verify all doctors were created
        assert len(created_doctors) == num_doctors, (
            f"All {num_doctors} valid doctors should be created"
        )


class TestRequiredFieldValidationExamples:
    """Unit tests for specific required field validation scenarios"""
    
    @pytest.mark.asyncio
    async def test_patient_missing_name(self, db_session: AsyncSession):
        """Test that patient creation fails when name is missing"""
        with pytest.raises(ValueError, match="name"):
            await patient_crud.create_patient(
                db=db_session,
                name="",
                age=30,
                gender=Gender.MALE,
                address="123 Test St",
                mobile_number="9876543210"
            )
    
    @pytest.mark.asyncio
    async def test_patient_invalid_age(self, db_session: AsyncSession):
        """Test that patient creation fails with invalid age"""
        with pytest.raises(ValueError, match="[Aa]ge"):
            await patient_crud.create_patient(
                db=db_session,
                name="John Doe",
                age=-5,
                gender=Gender.MALE,
                address="123 Test St",
                mobile_number="9876543210"
            )
    
    @pytest.mark.asyncio
    async def test_patient_invalid_mobile(self, db_session: AsyncSession):
        """Test that patient creation fails with invalid mobile number"""
        with pytest.raises(ValueError, match="mobile"):
            await patient_crud.create_patient(
                db=db_session,
                name="John Doe",
                age=30,
                gender=Gender.MALE,
                address="123 Test St",
                mobile_number="123"  # Too short
            )
    
    @pytest.mark.asyncio
    async def test_patient_missing_address(self, db_session: AsyncSession):
        """Test that patient creation fails when address is missing"""
        with pytest.raises(ValueError, match="address"):
            await patient_crud.create_patient(
                db=db_session,
                name="John Doe",
                age=30,
                gender=Gender.MALE,
                address="",
                mobile_number="9876543210"
            )
    
    @pytest.mark.asyncio
    async def test_doctor_missing_name(self, db_session: AsyncSession):
        """Test that doctor creation fails when name is missing"""
        with pytest.raises(ValueError, match="name"):
            await doctor_crud.create_doctor(
                db=db_session,
                name="",
                department="Cardiology",
                new_patient_fee=Decimal("500.00"),
                followup_fee=Decimal("300.00")
            )
    
    @pytest.mark.asyncio
    async def test_doctor_missing_department(self, db_session: AsyncSession):
        """Test that doctor creation fails when department is missing"""
        with pytest.raises(ValueError, match="[Dd]epartment"):
            await doctor_crud.create_doctor(
                db=db_session,
                name="Dr. Smith",
                department="",
                new_patient_fee=Decimal("500.00"),
                followup_fee=Decimal("300.00")
            )
    
    @pytest.mark.asyncio
    async def test_doctor_negative_fees(self, db_session: AsyncSession):
        """Test that doctor creation fails with negative fees"""
        with pytest.raises(ValueError, match="fee"):
            await doctor_crud.create_doctor(
                db=db_session,
                name="Dr. Smith",
                department="Cardiology",
                new_patient_fee=Decimal("-100.00"),
                followup_fee=Decimal("300.00")
            )
    
    @pytest.mark.asyncio
    async def test_patient_whitespace_only_name(self, db_session: AsyncSession):
        """Test that patient creation fails with whitespace-only name"""
        with pytest.raises(ValueError, match="name"):
            await patient_crud.create_patient(
                db=db_session,
                name="   ",
                age=30,
                gender=Gender.MALE,
                address="123 Test St",
                mobile_number="9876543210"
            )
    
    @pytest.mark.asyncio
    async def test_patient_age_boundary_valid(self, db_session: AsyncSession):
        """Test that patient creation succeeds with boundary age values"""
        # Test age 0
        patient1 = await patient_crud.create_patient(
            db=db_session,
            name="Baby Doe",
            age=0,
            gender=Gender.MALE,
            address="123 Test St",
            mobile_number="9876543210"
        )
        assert patient1.age == 0
        
        # Test age 150
        patient2 = await patient_crud.create_patient(
            db=db_session,
            name="Old Doe",
            age=150,
            gender=Gender.FEMALE,
            address="456 Test Ave",
            mobile_number="9876543211"
        )
        assert patient2.age == 150
    
    @pytest.mark.asyncio
    async def test_patient_age_boundary_invalid(self, db_session: AsyncSession):
        """Test that patient creation fails with out-of-bounds age"""
        # Test age 151
        with pytest.raises(ValueError, match="[Aa]ge"):
            await patient_crud.create_patient(
                db=db_session,
                name="Too Old",
                age=151,
                gender=Gender.MALE,
                address="123 Test St",
                mobile_number="9876543210"
            )
    
    @pytest.mark.asyncio
    async def test_doctor_zero_fees_valid(self, db_session: AsyncSession):
        """Test that doctor creation succeeds with zero fees"""
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Free",
            department="Charity",
            new_patient_fee=Decimal("0.00"),
            followup_fee=Decimal("0.00")
        )
        assert doctor.new_patient_fee == Decimal("0.00")
        assert doctor.followup_fee == Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_patient_duplicate_mobile_rejected(self, db_session: AsyncSession):
        """Test that duplicate mobile numbers are rejected"""
        # Create first patient
        await patient_crud.create_patient(
            db=db_session,
            name="John Doe",
            age=30,
            gender=Gender.MALE,
            address="123 Test St",
            mobile_number="9876543210"
        )
        
        # Attempt to create second patient with same mobile
        with pytest.raises(ValueError, match="[Mm]obile"):
            await patient_crud.create_patient(
                db=db_session,
                name="Jane Doe",
                age=25,
                gender=Gender.FEMALE,
                address="456 Test Ave",
                mobile_number="9876543210"  # Duplicate
            )
    
    @pytest.mark.asyncio
    async def test_patient_valid_mobile_formats(self, db_session: AsyncSession):
        """Test that valid Indian mobile number formats are accepted"""
        valid_mobiles = ["9876543210", "8765432109", "7654321098", "6543210987"]
        
        for i, mobile in enumerate(valid_mobiles):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=30,
                gender=Gender.MALE,
                address="123 Test St",
                mobile_number=mobile
            )
            assert patient.mobile_number == mobile
    
    @pytest.mark.asyncio
    async def test_patient_invalid_mobile_start_digit(self, db_session: AsyncSession):
        """Test that mobile numbers starting with invalid digits are rejected"""
        invalid_mobiles = ["0123456789", "1234567890", "5432109876"]
        
        for mobile in invalid_mobiles:
            with pytest.raises(ValueError, match="mobile"):
                await patient_crud.create_patient(
                    db=db_session,
                    name="Test Patient",
                    age=30,
                    gender=Gender.MALE,
                    address="123 Test St",
                    mobile_number=mobile
                )
