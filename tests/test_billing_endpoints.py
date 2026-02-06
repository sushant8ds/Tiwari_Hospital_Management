"""
Tests for billing endpoints
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud
from app.models.patient import Gender
from app.models.visit import VisitType, PaymentMode


@pytest.mark.asyncio
async def test_add_investigation_charges_endpoint(async_client, db_session, auth_headers):
    """Test adding investigation charges via endpoint"""
    # Create patient, doctor, and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543220"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="Cardiology",
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
    
    # Add investigation charges
    investigation_data = [
        {
            "charge_name": "X-Ray Chest",
            "rate": 500.00,
            "quantity": 1
        },
        {
            "charge_name": "ECG",
            "rate": 300.00,
            "quantity": 1
        }
    ]
    
    response = await async_client.post(
        f"/api/v1/billing/{visit.visit_id}/investigations",
        json=investigation_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["charge_name"] == "X-Ray Chest"
    assert data[1]["charge_name"] == "ECG"


@pytest.mark.asyncio
async def test_add_procedure_charges_endpoint(async_client, db_session, auth_headers):
    """Test adding procedure charges via endpoint"""
    # Create patient, doctor, and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543221"
    )
    
    doctor = await doctor_crud.create_doctor(
        db=db_session,
        name="Dr. Test",
        department="Surgery",
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
    
    # Add procedure charges
    procedure_data = [
        {
            "charge_name": "Dressing",
            "rate": 200.00,
            "quantity": 2
        }
    ]
    
    response = await async_client.post(
        f"/api/v1/billing/{visit.visit_id}/procedures",
        json=procedure_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["charge_name"] == "Dressing"
    assert float(data[0]["total_amount"]) == 400.00


@pytest.mark.asyncio
async def test_add_service_charges_endpoint(async_client, db_session, auth_headers):
    """Test adding service charges via endpoint"""
    # Create patient, doctor, and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543222"
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
    
    # Add service charges with time calculation
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=5)
    
    service_data = [
        {
            "charge_name": "Oxygen",
            "rate": 100.00,
            "quantity": 1,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    ]
    
    response = await async_client.post(
        f"/api/v1/billing/{visit.visit_id}/services",
        json=service_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["charge_name"] == "Oxygen"
    assert data[0]["quantity"] == 5  # 5 hours


@pytest.mark.asyncio
async def test_get_visit_charges_endpoint(async_client, db_session, auth_headers):
    """Test getting all charges for a visit"""
    # Create patient, doctor, and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543223"
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
    
    # Add some charges
    investigation_data = [
        {
            "charge_name": "X-Ray",
            "rate": 500.00,
            "quantity": 1
        }
    ]
    
    await async_client.post(
        f"/api/v1/billing/{visit.visit_id}/investigations",
        json=investigation_data,
        headers=auth_headers
    )
    
    # Get all charges
    response = await async_client.get(
        f"/api/v1/billing/{visit.visit_id}/charges",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["charge_name"] == "X-Ray"


@pytest.mark.asyncio
async def test_get_visit_total_endpoint(async_client, db_session, auth_headers):
    """Test getting total charges for a visit"""
    # Create patient, doctor, and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543224"
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
    
    # Add charges
    investigation_data = [
        {
            "charge_name": "X-Ray",
            "rate": 500.00,
            "quantity": 1
        }
    ]
    
    procedure_data = [
        {
            "charge_name": "Dressing",
            "rate": 200.00,
            "quantity": 2
        }
    ]
    
    await async_client.post(
        f"/api/v1/billing/{visit.visit_id}/investigations",
        json=investigation_data,
        headers=auth_headers
    )
    
    await async_client.post(
        f"/api/v1/billing/{visit.visit_id}/procedures",
        json=procedure_data,
        headers=auth_headers
    )
    
    # Get total
    response = await async_client.get(
        f"/api/v1/billing/{visit.visit_id}/total",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["visit_id"] == visit.visit_id
    assert float(data["total_charges"]) == 900.00  # 500 + (200 * 2)


@pytest.mark.asyncio
async def test_add_investigation_charges_invalid_visit(async_client, db_session, auth_headers):
    """Test adding investigation charges with invalid visit ID"""
    investigation_data = [
        {
            "charge_name": "X-Ray",
            "rate": 500.00,
            "quantity": 1
        }
    ]
    
    response = await async_client.post(
        "/api/v1/billing/INVALID_VISIT_ID/investigations",
        json=investigation_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Visit not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_add_charges_with_negative_rate(async_client, db_session, auth_headers):
    """Test adding charges with negative rate fails"""
    # Create patient, doctor, and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543225"
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
    
    # Try to add charge with negative rate
    investigation_data = [
        {
            "charge_name": "X-Ray",
            "rate": -500.00,
            "quantity": 1
        }
    ]
    
    response = await async_client.post(
        f"/api/v1/billing/{visit.visit_id}/investigations",
        json=investigation_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_add_charges_with_zero_quantity(async_client, db_session, auth_headers):
    """Test adding charges with zero quantity fails"""
    # Create patient, doctor, and visit
    patient = await patient_crud.create_patient(
        db=db_session,
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        address="123 Test St",
        mobile_number="9876543226"
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
    
    # Try to add charge with zero quantity
    investigation_data = [
        {
            "charge_name": "X-Ray",
            "rate": 500.00,
            "quantity": 0
        }
    ]
    
    response = await async_client.post(
        f"/api/v1/billing/{visit.visit_id}/investigations",
        json=investigation_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error
