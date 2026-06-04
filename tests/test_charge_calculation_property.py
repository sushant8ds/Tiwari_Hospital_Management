"""
Property-based tests for charge calculation accuracy

**Feature: hospital-management-system, Property 7: Charge Calculation Accuracy**
**Validates: Requirements 2.2, 3.4, 6.1, 6.2**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from decimal import Decimal
from datetime import datetime, timedelta

from app.models.patient import Patient, Gender
from app.models.doctor import Doctor, DoctorStatus
from app.models.visit import Visit, VisitType, PaymentMode
from app.models.billing import BillingCharge, ChargeType
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.billing import billing_crud


# Strategy for generating valid charge data
@st.composite
def valid_charge_data(draw):
    """Generate valid charge data"""
    return {
        "name": draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        "rate": Decimal(str(draw(st.floats(min_value=10, max_value=5000, allow_nan=False, allow_infinity=False)))),
        "quantity": draw(st.integers(min_value=1, max_value=10))
    }


class TestChargeCalculationAccuracyProperty:
    """Property-based tests for charge calculation accuracy"""
    
    @given(
        num_investigations=st.integers(min_value=1, max_value=5),
        num_procedures=st.integers(min_value=1, max_value=5),
        num_services=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_total_equals_sum_of_charges_property(
        self,
        db_session: AsyncSession,
        num_investigations: int,
        num_procedures: int,
        num_services: int
    ):
        """
        Property: For any billing operation, the total amount should equal 
        the sum of all individual charges.
        
        **Validates: Requirements 2.2, 3.4, 6.1, 6.2**
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
        
        # Track expected total
        expected_total = Decimal("0")
        all_charges = []
        
        # Add investigation charges
        for i in range(num_investigations):
            rate = Decimal(str(100 + (i * 50)))
            quantity = 1 + (i % 3)
            
            charge = await billing_crud.create_charge(
                db=db_session,
                charge_type=ChargeType.INVESTIGATION,
                charge_name=f"Investigation {i}",
                rate=rate,
                quantity=quantity,
                visit_id=visit.visit_id,
                created_by="test_user"
            )
            all_charges.append(charge)
            expected_total += rate * quantity
        
        # Add procedure charges
        for i in range(num_procedures):
            rate = Decimal(str(200 + (i * 100)))
            quantity = 1 + (i % 4)
            
            charge = await billing_crud.create_charge(
                db=db_session,
                charge_type=ChargeType.PROCEDURE,
                charge_name=f"Procedure {i}",
                rate=rate,
                quantity=quantity,
                visit_id=visit.visit_id,
                created_by="test_user"
            )
            all_charges.append(charge)
            expected_total += rate * quantity
        
        # Add service charges
        for i in range(num_services):
            rate = Decimal(str(150 + (i * 50)))
            quantity = 2 + (i % 5)
            
            charge = await billing_crud.create_charge(
                db=db_session,
                charge_type=ChargeType.SERVICE,
                charge_name=f"Service {i}",
                rate=rate,
                quantity=quantity,
                visit_id=visit.visit_id,
                created_by="test_user"
            )
            all_charges.append(charge)
            expected_total += rate * quantity
        
        # CRITICAL PROPERTY 1: Calculate total using CRUD method
        calculated_total = await billing_crud.calculate_total_charges(
            db=db_session,
            visit_id=visit.visit_id
        )
        
        assert calculated_total == expected_total, (
            f"Calculated total {calculated_total} should equal expected total {expected_total}"
        )
        
        # CRITICAL PROPERTY 2: Verify each charge has correct total_amount
        for charge in all_charges:
            assert charge.total_amount == charge.rate * charge.quantity, (
                f"Charge {charge.charge_id} total_amount {charge.total_amount} should equal "
                f"rate {charge.rate} * quantity {charge.quantity} = {charge.rate * charge.quantity}"
            )
        
        # CRITICAL PROPERTY 3: Sum of individual charge totals equals calculated total
        sum_of_charges = sum(charge.total_amount for charge in all_charges)
        assert sum_of_charges == calculated_total, (
            f"Sum of individual charges {sum_of_charges} should equal calculated total {calculated_total}"
        )
    
    @given(
        service_hours=st.integers(min_value=1, max_value=24),
        hourly_rate=st.floats(min_value=50, max_value=500, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_service_time_calculation_accuracy_property(
        self,
        db_session: AsyncSession,
        service_hours: int,
        hourly_rate: float
    ):
        """
        Property: For any hourly service, the calculated hours should equal 
        the difference between end time and start time, and total should be hours * rate.
        
        **Validates: Requirements 3.4**
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
            department="Emergency",
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
        
        # Create service with time calculation
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=service_hours)
        # Quantize rate to 2 decimal places to match database precision
        rate = Decimal(str(hourly_rate)).quantize(Decimal("0.01"))
        
        services = [
            {
                "name": "Oxygen Service",
                "rate": hourly_rate,
                "start_time": start_time,
                "end_time": end_time
            }
        ]
        
        charges = await billing_crud.add_service_charges(
            db=db_session,
            visit_id=visit.visit_id,
            ipd_id=None,
            services=services,
            created_by="test_user"
        )
        
        assert len(charges) == 1, "Should create exactly one charge"
        charge = charges[0]
        
        # CRITICAL PROPERTY: Quantity should equal service hours
        assert charge.quantity == service_hours, (
            f"Service quantity {charge.quantity} should equal hours {service_hours}"
        )
        
        # CRITICAL PROPERTY: Total should equal hours * rate (quantized to 2 decimal places)
        expected_total = (rate * service_hours).quantize(Decimal("0.01"))
        assert charge.total_amount == expected_total, (
            f"Service total {charge.total_amount} should equal "
            f"hours {service_hours} * rate {rate} = {expected_total}"
        )
    
    @given(
        num_charges=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_mixed_charge_types_calculation_property(
        self,
        db_session: AsyncSession,
        num_charges: int
    ):
        """
        Property: For any mix of charge types, the total should equal 
        the sum of all individual charge totals.
        
        **Validates: Requirements 2.2, 6.1**
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
        
        # Create mixed charge types
        charge_types = [ChargeType.INVESTIGATION, ChargeType.PROCEDURE, ChargeType.SERVICE, ChargeType.MANUAL]
        expected_total = Decimal("0")
        
        for i in range(num_charges):
            charge_type = charge_types[i % len(charge_types)]
            rate = Decimal(str(100 + (i * 25)))
            quantity = 1 + (i % 5)
            
            charge = await billing_crud.create_charge(
                db=db_session,
                charge_type=charge_type,
                charge_name=f"Charge {i}",
                rate=rate,
                quantity=quantity,
                visit_id=visit.visit_id,
                created_by="test_user"
            )
            
            expected_total += rate * quantity
        
        # CRITICAL PROPERTY: Calculated total equals expected total
        calculated_total = await billing_crud.calculate_total_charges(
            db=db_session,
            visit_id=visit.visit_id
        )
        
        assert calculated_total == expected_total, (
            f"Calculated total {calculated_total} should equal expected total {expected_total}"
        )
    
    @given(
        initial_rate=st.floats(min_value=100, max_value=1000, allow_nan=False, allow_infinity=False),
        initial_quantity=st.integers(min_value=1, max_value=5),
        new_rate=st.floats(min_value=100, max_value=1000, allow_nan=False, allow_infinity=False),
        new_quantity=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_charge_update_recalculation_property(
        self,
        db_session: AsyncSession,
        initial_rate: float,
        initial_quantity: int,
        new_rate: float,
        new_quantity: int
    ):
        """
        Property: When a charge is updated, the total_amount should be 
        automatically recalculated as rate * quantity.
        
        **Validates: Requirements 2.2**
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
        
        # Create initial charge - quantize to 2 decimal places
        initial_rate_decimal = Decimal(str(initial_rate)).quantize(Decimal("0.01"))
        charge = await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="Test Charge",
            rate=initial_rate_decimal,
            quantity=initial_quantity,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
        
        # Verify initial calculation (quantized to 2 decimal places)
        expected_initial_total = (initial_rate_decimal * initial_quantity).quantize(Decimal("0.01"))
        assert charge.total_amount == expected_initial_total, (
            f"Initial total {charge.total_amount} should equal "
            f"{initial_rate_decimal} * {initial_quantity} = {expected_initial_total}"
        )
        
        # Update charge - quantize to 2 decimal places
        new_rate_decimal = Decimal(str(new_rate)).quantize(Decimal("0.01"))
        updated_charge = await billing_crud.update_charge(
            db=db_session,
            charge_id=charge.charge_id,
            rate=new_rate_decimal,
            quantity=new_quantity
        )
        
        # CRITICAL PROPERTY: Updated total should be recalculated (quantized to 2 decimal places)
        expected_new_total = (new_rate_decimal * new_quantity).quantize(Decimal("0.01"))
        assert updated_charge.total_amount == expected_new_total, (
            f"Updated total {updated_charge.total_amount} should equal "
            f"{new_rate_decimal} * {new_quantity} = {expected_new_total}"
        )
    
    @given(
        num_charges=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_no_rounding_errors_property(
        self,
        db_session: AsyncSession,
        num_charges: int
    ):
        """
        Property: For any set of charges, there should be no rounding errors 
        in the total calculation (using Decimal for precision).
        
        **Validates: Requirements 2.2, 6.1**
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
        
        # Create charges with decimal values
        expected_total = Decimal("0")
        
        for i in range(num_charges):
            # Use decimal values that might cause rounding errors with floats
            rate = Decimal(f"{100 + i}.{33 + (i * 7) % 100}")
            quantity = 1 + (i % 3)
            
            charge = await billing_crud.create_charge(
                db=db_session,
                charge_type=ChargeType.INVESTIGATION,
                charge_name=f"Charge {i}",
                rate=rate,
                quantity=quantity,
                visit_id=visit.visit_id,
                created_by="test_user"
            )
            
            expected_total += rate * quantity
        
        # CRITICAL PROPERTY: No rounding errors
        calculated_total = await billing_crud.calculate_total_charges(
            db=db_session,
            visit_id=visit.visit_id
        )
        
        assert calculated_total == expected_total, (
            f"Calculated total {calculated_total} should exactly equal expected total {expected_total} "
            f"(no rounding errors)"
        )


class TestChargeCalculationAccuracyExamples:
    """Unit tests for specific charge calculation scenarios"""
    
    @pytest.mark.asyncio
    async def test_single_charge_calculation(self, db_session: AsyncSession):
        """Test calculation for a single charge"""
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
        
        # Create single charge
        charge = await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="X-Ray",
            rate=Decimal("500.00"),
            quantity=1,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
        
        # Verify calculation
        assert charge.total_amount == Decimal("500.00")
        
        total = await billing_crud.calculate_total_charges(db_session, visit_id=visit.visit_id)
        assert total == Decimal("500.00")
    
    @pytest.mark.asyncio
    async def test_multiple_charges_sum(self, db_session: AsyncSession):
        """Test that multiple charges sum correctly"""
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
        
        # Create multiple charges
        await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="X-Ray",
            rate=Decimal("500.00"),
            quantity=1,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
        
        await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.PROCEDURE,
            charge_name="Dressing",
            rate=Decimal("200.00"),
            quantity=2,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
        
        await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.SERVICE,
            charge_name="Nursing",
            rate=Decimal("150.00"),
            quantity=3,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
        
        # Verify total: 500 + (200*2) + (150*3) = 500 + 400 + 450 = 1350
        total = await billing_crud.calculate_total_charges(db_session, visit_id=visit.visit_id)
        assert total == Decimal("1350.00")
    
    @pytest.mark.asyncio
    async def test_quantity_multiplication(self, db_session: AsyncSession):
        """Test that quantity is correctly multiplied by rate"""
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
        
        # Create charge with quantity > 1
        charge = await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.PROCEDURE,
            charge_name="Dressing",
            rate=Decimal("200.00"),
            quantity=5,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
        
        # Verify: 200 * 5 = 1000
        assert charge.total_amount == Decimal("1000.00")
    
    @pytest.mark.asyncio
    async def test_decimal_precision(self, db_session: AsyncSession):
        """Test that decimal precision is maintained"""
        # Create patient, doctor, and visit
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543213"
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
        
        # Create charge with decimal rate
        charge = await billing_crud.create_charge(
            db=db_session,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="Blood Test",
            rate=Decimal("123.45"),
            quantity=3,
            visit_id=visit.visit_id,
            created_by="test_user"
        )
        
        # Verify: 123.45 * 3 = 370.35
        assert charge.total_amount == Decimal("370.35")
