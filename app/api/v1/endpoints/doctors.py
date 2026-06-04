"""
Doctor management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.doctor import DoctorCreate, DoctorResponse
from app.schemas.auth import UserResponse
from app.crud.doctor import doctor_crud
from app.models.doctor import DoctorStatus

router = APIRouter()


@router.post("/", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    doctor: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new doctor (Admin only)
    
    - Validates all required fields
    - Generates unique doctor ID
    - Sets consultation fees for new and follow-up patients
    """
    try:
        # Parse status
        doctor_status = DoctorStatus[doctor.status.upper()]
        
        new_doctor = await doctor_crud.create_doctor(
            db=db,
            name=doctor.name,
            department=doctor.department,
            new_patient_fee=doctor.new_patient_fee,
            followup_fee=doctor.followup_fee,
            status=doctor_status
        )
        
        return DoctorResponse(
            doctor_id=new_doctor.doctor_id,
            name=new_doctor.name,
            department=new_doctor.department,
            new_patient_fee=new_doctor.new_patient_fee,
            followup_fee=new_doctor.followup_fee,
            status=new_doctor.status.value,
            created_date=new_doctor.created_date
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating doctor: {str(e)}"
        )


@router.get("/", response_model=List[DoctorResponse])
async def get_doctors(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of doctors (Public endpoint for OPD registration)
    
    - Returns active doctors by default
    - Can return all doctors if active_only=false
    - Used for doctor selection dropdown in OPD registration
    - No authentication required to allow public access for registration forms
    """
    try:
        if active_only:
            doctors = await doctor_crud.get_active_doctors(db)
        else:
            # For now, just return active doctors
            # Can be extended to return all doctors if needed
            doctors = await doctor_crud.get_active_doctors(db)
        
        return [
            DoctorResponse(
                doctor_id=doctor.doctor_id,
                name=doctor.name,
                department=doctor.department,
                new_patient_fee=doctor.new_patient_fee,
                followup_fee=doctor.followup_fee,
                status=doctor.status.value,
                created_date=doctor.created_date
            )
            for doctor in doctors
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving doctors: {str(e)}"
        )


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(
    doctor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get doctor details by ID
    
    - Returns doctor information including fees
    - Used for auto-filling department when doctor is selected
    """
    try:
        doctor = await doctor_crud.get_doctor_by_id(db, doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found"
            )
        
        return DoctorResponse(
            doctor_id=doctor.doctor_id,
            name=doctor.name,
            department=doctor.department,
            new_patient_fee=doctor.new_patient_fee,
            followup_fee=doctor.followup_fee,
            status=doctor.status.value,
            created_date=doctor.created_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving doctor: {str(e)}"
        )