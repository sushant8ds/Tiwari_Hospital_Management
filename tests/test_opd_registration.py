"""
Test OPD registration and follow-up functionality
"""

import pytest
import pytest_asyncio
from datetime import date, time
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.models.patient import Gender
from app.models.doctor import DoctorStatus
from app.models.visit import VisitType, PaymentMode


@pytest_asyncio.fixture
async def test_patient(db_session: AsyncSession):
    """Create a test patient."""
    return await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test Street",
        mobile_number="9876543210"
    )


@pytest_asyncio.fixture
async def test_doctor(db_session: AsyncSession):
    """Create a test doctor."""
    return await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="Cardiology",
        new_patient_fee=Decimal("500.00"),
        followup_fee=Decimal("300.00"),
        status=DoctorStatus.ACTIVE
    )


@pytest_asyncio.fixture
async def patient_with_visit(db_session: AsyncSession, test_patient, test_doctor):
    """Create a patient with a previous visit for follow-up testing."""
    visit = await visit_crud.create_visit(
        db=db_session,
        patient_id=test_patient.patient_id,
        doctor_id=test_doctor.doctor_id,
        visit_type=VisitType.OPD_NEW,
        payment_mode=PaymentMode.CASH
    )
    return test_patient, visit


@pytest.mark.asyncio
async def test_register_new_opd_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_patient,
    test_doctor,
    auth_headers
):
    """Test successful new OPD registration."""
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "CASH"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/register",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify response structure
    assert "visit_id" in data
    assert data["visit_id"].startswith("V")
    assert data["patient_id"] == test_patient.patient_id
    assert data["doctor_id"] == test_doctor.doctor_id
    assert data["visit_type"] == "OPD_NEW"
    assert data["department"] == test_doctor.department
    assert data["serial_number"] == 1
    assert float(data["opd_fee"]) == float(test_doctor.new_patient_fee)
    assert data["payment_mode"] == "CASH"
    assert data["status"] == "ACTIVE"
    
    # Verify patient info is included
    assert "patient" in data
    assert data["patient"]["patient_id"] == test_patient.patient_id
    assert data["patient"]["name"] == test_patient.name
    
    # Verify doctor info is included
    assert "doctor" in data
    assert data["doctor"]["doctor_id"] == test_doctor.doctor_id
    assert data["doctor"]["name"] == test_doctor.name
    assert data["doctor"]["department"] == test_doctor.department


@pytest.mark.asyncio
async def test_register_new_opd_with_upi(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_patient,
    test_doctor,
    auth_headers
):
    """Test new OPD registration with UPI payment."""
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "UPI"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/register",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["payment_mode"] == "UPI"


@pytest.mark.asyncio
async def test_register_new_opd_with_card(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_patient,
    test_doctor,
    auth_headers
):
    """Test new OPD registration with Card payment."""
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "CARD"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/register",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["payment_mode"] == "CARD"


