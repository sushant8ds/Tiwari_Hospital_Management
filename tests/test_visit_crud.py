"""
Test Visit CRUD operations
"""

import pytest
import pytest_asyncio
from datetime import date, time
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.visit import visit_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.models.visit import Visit, VisitType, PaymentMode, VisitStatus
from app.models.patient import Gender
from app.models.doctor import DoctorStatus


@pytest_asyncio.fixture
async def sample_patient(db_session: AsyncSession):
    """Create a sample patient for testing."""
    return await patient_crud.create_patient(
        db=db_session,
        name="John Doe",
        age=35,
        gender=Gender.MALE,
        address="123 Test Street",
        mobile_number="9876543210"
    )


@pytest_asyncio.fixture
async def sample_doctor(db_session: AsyncSession):
    """Create a sample doctor for testing."""
    return await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Smith",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )


@pytest.mark.asyncio
async def test_create_new_visit_success(db_session: AsyncSession, sample_patient, sample_doctor):
    """Test successful new visit creation."""
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=sample_patient.patient_id,
        doctor_id=sample_doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    assert visit.visit_id.startswith("V")
    assert visit.patient_id == sample_patient.patient_id
    assert visit.doctor_id == sample_doctor.doctor_id
    assert visit.visit_type == VisitType.OPD_NEW
    assert visit.department == sample_doctor.department
    assert visit.serial_number == 1  # First visit of the day
    assert visit.opd_fee == sample_doctor.new_patient_fee
    assert visit.payment_mode == PaymentMode.CASH
    assert visit.status == VisitStatus.ACTIVE


@pytest.mark.asyncio
async def test_create_followup_visit_success(db_session: AsyncSession, sample_patient, sample_doctor):
    """Test successful follow-up visit creation."""
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=sample_patient.patient_id,
        doctor_id=sample_doctor.doctor_id,
        visit_type=VisitType.OPD_FOLLOWUP,
        payment_mode=PaymentMode.UPI
    )
    
    assert visit.visit_type == VisitType.OPD_FOLLOWUP
    assert visit.opd_fee == sample_doctor.followup_fee
    assert visit.payment_mode == PaymentMode.UPI


@pytest.mark.asyncio
async def test_serial_number_increment(db_session: AsyncSession, sample_patient, sample_doctor):
    """Test that serial numbers increment correctly for same doctor on same day."""
    today = date.today()
    
    # Create first visit
    visit1 = await visit_crud.create_visit(
        db=db_session,
        patient_id=sample_patient.patient_id,
        doctor_id=sample_doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH,
        visit_date=today
    )
    
    # Create second patient for second visit
    patient2 = await patient_crud.create_patient(
        db=db_session,
        name="Jane Doe",
        age=28,
        gender=Gender.FEMALE,
        address="456 Another Street",
        mobile_number="9876543211"
    )
    
    # Create second visit for same doctor on same day
    visit2 = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient2.patient_id,
        doctor_id=sample_doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CARD,
        visit_date=today
    )
    
    assert visit1.serial_number == 1
    assert visit2.serial_number == 2
    assert visit1.visit_date == visit2.visit_date
    assert visit1.doctor_id == visit2.doctor_id


@pytest.mark.asyncio
async def test_serial_number_different_doctors(db_session: AsyncSession, sample_patient):
    """Test that serial numbers are independent for different doctors."""
    # Create two doctors
    doctor1 = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. First",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    doctor2 = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Second",
        department="Neurology",
        new_patient_fee=Decimal("600.00"),
        followup_fee=Decimal("400.00")
    )
    
    today = date.today()
    
    # Create visits for both doctors
    visit1 = await visit_crud.create_visit(
        db=db_session,
        patient_id=sample_patient.patient_id,
        doctor_id=doctor1.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH,
        visit_date=today
    )
    
    # Create second patient
    patient2 = await patient_crud.create_patient(
        db=db_session,
        name="Jane Doe",
        age=28,
        gender=Gender.FEMALE,
        address="456 Another Street",
        mobile_number="9876543211"
    )
    
    visit2 = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient2.patient_id,
        doctor_id=doctor2.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.UPI,
        visit_date=today
    )
    
    # Both should have serial number 1 since they're for different doctors
    assert visit1.serial_number == 1
    assert visit2.serial_number == 1


@pytest.mark.asyncio
async def test_create_visit_invalid_patient(db_session: AsyncSession, sample_doctor):
    """Test visit creation with invalid patient ID."""
    with pytest.raises(ValueError, match="Patient not found"):
        await visit_crud.create_visit(
            db=db_session,
            patient_id="P999999999999",  # Non-existent patient
            doctor_id=sample_doctor.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )


@pytest.mark.asyncio
async def test_create_visit_invalid_doctor(db_session: AsyncSession, sample_patient):
    """Test visit creation with invalid doctor ID."""
    with pytest.raises(ValueError, match="Doctor not found"):
        await visit_crud.create_visit(
            db=db_session,
            patient_id=sample_patient.patient_id,
            doctor_id="D999999999999",  # Non-existent doctor
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode.CASH
        )


@pytest.mark.asyncio
async def test_get_visit_by_id(db_session: AsyncSession, sample_patient, sample_doctor):
    """Test getting visit by ID."""
    # Create visit
    created_visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=sample_patient.patient_id,
        doctor_id=sample_doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Get visit by ID
    retrieved_visit = await visit_crud.get_visit_by_id(
        db=db_session, 
        visit_id=created_visit.visit_id
    )
    
    assert retrieved_visit is not None
    assert retrieved_visit.visit_id == created_visit.visit_id
    assert retrieved_visit.patient_id == sample_patient.patient_id


@pytest.mark.asyncio
async def test_get_daily_visits(db_session: AsyncSession, sample_patient, sample_doctor):
    """Test getting daily visits."""
    today = date.today()
    
    # Create multiple visits for today
    visit1 = await visit_crud.create_visit(
        db=db_session,
        patient_id=sample_patient.patient_id,
        doctor_id=sample_doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH,
        visit_date=today
    )
    
    # Create second patient and visit
    patient2 = await patient_crud.create_patient(
        db=db_session,
        name="Jane Doe",
        age=28,
        gender=Gender.FEMALE,
        address="456 Another Street",
        mobile_number="9876543211"
    )
    
    visit2 = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient2.patient_id,
        doctor_id=sample_doctor.doctor_id,
        visit_type=VisitType.OPD_FOLLOWUP,
        payment_mode=PaymentMode.UPI,
        visit_date=today
    )
    
    # Get daily visits
    daily_visits = await visit_crud.get_daily_visits(db=db_session, visit_date=today)
    
    assert len(daily_visits) == 2
    assert daily_visits[0].serial_number == 1
    assert daily_visits[1].serial_number == 2


@pytest.mark.asyncio
async def test_get_daily_visits_by_doctor(db_session: AsyncSession, sample_patient):
    """Test getting daily visits filtered by doctor."""
    # Create two doctors
    doctor1 = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. First",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00")
    )
    
    doctor2 = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Second",
        department="Neurology",
        new_patient_fee=Decimal("600.00"),
        followup_fee=Decimal("400.00")
    )
    
    today = date.today()
    
    # Create visits for both doctors
    visit1 = await visit_crud.create_visit(
        db=db_session,
        patient_id=sample_patient.patient_id,
        doctor_id=doctor1.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH,
        visit_date=today
    )
    
    # Create second patient
    patient2 = await patient_crud.create_patient(
        db=db_session,
        name="Jane Doe",
        age=28,
        gender=Gender.FEMALE,
        address="456 Another Street",
        mobile_number="9876543211"
    )
    
    visit2 = await visit_crud.create_visit(
        db=db_session,
        patient_id=patient2.patient_id,
        doctor_id=doctor2.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.UPI,
        visit_date=today
    )
    
    # Get visits for doctor1 only
    doctor1_visits = await visit_crud.get_daily_visits(
        db=db_session, 
        visit_date=today, 
        doctor_id=doctor1.doctor_id
    )
    
    assert len(doctor1_visits) == 1
    assert doctor1_visits[0].doctor_id == doctor1.doctor_id


@pytest.mark.asyncio
async def test_update_visit_status(db_session: AsyncSession, sample_patient, sample_doctor):
    """Test updating visit status."""
    # Create visit
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=sample_patient.patient_id,
        doctor_id=sample_doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    
    # Update status
    updated_visit = await visit_crud.update_visit_status(
        db=db_session,
        visit_id=visit.visit_id,
        status=VisitStatus.COMPLETED
    )
    
    assert updated_visit is not None
    assert updated_visit.status == VisitStatus.COMPLETED


@pytest.mark.asyncio
async def test_get_doctor_daily_count(db_session: AsyncSession, sample_patient, sample_doctor):
    """Test getting doctor's daily visit count."""
    today = date.today()
    
    # Initially should be 0
    count = await visit_crud.get_doctor_daily_count(
        db=db_session,
        doctor_id=sample_doctor.doctor_id,
        visit_date=today
    )
    assert count == 0
    
    # Create a visit
    await visit_crud.create_visit(
        db=db_session,
        patient_id=sample_patient.patient_id,
        doctor_id=sample_doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH,
        visit_date=today
    )
    
    # Count should be 1
    count = await visit_crud.get_doctor_daily_count(
        db=db_session,
        doctor_id=sample_doctor.doctor_id,
        visit_date=today
    )
    assert count == 1