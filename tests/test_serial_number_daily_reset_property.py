"""
Property-based tests for serial number daily reset

**Feature: hospital-management-system, Property 5: Serial Number Daily Reset**
**Validates: Requirements 1.8**
"""

import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from decimal import Decimal
from datetime import date, time, datetime, timedelta

from app.models.doctor import Doctor, DoctorStatus
from app.models.patient import Patient, Gender
from app.models.visit import Visit, VisitType, PaymentMode, VisitStatus
from app.crud.doctor import doctor_crud
from app.crud.patient import patient_crud
from app.crud.visit import visit_crud


# Strategy for generating valid doctor data
@st.composite
def valid_doctor_data(draw):
    """Generate valid doctor data"""
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


class TestSerialNumberDailyResetProperty:
    """Property-based tests for serial number daily reset"""
    
    @given(
        doctor_data=valid_doctor_data(),
        num_visits_day1=st.integers(min_value=5, max_value=20),
        num_visits_day2=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_serial_number_daily_reset_property(
        self,
        db_session: AsyncSession,
        doctor_data: Dict[str, Any],
        num_visits_day1: int,
        num_visits_day2: int
    ):
        """
        Property: For any doctor on any given date, serial numbers should start from 1 
        and increment sequentially, resetting to 1 on the next date.
        
        **Validates: Requirements 1.8**
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
        
        # Use two different dates
        day1 = date.today()
        day2 = date.today() + timedelta(days=1)
        
        # Generate unique mobile base
        import time
        import random
        base_timestamp = int(time.time() * 1000) % 100000000
        
        # Create visits for day 1
        day1_visits = []
        for i in range(num_visits_day1):
            mobile = f"9{(base_timestamp + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient Day1 {i}",
                age=25 + (i % 50),
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=mobile
            )
            
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                visit_type=VisitType.OPD_NEW,
                payment_mode=PaymentMode.CASH,
                visit_date=day1
            )
            day1_visits.append(visit)
        
        # CRITICAL PROPERTY 1: Day 1 serial numbers should start from 1 and increment sequentially
        day1_serials = [v.serial_number for v in day1_visits]
        expected_day1_serials = list(range(1, num_visits_day1 + 1))
        
        assert day1_serials == expected_day1_serials, (
            f"Day 1 serial numbers should be sequential starting from 1. "
            f"Expected {expected_day1_serials}, got {day1_serials}"
        )
        
        # Create visits for day 2
        day2_visits = []
        for i in range(num_visits_day2):
            mobile = f"9{(base_timestamp + num_visits_day1 + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient Day2 {i}",
                age=25 + (i % 50),
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=mobile
            )
            
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                visit_type=VisitType.OPD_NEW,
                payment_mode=PaymentMode.CASH,
                visit_date=day2
            )
            day2_visits.append(visit)
        
        # CRITICAL PROPERTY 2: Day 2 serial numbers should RESET to 1 and increment sequentially
        day2_serials = [v.serial_number for v in day2_visits]
        expected_day2_serials = list(range(1, num_visits_day2 + 1))
        
        assert day2_serials == expected_day2_serials, (
            f"Day 2 serial numbers should RESET to 1 and be sequential. "
            f"Expected {expected_day2_serials}, got {day2_serials}"
        )
        
        # CRITICAL PROPERTY 3: First serial number on day 2 should be 1 (reset verification)
        assert day2_visits[0].serial_number == 1, (
            f"First visit on day 2 should have serial number 1 (reset), "
            f"but got {day2_visits[0].serial_number}"
        )
    
    @given(
        num_doctors=st.integers(min_value=2, max_value=5),
        num_visits_per_doctor=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_serial_number_per_doctor_independence_property(
        self,
        db_session: AsyncSession,
        num_doctors: int,
        num_visits_per_doctor: int
    ):
        """
        Property: For any set of doctors on the same date, each doctor should have 
        independent serial number sequences starting from 1.
        
        **Validates: Requirements 1.8**
        """
        departments = ["Cardiology", "Neurology", "Orthopedics", "Pediatrics", "General Medicine"]
        doctors = []
        
        # Create multiple doctors
        for i in range(num_doctors):
            doctor = await doctor_crud.create_doctor(
                db=db_session,
                name=f"Dr. Test {i}",
                department=departments[i % len(departments)],
                new_patient_fee=Decimal("500.00"),
                followup_fee=Decimal("300.00"),
                status=DoctorStatus.ACTIVE
            )
            doctors.append(doctor)
        
        # Use same date for all visits
        visit_date = date.today()
        
        # Generate unique mobile base
        import time
        base_timestamp = int(time.time() * 1000) % 100000000
        
        # Create visits for each doctor
        doctor_visits = {}
        mobile_counter = 0
        
        for doctor in doctors:
            visits = []
            for j in range(num_visits_per_doctor):
                mobile = f"9{(base_timestamp + mobile_counter) % 1000000000:09d}"
                mobile_counter += 1
                
                patient = await patient_crud.create_patient(
                    db=db_session,
                    name=f"Patient {doctor.doctor_id} {j}",
                    age=30,
                    gender=Gender.MALE,
                    address="Test Address",
                    mobile_number=mobile
                )
                
                visit = await visit_crud.create_visit(
                    db=db_session,
                    patient_id=patient.patient_id,
                    doctor_id=doctor.doctor_id,
                    visit_type=VisitType.OPD_NEW,
                    payment_mode=PaymentMode.CASH,
                    visit_date=visit_date
                )
                visits.append(visit)
            
            doctor_visits[doctor.doctor_id] = visits
        
        # CRITICAL PROPERTY: Each doctor should have independent serial numbers starting from 1
        for doctor_id, visits in doctor_visits.items():
            serials = [v.serial_number for v in visits]
            expected_serials = list(range(1, num_visits_per_doctor + 1))
            
            assert serials == expected_serials, (
                f"Doctor {doctor_id} should have serial numbers {expected_serials}, "
                f"but got {serials}. Serial numbers should be independent per doctor."
            )
            
            # Verify first serial is 1
            assert visits[0].serial_number == 1, (
                f"First visit for doctor {doctor_id} should have serial number 1"
            )
    
    @given(
        doctor_data=valid_doctor_data(),
        num_days=st.integers(min_value=3, max_value=7),
        visits_per_day=st.integers(min_value=2, max_value=8)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_serial_number_multi_day_reset_property(
        self,
        db_session: AsyncSession,
        doctor_data: Dict[str, Any],
        num_days: int,
        visits_per_day: int
    ):
        """
        Property: For any doctor across multiple consecutive days, serial numbers 
        should reset to 1 at the start of each new day.
        
        **Validates: Requirements 1.8**
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
        
        # Generate unique mobile base
        import time
        base_timestamp = int(time.time() * 1000) % 100000000
        mobile_counter = 0
        
        # Create visits across multiple days
        all_visits_by_day = {}
        
        for day_offset in range(num_days):
            visit_date = date.today() + timedelta(days=day_offset)
            day_visits = []
            
            for i in range(visits_per_day):
                mobile = f"9{(base_timestamp + mobile_counter) % 1000000000:09d}"
                mobile_counter += 1
                
                patient = await patient_crud.create_patient(
                    db=db_session,
                    name=f"Patient Day{day_offset} Visit{i}",
                    age=25 + (i % 50),
                    gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                    address=f"Address {i}",
                    mobile_number=mobile
                )
                
                visit = await visit_crud.create_visit(
                    db=db_session,
                    patient_id=patient.patient_id,
                    doctor_id=doctor.doctor_id,
                    visit_type=VisitType.OPD_NEW,
                    payment_mode=PaymentMode.CASH,
                    visit_date=visit_date
                )
                day_visits.append(visit)
            
            all_visits_by_day[visit_date] = day_visits
        
        # CRITICAL PROPERTY: Each day should have serial numbers starting from 1
        for visit_date, visits in all_visits_by_day.items():
            serials = [v.serial_number for v in visits]
            expected_serials = list(range(1, visits_per_day + 1))
            
            assert serials == expected_serials, (
                f"Date {visit_date} should have serial numbers {expected_serials}, "
                f"but got {serials}. Serial numbers should reset daily."
            )
            
            # Verify first serial is always 1
            assert visits[0].serial_number == 1, (
                f"First visit on {visit_date} should have serial number 1 (daily reset)"
            )
    
    @given(
        doctor_data=valid_doctor_data(),
        num_visits=st.integers(min_value=10, max_value=30)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_serial_number_sequential_increment_property(
        self,
        db_session: AsyncSession,
        doctor_data: Dict[str, Any],
        num_visits: int
    ):
        """
        Property: For any doctor on a single day, serial numbers should increment 
        by exactly 1 for each consecutive visit.
        
        **Validates: Requirements 1.8**
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
        
        visit_date = date.today()
        
        # Generate unique mobile base
        import time
        base_timestamp = int(time.time() * 1000) % 100000000
        
        # Create visits
        visits = []
        for i in range(num_visits):
            mobile = f"9{(base_timestamp + i) % 1000000000:09d}"
            
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=25 + (i % 50),
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=mobile
            )
            
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                visit_type=VisitType.OPD_NEW,
                payment_mode=PaymentMode.CASH,
                visit_date=visit_date
            )
            visits.append(visit)
        
        # CRITICAL PROPERTY 1: Serial numbers should be consecutive integers
        serials = [v.serial_number for v in visits]
        for i in range(len(serials) - 1):
            assert serials[i + 1] == serials[i] + 1, (
                f"Serial numbers should increment by 1. "
                f"Visit {i} has serial {serials[i]}, visit {i+1} has serial {serials[i+1]}"
            )
        
        # CRITICAL PROPERTY 2: No gaps in serial numbers
        expected_serials = list(range(1, num_visits + 1))
        assert serials == expected_serials, (
            f"Serial numbers should be {expected_serials} with no gaps, "
            f"but got {serials}"
        )
        
        # CRITICAL PROPERTY 3: First serial is 1
        assert visits[0].serial_number == 1, (
            f"First visit should have serial number 1, got {visits[0].serial_number}"
        )
        
        # CRITICAL PROPERTY 4: Last serial equals number of visits
        assert visits[-1].serial_number == num_visits, (
            f"Last visit should have serial number {num_visits}, "
            f"got {visits[-1].serial_number}"
        )
    
    @given(
        num_doctors=st.integers(min_value=2, max_value=4),
        num_days=st.integers(min_value=2, max_value=4),
        visits_per_doctor_per_day=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_serial_number_complex_scenario_property(
        self,
        db_session: AsyncSession,
        num_doctors: int,
        num_days: int,
        visits_per_doctor_per_day: int
    ):
        """
        Property: For any combination of multiple doctors across multiple days, 
        each doctor's serial numbers should reset daily and be independent of other doctors.
        
        **Validates: Requirements 1.8**
        """
        departments = ["Cardiology", "Neurology", "Orthopedics", "Pediatrics"]
        doctors = []
        
        # Create doctors
        for i in range(num_doctors):
            doctor = await doctor_crud.create_doctor(
                db=db_session,
                name=f"Dr. Complex {i}",
                department=departments[i % len(departments)],
                new_patient_fee=Decimal("500.00"),
                followup_fee=Decimal("300.00"),
                status=DoctorStatus.ACTIVE
            )
            doctors.append(doctor)
        
        # Generate unique mobile base
        import time
        base_timestamp = int(time.time() * 1000) % 100000000
        mobile_counter = 0
        
        # Track visits by doctor and date
        visits_by_doctor_and_date = {}
        
        # Create visits for each doctor on each day
        for day_offset in range(num_days):
            visit_date = date.today() + timedelta(days=day_offset)
            
            for doctor in doctors:
                key = (doctor.doctor_id, visit_date)
                visits = []
                
                for i in range(visits_per_doctor_per_day):
                    mobile = f"9{(base_timestamp + mobile_counter) % 1000000000:09d}"
                    mobile_counter += 1
                    
                    patient = await patient_crud.create_patient(
                        db=db_session,
                        name=f"Patient D{doctors.index(doctor)} Day{day_offset} V{i}",
                        age=30,
                        gender=Gender.MALE,
                        address="Test Address",
                        mobile_number=mobile
                    )
                    
                    visit = await visit_crud.create_visit(
                        db=db_session,
                        patient_id=patient.patient_id,
                        doctor_id=doctor.doctor_id,
                        visit_type=VisitType.OPD_NEW,
                        payment_mode=PaymentMode.CASH,
                        visit_date=visit_date
                    )
                    visits.append(visit)
                
                visits_by_doctor_and_date[key] = visits
        
        # CRITICAL PROPERTY: Each doctor-date combination should have serial numbers 1 to N
        for (doctor_id, visit_date), visits in visits_by_doctor_and_date.items():
            serials = [v.serial_number for v in visits]
            expected_serials = list(range(1, visits_per_doctor_per_day + 1))
            
            assert serials == expected_serials, (
                f"Doctor {doctor_id} on {visit_date} should have serial numbers {expected_serials}, "
                f"but got {serials}. Serial numbers should reset daily per doctor."
            )
            
            # Verify first serial is always 1
            assert visits[0].serial_number == 1, (
                f"First visit for doctor {doctor_id} on {visit_date} should have serial number 1"
            )


class TestSerialNumberDailyResetExamples:
    """Unit tests for specific serial number daily reset scenarios"""
    
    @pytest.mark.asyncio
    async def test_serial_number_starts_at_one(self, db_session: AsyncSession):
        """Test that serial number starts at 1 for first visit of the day"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Serial",
            department="Cardiology",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="First Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543210"
        )
        
        # Create first visit of the day
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Verify serial number is 1
        assert visit.serial_number == 1
    
    @pytest.mark.asyncio
    async def test_serial_number_increments_sequentially(self, db_session: AsyncSession):
        """Test that serial numbers increment sequentially on the same day"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Sequential",
            department="Neurology",
            new_patient_fee=Decimal("600.00"),
            followup_fee=Decimal("400.00")
        )
        
        visit_date = date.today()
        visits = []
        
        # Create 5 visits on the same day
        for i in range(5):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=25 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=f"987654321{i}"
            )
            
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                visit_type=VisitType.OPD_NEW,
                payment_mode=PaymentMode.CASH,
                visit_date=visit_date
            )
            visits.append(visit)
        
        # Verify serial numbers are 1, 2, 3, 4, 5
        serials = [v.serial_number for v in visits]
        assert serials == [1, 2, 3, 4, 5]
    
    @pytest.mark.asyncio
    async def test_serial_number_resets_next_day(self, db_session: AsyncSession):
        """Test that serial numbers reset to 1 on the next day"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Reset",
            department="Orthopedics",
            new_patient_fee=Decimal("700.00"),
            followup_fee=Decimal("500.00")
        )
        
        day1 = date.today()
        day2 = date.today() + timedelta(days=1)
        
        # Create 3 visits on day 1
        day1_visits = []
        for i in range(3):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient Day1 {i}",
                age=30 + i,
                gender=Gender.MALE,
                address=f"Address {i}",
                mobile_number=f"987654320{i}"
            )
            
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                visit_type=VisitType.OPD_NEW,
                payment_mode=PaymentMode.CASH,
                visit_date=day1
            )
            day1_visits.append(visit)
        
        # Verify day 1 serials are 1, 2, 3
        day1_serials = [v.serial_number for v in day1_visits]
        assert day1_serials == [1, 2, 3]
        
        # Create 3 visits on day 2
        day2_visits = []
        for i in range(3):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient Day2 {i}",
                age=40 + i,
                gender=Gender.FEMALE,
                address=f"Address Day2 {i}",
                mobile_number=f"987654321{i}"
            )
            
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                visit_type=VisitType.OPD_NEW,
                payment_mode=PaymentMode.CASH,
                visit_date=day2
            )
            day2_visits.append(visit)
        
        # Verify day 2 serials RESET to 1, 2, 3
        day2_serials = [v.serial_number for v in day2_visits]
        assert day2_serials == [1, 2, 3]
        
        # Verify first visit on day 2 has serial 1 (reset)
        assert day2_visits[0].serial_number == 1
    
    @pytest.mark.asyncio
    async def test_serial_number_independent_per_doctor(self, db_session: AsyncSession):
        """Test that serial numbers are independent for different doctors on the same day"""
        # Create two doctors
        doctor1 = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. One",
            department="Cardiology",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        doctor2 = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Two",
            department="Neurology",
            new_patient_fee=Decimal("600.00"),
            followup_fee=Decimal("400.00")
        )
        
        visit_date = date.today()
        
        # Create 3 visits for doctor 1
        doctor1_visits = []
        for i in range(3):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient D1 {i}",
                age=30 + i,
                gender=Gender.MALE,
                address=f"Address {i}",
                mobile_number=f"987654330{i}"
            )
            
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor1.doctor_id,
                visit_type=VisitType.OPD_NEW,
                payment_mode=PaymentMode.CASH,
                visit_date=visit_date
            )
            doctor1_visits.append(visit)
        
        # Create 3 visits for doctor 2
        doctor2_visits = []
        for i in range(3):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient D2 {i}",
                age=40 + i,
                gender=Gender.FEMALE,
                address=f"Address D2 {i}",
                mobile_number=f"987654331{i}"
            )
            
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor2.doctor_id,
                visit_type=VisitType.OPD_NEW,
                payment_mode=PaymentMode.CASH,
                visit_date=visit_date
            )
            doctor2_visits.append(visit)
        
        # Verify both doctors have independent serial numbers starting from 1
        doctor1_serials = [v.serial_number for v in doctor1_visits]
        doctor2_serials = [v.serial_number for v in doctor2_visits]
        
        assert doctor1_serials == [1, 2, 3]
        assert doctor2_serials == [1, 2, 3]
    
    @pytest.mark.asyncio
    async def test_serial_number_across_multiple_days(self, db_session: AsyncSession):
        """Test that serial numbers reset correctly across multiple consecutive days"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. MultiDay",
            department="Pediatrics",
            new_patient_fee=Decimal("400.00"),
            followup_fee=Decimal("250.00")
        )
        
        # Create visits across 3 consecutive days
        for day_offset in range(3):
            visit_date = date.today() + timedelta(days=day_offset)
            
            # Create 2 visits per day
            for i in range(2):
                patient = await patient_crud.create_patient(
                    db=db_session,
                    name=f"Patient Day{day_offset} Visit{i}",
                    age=25 + i,
                    gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                    address=f"Address {day_offset}-{i}",
                    mobile_number=f"98765434{day_offset}{i}"
                )
                
                visit = await visit_crud.create_visit(
                    db=db_session,
                    patient_id=patient.patient_id,
                    doctor_id=doctor.doctor_id,
                    visit_type=VisitType.OPD_NEW,
                    payment_mode=PaymentMode.CASH,
                    visit_date=visit_date
                )
                
                # Verify serial number is correct for each day
                expected_serial = i + 1
                assert visit.serial_number == expected_serial, (
                    f"Day {day_offset}, visit {i} should have serial {expected_serial}, "
                    f"got {visit.serial_number}"
                )
    
    @pytest.mark.asyncio
    async def test_serial_number_with_followup_visits(self, db_session: AsyncSession):
        """Test that serial numbers work correctly with both new and follow-up visits"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Followup",
            department="General Medicine",
            new_patient_fee=Decimal("300.00"),
            followup_fee=Decimal("200.00")
        )
        
        visit_date = date.today()
        
        # Create 2 new visits
        patient1 = await patient_crud.create_patient(
            db=db_session,
            name="Patient New 1",
            age=30,
            gender=Gender.MALE,
            address="Address 1",
            mobile_number="9876543350"
        )
        
        visit1 = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient1.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH,
            visit_date=visit_date
        )
        
        patient2 = await patient_crud.create_patient(
            db=db_session,
            name="Patient New 2",
            age=35,
            gender=Gender.FEMALE,
            address="Address 2",
            mobile_number="9876543351"
        )
        
        visit2 = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient2.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH,
            visit_date=visit_date
        )
        
        # Create 1 follow-up visit
        visit3 = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient1.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_FOLLOWUP,
            payment_mode=PaymentMode.UPI,
            visit_date=visit_date
        )
        
        # Verify serial numbers are sequential regardless of visit type
        assert visit1.serial_number == 1
        assert visit2.serial_number == 2
        assert visit3.serial_number == 3
    
    @pytest.mark.asyncio
    async def test_serial_number_no_gaps(self, db_session: AsyncSession):
        """Test that serial numbers have no gaps in sequence"""
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. NoGaps",
            department="Surgery",
            new_patient_fee=Decimal("1000.00"),
            followup_fee=Decimal("700.00")
        )
        
        visit_date = date.today()
        
        # Create 10 visits
        visits = []
        for i in range(10):
            patient = await patient_crud.create_patient(
                db=db_session,
                name=f"Patient {i}",
                age=25 + i,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                address=f"Address {i}",
                mobile_number=f"987654336{i}"
            )
            
            visit = await visit_crud.create_visit(
                db=db_session,
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                visit_type=VisitType.OPD_NEW,
                payment_mode=PaymentMode.CASH,
                visit_date=visit_date
            )
            visits.append(visit)
        
        # Verify no gaps in serial numbers
        serials = [v.serial_number for v in visits]
        expected = list(range(1, 11))
        assert serials == expected, f"Expected {expected}, got {serials}"