@pytest.mark.asyncio
async def test_register_new_opd_invalid_patient(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_doctor,
    auth_headers
):
    """Test new OPD registration with invalid patient ID."""
    request_data = {
        "patient_id": "P999999999999",  # Non-existent patient
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "CASH"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/register",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_new_opd_invalid_doctor(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_patient,
    auth_headers
):
    """Test new OPD registration with invalid doctor ID."""
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": "D999999999999",  # Non-existent doctor
        "payment_mode": "CASH"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/register",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_new_opd_invalid_payment_mode(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_patient,
    test_doctor,
    auth_headers
):
    """Test new OPD registration with invalid payment mode."""
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "INVALID"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/register",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_followup_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    patient_with_visit,
    test_doctor,
    auth_headers
):
    """Test successful follow-up registration."""
    test_patient, previous_visit = patient_with_visit
    
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "UPI"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/followup",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify response structure
    assert "visit_id" in data
    assert data["visit_id"].startswith("V")
    assert data["patient_id"] == test_patient.patient_id
    assert data["doctor_id"] == test_doctor.doctor_id
    assert data["visit_type"] == "OPD_FOLLOWUP"
    assert data["department"] == test_doctor.department
    assert data["serial_number"] == 2  # Second visit for this doctor today
    assert float(data["opd_fee"]) == float(test_doctor.followup_fee)
    assert data["payment_mode"] == "UPI"
    assert data["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_register_followup_no_previous_visit(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_patient,
    test_doctor,
    auth_headers
):
    """Test follow-up registration for patient with no previous visits."""
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "CASH"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/followup",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "no previous visits" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_serial_number_increments_correctly(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_doctor,
    auth_headers
):
    """Test that serial numbers increment correctly for same doctor on same day."""
    # Create multiple patients
    patients = []
    for i in range(3):
        patient = await patient_crud.create_patient(
            db=db_session,
            name=f"Patient {i}",
            age=30 + i,
            gender=Gender.MALE,
            address=f"{i} Test Street",
            mobile_number=f"987654321{i}"
        )
        patients.append(patient)
    
    # Register all patients for same doctor
    serial_numbers = []
    for patient in patients:
        request_data = {
            "patient_id": patient.patient_id,
            "doctor_id": test_doctor.doctor_id,
            "payment_mode": "CASH"
        }
        
        response = await async_client.post(
            "/api/v1/visits/opd/register",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        serial_numbers.append(data["serial_number"])
    
    # Verify serial numbers are sequential
    assert serial_numbers == [1, 2, 3]


@pytest.mark.asyncio
async def test_serial_number_independent_per_doctor(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_patient,
    auth_headers
):
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
    
    # Create second patient
    patient2 = await patient_crud.create_patient(
        db=db_session,
        name="Patient Two",
        age=35,
        gender=Gender.FEMALE,
        address="456 Test Street",
        mobile_number="9876543211"
    )
    
    # Register patient1 with doctor1
    response1 = await async_client.post(
        "/api/v1/visits/opd/register",
        json={
            "patient_id": test_patient.patient_id,
            "doctor_id": doctor1.doctor_id,
            "payment_mode": "CASH"
        },
        headers=auth_headers
    )
    
    # Register patient2 with doctor2
    response2 = await async_client.post(
        "/api/v1/visits/opd/register",
        json={
            "patient_id": patient2.patient_id,
            "doctor_id": doctor2.doctor_id,
            "payment_mode": "CASH"
        },
        headers=auth_headers
    )
    
    assert response1.status_code == 201
    assert response2.status_code == 201
    
    # Both should have serial number 1 since they're for different doctors
    assert response1.json()["serial_number"] == 1
    assert response2.json()["serial_number"] == 1


@pytest.mark.asyncio
async def test_department_auto_filled_from_doctor(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_patient,
    test_doctor,
    auth_headers
):
    """Test that department is automatically filled from selected doctor."""
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "CASH"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/register",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify department matches doctor's department
    assert data["department"] == test_doctor.department
    assert data["doctor"]["department"] == test_doctor.department


@pytest.mark.asyncio
async def test_opd_fee_calculated_correctly_for_new_patient(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_patient,
    test_doctor,
    auth_headers
):
    """Test that OPD fee is calculated correctly for new patients."""
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "CASH"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/register",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify fee matches doctor's new patient fee
    assert float(data["opd_fee"]) == float(test_doctor.new_patient_fee)


@pytest.mark.asyncio
async def test_opd_fee_calculated_correctly_for_followup(
    async_client: AsyncClient,
    db_session: AsyncSession,
    patient_with_visit,
    test_doctor,
    auth_headers
):
    """Test that OPD fee is calculated correctly for follow-up patients."""
    test_patient, previous_visit = patient_with_visit
    
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "CASH"
    }
    
    response = await async_client.post(
        "/api/v1/visits/opd/followup",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify fee matches doctor's follow-up fee
    assert float(data["opd_fee"]) == float(test_doctor.followup_fee)


@pytest.mark.asyncio
async def test_search_followup_patients(
    async_client: AsyncClient,
    db_session: AsyncSession,
    patient_with_visit,
    auth_headers
):
    """Test searching for follow-up patients."""
    test_patient, previous_visit = patient_with_visit
    
    # Search by patient ID
    response = await async_client.get(
        f"/api/v1/visits/followup/search?search_term={test_patient.patient_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0
    assert data[0]["patient"]["patient_id"] == test_patient.patient_id
    assert "last_visit_date" in data[0]
    assert "last_visit_doctor" in data[0]
    assert "last_visit_department" in data[0]


@pytest.mark.asyncio
async def test_search_followup_patients_by_mobile(
    async_client: AsyncClient,
    db_session: AsyncSession,
    patient_with_visit,
    auth_headers
):
    """Test searching for follow-up patients by mobile number."""
    test_patient, previous_visit = patient_with_visit
    
    # Search by mobile number
    response = await async_client.get(
        f"/api/v1/visits/followup/search?search_term={test_patient.mobile_number}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0
    assert data[0]["patient"]["mobile_number"] == test_patient.mobile_number


@pytest.mark.asyncio
async def test_get_visit_by_id(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_patient,
    test_doctor,
    auth_headers
):
    """Test getting visit details by ID."""
    # Create a visit first
    request_data = {
        "patient_id": test_patient.patient_id,
        "doctor_id": test_doctor.doctor_id,
        "payment_mode": "CASH"
    }
    
    create_response = await async_client.post(
        "/api/v1/visits/opd/register",
        json=request_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    visit_id = create_response.json()["visit_id"]
    
    # Get visit by ID
    get_response = await async_client.get(
        f"/api/v1/visits/{visit_id}",
        headers=auth_headers
    )
    
    assert get_response.status_code == 200
    data = get_response.json()
    
    assert data["visit_id"] == visit_id
    assert data["patient_id"] == test_patient.patient_id
    assert data["doctor_id"] == test_doctor.doctor_id
    assert "patient" in data
    assert "doctor" in data


@pytest.mark.asyncio
async def test_get_visit_not_found(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers
):
    """Test getting non-existent visit."""
    response = await async_client.get(
        "/api/v1/visits/V999999999999",
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_active_doctors(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_doctor,
    auth_headers
):
    """Test getting list of active doctors."""
    response = await async_client.get(
        "/api/v1/doctors/",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0
    assert any(d["doctor_id"] == test_doctor.doctor_id for d in data)


@pytest.mark.asyncio
async def test_get_doctor_by_id(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_doctor,
    auth_headers
):
    """Test getting doctor details by ID."""
    response = await async_client.get(
        f"/api/v1/doctors/{test_doctor.doctor_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["doctor_id"] == test_doctor.doctor_id
    assert data["name"] == test_doctor.name
    assert data["department"] == test_doctor.department
    assert float(data["new_patient_fee"]) == float(test_doctor.new_patient_fee)
    assert float(data["followup_fee"]) == float(test_doctor.followup_fee)
