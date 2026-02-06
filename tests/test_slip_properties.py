"""
Property-based tests for slip generation and barcode system

**Feature: hospital-management-system**

Property 6: Comprehensive Slip Content Validation
Property 11: Barcode Content Validation  
Property 12: Barcode-Record Mapping

**Validates: Requirements 1.6, 2.5, 3.5, 4.5, 5.4, 6.3, 7.1, 7.2, 10.2, 10.3, 17.1, 17.2, 17.3, 17.4, 17.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json

from app.crud.slip import slip_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.crud.billing import billing_crud
from app.models.patient import Gender
from app.models.visit import VisitType, PaymentMode
from app.models.bed import WardType
from app.models.slip import PrinterFormat, SlipType
from app.models.billing import ChargeType


def generate_unique_mobile():
    """Generate a unique 10-digit mobile number starting with 9"""
    return "9" + str(uuid.uuid4().int)[:9]


# Strategies
printer_format_strategy = st.sampled_from([PrinterFormat.A4, PrinterFormat.THERMAL])


class TestSlipContentValidation:
    """Property 6: Comprehensive Slip Content Validation"""
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(printer_format=printer_format_strategy)
    async def test_opd_slip_contains_required_content(
        self,
        db_session: AsyncSession,
        printer_format: PrinterFormat
    ):
        """
        Property: OPD slips should contain hospital header, patient details, 
        visit details, doctor info, charges, and barcode
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Test",
            department="General",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        # Create visit
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Generate slip
        slip = await slip_crud.generate_opd_slip(
            db=db_session,
            visit_id=visit.visit_id,
            printer_format=printer_format,
            generated_by="test_user"
        )
        
        # Parse slip content
        content = json.loads(slip.slip_content)
        
        # Verify hospital header
        assert "hospital_name" in content
        assert content["hospital_name"] is not None
        
        # Verify patient details
        assert "patient" in content
        assert content["patient"]["id"] == patient.patient_id
        assert content["patient"]["name"] == patient.name
        assert content["patient"]["age"] == patient.age
        assert content["patient"]["gender"] == patient.gender.value
        assert content["patient"]["mobile"] == patient.mobile_number
        
        # Verify visit details
        assert "visit" in content
        assert content["visit"]["id"] == visit.visit_id
        assert content["visit"]["serial_number"] == visit.serial_number
        
        # Verify doctor info
        assert "doctor" in content
        assert content["doctor"]["name"] == doctor.name
        assert content["doctor"]["department"] == visit.department
        
        # Verify charges
        assert "charges" in content
        assert content["charges"]["opd_fee"] == float(visit.opd_fee)
        
        # Verify barcode
        assert "barcode_data" in content
        assert content["barcode_data"] is not None
        assert slip.barcode_data is not None
        assert slip.barcode_image is not None
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(printer_format=printer_format_strategy)
    async def test_discharge_slip_contains_complete_bill(
        self,
        db_session: AsyncSession,
        printer_format: PrinterFormat
    ):
        """
        Property: Discharge slips should contain all charges, payments, and summary
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
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
        
        # Add some charges
        await billing_crud.create_charge(
            db=db_session,
            ipd_id=ipd.ipd_id,
            charge_type=ChargeType.INVESTIGATION,
            charge_name="X-Ray",
            rate=Decimal("500.00"),
            quantity=1,
            created_by="test_user"
        )
        
        # Generate discharge slip
        slip = await slip_crud.generate_discharge_slip(
            db=db_session,
            ipd_id=ipd.ipd_id,
            printer_format=printer_format,
            generated_by="test_user"
        )
        
        # Parse slip content
        content = json.loads(slip.slip_content)
        
        # Verify hospital header
        assert "hospital_name" in content
        
        # Verify patient details
        assert "patient" in content
        assert content["patient"]["id"] == patient.patient_id
        
        # Verify IPD details
        assert "ipd" in content
        assert content["ipd"]["id"] == ipd.ipd_id
        assert content["ipd"]["file_charge"] == float(ipd.file_charge)
        
        # Verify charges by type
        assert "charges_by_type" in content
        
        # Verify summary
        assert "summary" in content
        assert "total_charges" in content["summary"]
        assert "total_paid" in content["summary"]
        assert "balance_due" in content["summary"]
        
        # Verify barcode
        assert "barcode_data" in content
        assert slip.barcode_data is not None


class TestBarcodeContentValidation:
    """Property 11: Barcode Content Validation"""
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(printer_format=printer_format_strategy)
    async def test_barcode_contains_patient_and_visit_id(
        self,
        db_session: AsyncSession,
        printer_format: PrinterFormat
    ):
        """
        Property: Barcodes should contain Patient_ID and Visit_ID in correct format
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Test",
            department="General",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        # Create visit
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Generate slip
        slip = await slip_crud.generate_opd_slip(
            db=db_session,
            visit_id=visit.visit_id,
            printer_format=printer_format,
            generated_by="test_user"
        )
        
        # Verify barcode format: {PatientID}-{VisitID}-{Timestamp}
        barcode_parts = slip.barcode_data.split("-")
        assert len(barcode_parts) >= 3
        assert barcode_parts[0] == patient.patient_id
        assert barcode_parts[1] == visit.visit_id
        # Third part is timestamp
        assert barcode_parts[2].isdigit()
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(printer_format=printer_format_strategy)
    async def test_barcode_contains_patient_and_ipd_id(
        self,
        db_session: AsyncSession,
        printer_format: PrinterFormat
    ):
        """
        Property: Barcodes for IPD should contain Patient_ID and IPD_ID
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number=f"BED{generate_unique_mobile()[:6]}",
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
        
        # Generate discharge slip
        slip = await slip_crud.generate_discharge_slip(
            db=db_session,
            ipd_id=ipd.ipd_id,
            printer_format=printer_format,
            generated_by="test_user"
        )
        
        # Verify barcode format
        barcode_parts = slip.barcode_data.split("-")
        assert len(barcode_parts) >= 3
        assert barcode_parts[0] == patient.patient_id
        assert barcode_parts[1] == ipd.ipd_id
        assert barcode_parts[2].isdigit()


class TestBarcodeRecordMapping:
    """Property 12: Barcode-Record Mapping"""
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(printer_format=printer_format_strategy)
    async def test_barcode_maps_to_correct_patient_record(
        self,
        db_session: AsyncSession,
        printer_format: PrinterFormat
    ):
        """
        Property: Barcode data should correctly map back to patient record
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Test",
            department="General",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        # Create visit
        visit = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        # Generate slip
        slip = await slip_crud.generate_opd_slip(
            db=db_session,
            visit_id=visit.visit_id,
            printer_format=printer_format,
            generated_by="test_user"
        )
        
        # Extract patient_id from barcode
        barcode_parts = slip.barcode_data.split("-")
        extracted_patient_id = barcode_parts[0]
        extracted_visit_id = barcode_parts[1]
        
        # Verify mapping
        assert extracted_patient_id == patient.patient_id
        assert extracted_visit_id == visit.visit_id
        
        # Verify we can retrieve the slip using the barcode data
        retrieved_slip = await slip_crud.get_slip_by_id(db_session, slip.slip_id)
        assert retrieved_slip is not None
        assert retrieved_slip.barcode_data == slip.barcode_data
        assert retrieved_slip.patient_id == patient.patient_id
        assert retrieved_slip.visit_id == visit.visit_id
    
    @pytest.mark.asyncio
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(printer_format=printer_format_strategy)
    async def test_multiple_slips_have_unique_barcodes(
        self,
        db_session: AsyncSession,
        printer_format: PrinterFormat
    ):
        """
        Property: Each slip should have a unique barcode even for same patient
        """
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=30,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number=generate_unique_mobile()
        )
        
        # Create doctor
        doctor = await doctor_crud.create_doctor(
            db=db_session,
            name="Dr. Test",
            department="General",
            new_patient_fee=Decimal("500.00"),
            followup_fee=Decimal("300.00")
        )
        
        # Create two visits
        visit1 = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )
        
        visit2 = await visit_crud.create_visit(
            db=db_session,
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            visit_type=VisitType.OPD_FOLLOWUP,
            payment_mode=PaymentMode.CASH
        )
        
        # Generate slips
        slip1 = await slip_crud.generate_opd_slip(
            db=db_session,
            visit_id=visit1.visit_id,
            printer_format=printer_format,
            generated_by="test_user"
        )
        
        slip2 = await slip_crud.generate_opd_slip(
            db=db_session,
            visit_id=visit2.visit_id,
            printer_format=printer_format,
            generated_by="test_user"
        )
        
        # Verify barcodes are different
        assert slip1.barcode_data != slip2.barcode_data
        assert slip1.slip_id != slip2.slip_id
        
        # Both should map to same patient but different visits
        assert slip1.patient_id == slip2.patient_id == patient.patient_id
        assert slip1.visit_id != slip2.visit_id
