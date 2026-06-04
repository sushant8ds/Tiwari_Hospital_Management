"""
Patient management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.schemas.patient import (
    PatientCreate, 
    PatientResponse, 
    PatientUpdate,
    PatientHistoryResponse
)
from app.crud.patient import patient_crud
from app.models.patient import Gender

router = APIRouter()


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new patient
    
    Requirements: 1.1, 1.2
    - Generates unique Patient_ID automatically
    - Validates all mandatory fields (name, age, gender, address, mobile_number)
    - Ensures mobile number uniqueness
    """
    try:
        # Convert gender string to enum
        gender_enum = Gender[patient.gender.upper()]
        
        new_patient = await patient_crud.create_patient(
            db=db,
            name=patient.name,
            age=patient.age,
            gender=gender_enum,
            address=patient.address,
            mobile_number=patient.mobile_number
        )
        
        return new_patient
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create patient: {str(e)}"
        )


@router.get("/search", response_model=List[PatientResponse])
async def search_patients(
    query: Optional[str] = Query(None, description="Search by patient ID, mobile number, or name"),
    patient_id: Optional[str] = Query(None, description="Search by patient ID"),
    mobile_number: Optional[str] = Query(None, description="Search by mobile number"),
    name: Optional[str] = Query(None, description="Search by patient name"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search patients by ID, mobile number, or name
    
    Requirements: 1.7, 13.1
    - Supports search by Patient_ID, Mobile_Number, and Patient_Name
    - Returns matching patient records
    - Accepts generic 'query' parameter or specific parameters
    """
    try:
        # Determine search term based on provided parameters
        search_term = query or patient_id or mobile_number or name
        
        if not search_term:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one search parameter is required"
            )
        
        patients = await patient_crud.search_patients(
            db=db,
            search_term=search_term
        )
        
        return patients
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search patients: {str(e)}"
        )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get patient details by ID
    
    Requirements: 1.7, 13.1
    - Retrieves complete patient information by Patient_ID
    """
    try:
        patient = await patient_crud.get_patient_by_id(db=db, patient_id=patient_id)
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        return patient
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patient: {str(e)}"
        )


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update patient details
    
    Requirements: 1.2
    - Updates patient information with validation
    - Maintains data integrity
    """
    try:
        # Convert gender string to enum if provided
        gender_enum = None
        if patient_update.gender:
            gender_enum = Gender[patient_update.gender.upper()]
        
        updated_patient = await patient_crud.update_patient(
            db=db,
            patient_id=patient_id,
            name=patient_update.name,
            age=patient_update.age,
            gender=gender_enum,
            address=patient_update.address,
            mobile_number=patient_update.mobile_number
        )
        
        if not updated_patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        return updated_patient
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update patient: {str(e)}"
        )


@router.get("/{patient_id}/history", response_model=PatientHistoryResponse)
async def get_patient_history(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get patient visit history
    
    Requirements: 13.2, 13.4
    - Displays complete patient history including visits and IPD admissions
    - Shows date-wise visits, doctors consulted, and charges
    """
    try:
        patient = await patient_crud.get_patient_history(db=db, patient_id=patient_id)
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        # Build history response
        history = {
            "patient": patient,
            "visits": patient.visits,
            "ipd_admissions": patient.ipd_admissions
        }
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patient history: {str(e)}"
        )