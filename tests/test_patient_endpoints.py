"""
Unit tests for patient registration endpoints
Tests Requirements: 1.1, 1.2, 1.7, 13.1
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient, Gender


@pytest.mark.asyncio
class TestPatientRegistration:
    """Test patient registration endpoint"""
    
    async def test_create_patient_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test successful patient registration"""
        patient_data = {
            "name": "John Doe",
            "age": 35,
            "gender": "MALE",
            "address": "123 Main Street, Mumbai",
            "mobile_number": "9876543210"
        }
        
        response = await async_client.post("/api/v1/patients/", json=patient_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == patient_data["name"]
        assert data["age"] == patient_data["age"]
        assert data["gender"] == patient_data["gender"]
        assert data["mobile_number"] == patient_data["mobile_number"]
        assert "patient_id" in data
        assert data["patient_id"].startswith("P")
    
    async def test_create_patient_invalid_mobile(self, async_client: AsyncClient):
        """Test patient registration with invalid mobile number"""
        patient_data = {
            "name": "Jane Doe",
            "age": 28,
            "gender": "FEMALE",
            "address": "456 Park Avenue, Delhi",
            "mobile_number": "1234567890"  # Invalid - doesn't start with 6-9
        }
        
        response = await async_client.post("/api/v1/patients/", json=patient_data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_create_patient_invalid_age(self, async_client: AsyncClient):
        """Test patient registration with invalid age"""
        patient_data = {
            "name": "Invalid Age",
            "age": 200,  # Invalid age
            "gender": "MALE",
            "address": "789 Test Street",
            "mobile_number": "9876543211"
        }
        
        response = await async_client.post("/api/v1/patients/", json=patient_data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_create_patient_duplicate_mobile(self, async_client: AsyncClient):
        """Test patient registration with duplicate mobile number"""
        patient_data = {
            "name": "First Patient",
            "age": 30,
            "gender": "MALE",
            "address": "123 Street",
            "mobile_number": "9876543212"
        }
        
        # Create first patient
        response1 = await async_client.post("/api/v1/patients/", json=patient_data)
        assert response1.status_code == 201
        
        # Try to create second patient with same mobile
        patient_data["name"] = "Second Patient"
        response2 = await async_client.post("/api/v1/patients/", json=patient_data)
        
        assert response2.status_code == 400  # Bad request
        assert "already exists" in response2.json()["detail"].lower()
    
    async def test_create_patient_missing_required_field(self, async_client: AsyncClient):
        """Test patient registration with missing required field"""
        patient_data = {
            "name": "Missing Field",
            "age": 25,
            "gender": "FEMALE",
            # Missing address
            "mobile_number": "9876543213"
        }
        
        response = await async_client.post("/api/v1/patients/", json=patient_data)
        
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestPatientSearch:
    """Test patient search functionality"""
    
    async def test_search_by_patient_id(self, async_client: AsyncClient, sample_patient: Patient):
        """Test search by patient ID"""
        response = await async_client.get(
            f"/api/v1/patients/search?patient_id={sample_patient.patient_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["patient_id"] == sample_patient.patient_id for p in data)
    
    async def test_search_by_mobile_number(self, async_client: AsyncClient, sample_patient: Patient):
        """Test search by mobile number"""
        response = await async_client.get(
            f"/api/v1/patients/search?mobile_number={sample_patient.mobile_number}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["mobile_number"] == sample_patient.mobile_number for p in data)
    
    async def test_search_by_name(self, async_client: AsyncClient, sample_patient: Patient):
        """Test search by patient name"""
        response = await async_client.get(
            f"/api/v1/patients/search?name={sample_patient.name}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["name"] == sample_patient.name for p in data)
    
    async def test_search_partial_name(self, async_client: AsyncClient, sample_patient: Patient):
        """Test search with partial name match"""
        # Search with first part of name
        search_term = sample_patient.name.split()[0]
        response = await async_client.get(
            f"/api/v1/patients/search?name={search_term}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    async def test_search_no_parameters(self, async_client: AsyncClient):
        """Test search without any parameters"""
        response = await async_client.get("/api/v1/patients/search")
        
        assert response.status_code == 400  # Bad request
        assert "required" in response.json()["detail"].lower()
    
    async def test_search_nonexistent_patient(self, async_client: AsyncClient):
        """Test search for nonexistent patient"""
        response = await async_client.get(
            "/api/v1/patients/search?patient_id=P99999999999"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


@pytest.mark.asyncio
class TestPatientRetrieval:
    """Test patient retrieval by ID"""
    
    async def test_get_patient_success(self, async_client: AsyncClient, sample_patient: Patient):
        """Test successful patient retrieval"""
        response = await async_client.get(f"/api/v1/patients/{sample_patient.patient_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == sample_patient.patient_id
        assert data["name"] == sample_patient.name
        assert data["mobile_number"] == sample_patient.mobile_number
    
    async def test_get_patient_not_found(self, async_client: AsyncClient):
        """Test retrieval of nonexistent patient"""
        response = await async_client.get("/api/v1/patients/P99999999999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestPatientUpdate:
    """Test patient update functionality"""
    
    async def test_update_patient_name(self, async_client: AsyncClient, sample_patient: Patient):
        """Test updating patient name"""
        update_data = {"name": "Updated Name"}
        
        response = await async_client.put(
            f"/api/v1/patients/{sample_patient.patient_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["patient_id"] == sample_patient.patient_id
    
    async def test_update_patient_age(self, async_client: AsyncClient, sample_patient: Patient):
        """Test updating patient age"""
        update_data = {"age": 40}
        
        response = await async_client.put(
            f"/api/v1/patients/{sample_patient.patient_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["age"] == 40
    
    async def test_update_patient_mobile(self, async_client: AsyncClient, sample_patient: Patient):
        """Test updating patient mobile number"""
        update_data = {"mobile_number": "9999888877"}
        
        response = await async_client.put(
            f"/api/v1/patients/{sample_patient.patient_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["mobile_number"] == "9999888877"
    
    async def test_update_patient_invalid_mobile(self, async_client: AsyncClient, sample_patient: Patient):
        """Test updating with invalid mobile number"""
        update_data = {"mobile_number": "1234567890"}  # Invalid
        
        response = await async_client.put(
            f"/api/v1/patients/{sample_patient.patient_id}",
            json=update_data
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_update_patient_not_found(self, async_client: AsyncClient):
        """Test updating nonexistent patient"""
        update_data = {"name": "New Name"}
        
        response = await async_client.put(
            "/api/v1/patients/P99999999999",
            json=update_data
        )
        
        assert response.status_code == 404
    
    async def test_update_patient_multiple_fields(self, async_client: AsyncClient, sample_patient: Patient):
        """Test updating multiple fields at once"""
        update_data = {
            "name": "Multi Update",
            "age": 45,
            "address": "New Address 123"
        }
        
        response = await async_client.put(
            f"/api/v1/patients/{sample_patient.patient_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Multi Update"
        assert data["age"] == 45
        assert data["address"] == "New Address 123"


@pytest.mark.asyncio
class TestPatientHistory:
    """Test patient history retrieval"""
    
    async def test_get_patient_history_no_visits(self, async_client: AsyncClient, sample_patient: Patient):
        """Test patient history with no visits"""
        response = await async_client.get(
            f"/api/v1/patients/{sample_patient.patient_id}/history"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "patient" in data
        assert "visits" in data
        assert "ipd_admissions" in data
        assert data["patient"]["patient_id"] == sample_patient.patient_id
        assert isinstance(data["visits"], list)
        assert isinstance(data["ipd_admissions"], list)
    
    async def test_get_patient_history_not_found(self, async_client: AsyncClient):
        """Test history for nonexistent patient"""
        response = await async_client.get("/api/v1/patients/P99999999999/history")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
