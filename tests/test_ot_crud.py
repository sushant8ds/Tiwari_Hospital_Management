"""
Tests for OT CRUD operations
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.ot import ot_crud
from app.crud.patient import patient_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.models.patient import Gender
from app.models.bed import WardType
from app.models.billing import ChargeType


class TestOTCrud:
    """Test OT CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_ot_procedure(self, db_session: AsyncSession):
        """Test creating an OT procedure"""
        # Create patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=45,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543210"
        )
        
        # Create bed
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="OT001",
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
        
        # Create OT procedure
        operation_date = datetime.now()
        ot_procedure = await ot_crud.create_ot_procedure(
            db=db_session,
            ipd_id=ipd.ipd_id,
            operation_name="Appendectomy",
            operation_date=operation_date,
            duration_minutes=120,
            surgeon_name="Dr. Smith",
            anesthesia_type="General",
            notes="Routine procedure",
            created_by="test_user"
        )
        
        assert ot_procedure.ot_id is not None
        assert ot_procedure.ipd_id == ipd.ipd_id
        assert ot_procedure.operation_name == "Appendectomy"
        assert ot_procedure.duration_minutes == 120
        assert ot_procedure.surgeon_name == "Dr. Smith"
        assert ot_procedure.anesthesia_type == "General"
        assert ot_procedure.notes == "Routine procedure"
    
    @pytest.mark.asyncio
    async def test_create_ot_procedure_invalid_ipd(self, db_session: AsyncSession):
        """Test creating OT procedure with invalid IPD ID"""
        with pytest.raises(ValueError, match="IPD record not found"):
            await ot_crud.create_ot_procedure(
                db=db_session,
                ipd_id="INVALID_IPD",
                operation_name="Test Operation",
                operation_date=datetime.now(),
                duration_minutes=60,
                surgeon_name="Dr. Test",
                created_by="test_user"
            )
    
    @pytest.mark.asyncio
    async def test_create_ot_procedure_empty_operation_name(self, db_session: AsyncSession):
        """Test creating OT procedure with empty operation name"""
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=45,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543211"
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="OT002",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        with pytest.raises(ValueError, match="Operation name is required"):
            await ot_crud.create_ot_procedure(
                db=db_session,
                ipd_id=ipd.ipd_id,
                operation_name="",
                operation_date=datetime.now(),
                duration_minutes=60,
                surgeon_name="Dr. Test",
                created_by="test_user"
            )
    
    @pytest.mark.asyncio
    async def test_add_ot_charges(self, db_session: AsyncSession):
        """Test adding OT charges"""
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=45,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543212"
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="OT003",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Create OT procedure
        ot_procedure = await ot_crud.create_ot_procedure(
            db=db_session,
            ipd_id=ipd.ipd_id,
            operation_name="Hernia Repair",
            operation_date=datetime.now(),
            duration_minutes=90,
            surgeon_name="Dr. Johnson",
            created_by="test_user"
        )
        
        # Add OT charges
        charges = await ot_crud.add_ot_charges(
            db=db_session,
            ipd_id=ipd.ipd_id,
            ot_id=ot_procedure.ot_id,
            surgeon_charge=Decimal("15000.00"),
            anesthesia_charge=Decimal("5000.00"),
            facility_charge=Decimal("3000.00"),
            assistant_charge=Decimal("2000.00"),
            created_by="test_user"
        )
        
        assert len(charges) == 4
        
        # Verify surgeon charge
        surgeon_charge = next(c for c in charges if "Surgeon" in c.charge_name)
        assert surgeon_charge.charge_type == ChargeType.OT
        assert surgeon_charge.total_amount == Decimal("15000.00")
        
        # Verify anesthesia charge
        anesthesia_charge = next(c for c in charges if "Anesthesia" in c.charge_name)
        assert anesthesia_charge.total_amount == Decimal("5000.00")
        
        # Verify facility charge
        facility_charge = next(c for c in charges if "Facility" in c.charge_name)
        assert facility_charge.total_amount == Decimal("3000.00")
        
        # Verify assistant charge
        assistant_charge = next(c for c in charges if "Assistant" in c.charge_name)
        assert assistant_charge.total_amount == Decimal("2000.00")
    
    @pytest.mark.asyncio
    async def test_add_ot_charges_without_assistant(self, db_session: AsyncSession):
        """Test adding OT charges without assistant charge"""
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=45,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543213"
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="OT004",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Create OT procedure
        ot_procedure = await ot_crud.create_ot_procedure(
            db=db_session,
            ipd_id=ipd.ipd_id,
            operation_name="Cataract Surgery",
            operation_date=datetime.now(),
            duration_minutes=45,
            surgeon_name="Dr. Lee",
            created_by="test_user"
        )
        
        # Add OT charges without assistant
        charges = await ot_crud.add_ot_charges(
            db=db_session,
            ipd_id=ipd.ipd_id,
            ot_id=ot_procedure.ot_id,
            surgeon_charge=Decimal("8000.00"),
            anesthesia_charge=Decimal("2000.00"),
            facility_charge=Decimal("1500.00"),
            created_by="test_user"
        )
        
        # Should only have 3 charges (no assistant)
        assert len(charges) == 3
        assert all("Assistant" not in c.charge_name for c in charges)
    
    @pytest.mark.asyncio
    async def test_add_ot_charges_negative_charge(self, db_session: AsyncSession):
        """Test adding OT charges with negative values"""
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=45,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543214"
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="OT005",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Create OT procedure
        ot_procedure = await ot_crud.create_ot_procedure(
            db=db_session,
            ipd_id=ipd.ipd_id,
            operation_name="Test Operation",
            operation_date=datetime.now(),
            duration_minutes=60,
            surgeon_name="Dr. Test",
            created_by="test_user"
        )
        
        # Try to add negative surgeon charge
        with pytest.raises(ValueError, match="Surgeon charge cannot be negative"):
            await ot_crud.add_ot_charges(
                db=db_session,
                ipd_id=ipd.ipd_id,
                ot_id=ot_procedure.ot_id,
                surgeon_charge=Decimal("-1000.00"),
                anesthesia_charge=Decimal("2000.00"),
                facility_charge=Decimal("1500.00"),
                created_by="test_user"
            )
    
    @pytest.mark.asyncio
    async def test_get_ot_procedure_by_id(self, db_session: AsyncSession):
        """Test getting OT procedure by ID"""
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=45,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543215"
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="OT006",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Create OT procedure
        ot_procedure = await ot_crud.create_ot_procedure(
            db=db_session,
            ipd_id=ipd.ipd_id,
            operation_name="Gallbladder Removal",
            operation_date=datetime.now(),
            duration_minutes=150,
            surgeon_name="Dr. Brown",
            created_by="test_user"
        )
        
        # Get OT procedure by ID
        retrieved = await ot_crud.get_ot_procedure_by_id(db_session, ot_procedure.ot_id)
        
        assert retrieved is not None
        assert retrieved.ot_id == ot_procedure.ot_id
        assert retrieved.operation_name == "Gallbladder Removal"
    
    @pytest.mark.asyncio
    async def test_get_ot_procedures_by_ipd(self, db_session: AsyncSession):
        """Test getting all OT procedures for an IPD"""
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=45,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543216"
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="OT007",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Create multiple OT procedures
        ot1 = await ot_crud.create_ot_procedure(
            db=db_session,
            ipd_id=ipd.ipd_id,
            operation_name="Operation 1",
            operation_date=datetime.now(),
            duration_minutes=60,
            surgeon_name="Dr. A",
            created_by="test_user"
        )
        
        ot2 = await ot_crud.create_ot_procedure(
            db=db_session,
            ipd_id=ipd.ipd_id,
            operation_name="Operation 2",
            operation_date=datetime.now() + timedelta(days=1),
            duration_minutes=90,
            surgeon_name="Dr. B",
            created_by="test_user"
        )
        
        # Get all OT procedures for IPD
        procedures = await ot_crud.get_ot_procedures_by_ipd(db_session, ipd.ipd_id)
        
        assert len(procedures) == 2
        assert any(p.operation_name == "Operation 1" for p in procedures)
        assert any(p.operation_name == "Operation 2" for p in procedures)
    
    @pytest.mark.asyncio
    async def test_get_ot_charges_by_ipd(self, db_session: AsyncSession):
        """Test getting all OT charges for an IPD"""
        # Create patient and IPD
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Test Patient",
            age=45,
            gender=Gender.MALE,
            address="Test Address",
            mobile_number="9876543217"
        )
        
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="OT008",
            ward_type=WardType.GENERAL,
            per_day_charge=Decimal("500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("1000.00")
        )
        
        # Create OT procedure
        ot_procedure = await ot_crud.create_ot_procedure(
            db=db_session,
            ipd_id=ipd.ipd_id,
            operation_name="Test Operation",
            operation_date=datetime.now(),
            duration_minutes=120,
            surgeon_name="Dr. Test",
            created_by="test_user"
        )
        
        # Add OT charges
        await ot_crud.add_ot_charges(
            db=db_session,
            ipd_id=ipd.ipd_id,
            ot_id=ot_procedure.ot_id,
            surgeon_charge=Decimal("10000.00"),
            anesthesia_charge=Decimal("3000.00"),
            facility_charge=Decimal("2000.00"),
            created_by="test_user"
        )
        
        # Get all OT charges for IPD
        charges = await ot_crud.get_ot_charges_by_ipd(db_session, ipd.ipd_id)
        
        assert len(charges) == 3
        assert all(c.charge_type == ChargeType.OT for c in charges)
        
        total = sum(c.total_amount for c in charges)
        assert total == Decimal("15000.00")
