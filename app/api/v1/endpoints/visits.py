"""
Visit management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.visit import (
    OPDRegistrationRequest,
    FollowUpRegistrationRequest,
    VisitResponse,
    VisitDetailResponse,
    FollowUpPatientInfo,
    PatientInfo,
    DoctorInfo
)
from app.schemas.auth import UserResponse
from app.crud.visit import visit_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.models.visit import VisitType, PaymentMode

router = APIRouter()


@router.post("/opd/new", response_model=VisitDetailResponse, status_code=status.HTTP_201_CREATED)
async def register_new_opd_with_patient(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new OPD patient visit (Public endpoint for registration form)
    
    - Creates new patient if needed
    - Automatically populates department from doctor
    - Generates unique visit ID and serial number
    - Calculates OPD fee based on doctor's new patient fee
    - Supports Cash, UPI, and Card payment modes
    - No authentication required for public registration
    """
    try:
        # Extract patient and visit data
        patient_data = request.get("patient", {})
        doctor_id = request.get("doctor_id")
        payment_mode = request.get("payment_mode", "CASH")
        
        # Create new patient
        from app.models.patient import Gender
        patient = await patient_crud.create_patient(
            db=db,
            name=patient_data.get("name"),
            age=patient_data.get("age"),
            gender=Gender[patient_data.get("gender")],
            mobile_number=patient_data.get("mobile_number"),
            address=patient_data.get("address")
        )
        
        # Validate doctor exists and is active
        doctor = await doctor_crud.get_doctor_by_id(db, doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found"
            )
        
        # Create new OPD visit
        visit = await visit_crud.create_visit(
            db=db,
            patient_id=patient.patient_id,
            doctor_id=doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode[payment_mode]
        )
        
        # Prepare response with patient and doctor info
        response = VisitDetailResponse(
            visit_id=visit.visit_id,
            patient_id=visit.patient_id,
            visit_type=visit.visit_type.value,
            doctor_id=visit.doctor_id,
            department=visit.department,
            serial_number=visit.serial_number,
            visit_date=visit.visit_date,
            visit_time=visit.visit_time,
            opd_fee=visit.opd_fee,
            payment_mode=visit.payment_mode.value,
            status=visit.status.value,
            created_date=visit.created_date,
            patient=PatientInfo(
                patient_id=patient.patient_id,
                name=patient.name,
                age=patient.age,
                gender=patient.gender.value,
                mobile_number=patient.mobile_number
            ),
            doctor=DoctorInfo(
                doctor_id=doctor.doctor_id,
                name=doctor.name,
                department=doctor.department,
                new_patient_fee=doctor.new_patient_fee,
                followup_fee=doctor.followup_fee
            )
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating OPD visit: {str(e)}"
        )


@router.post("/opd/register", response_model=VisitDetailResponse, status_code=status.HTTP_201_CREATED)
async def register_new_opd(
    request: OPDRegistrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Register a new OPD patient visit
    
    - Validates patient and doctor exist
    - Automatically populates department from doctor
    - Generates unique visit ID and serial number
    - Calculates OPD fee based on doctor's new patient fee
    - Supports Cash, UPI, and Card payment modes
    """
    # Validate patient exists
    patient = await patient_crud.get_patient_by_id(db, request.patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {request.patient_id} not found"
        )
    
    # Validate doctor exists and is active
    doctor = await doctor_crud.get_doctor_by_id(db, request.doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {request.doctor_id} not found"
        )
    
    try:
        # Create new OPD visit
        visit = await visit_crud.create_visit(
            db=db,
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            visit_type=VisitType.OPD_NEW,
            payment_mode=PaymentMode[request.payment_mode],
            visit_date=request.visit_date,
            visit_time=request.visit_time
        )
        
        # Prepare response with patient and doctor info
        response = VisitDetailResponse(
            visit_id=visit.visit_id,
            patient_id=visit.patient_id,
            visit_type=visit.visit_type.value,
            doctor_id=visit.doctor_id,
            department=visit.department,
            serial_number=visit.serial_number,
            visit_date=visit.visit_date,
            visit_time=visit.visit_time,
            opd_fee=visit.opd_fee,
            payment_mode=visit.payment_mode.value,
            status=visit.status.value,
            created_date=visit.created_date,
            patient=PatientInfo(
                patient_id=patient.patient_id,
                name=patient.name,
                age=patient.age,
                gender=patient.gender.value,
                mobile_number=patient.mobile_number
            ),
            doctor=DoctorInfo(
                doctor_id=doctor.doctor_id,
                name=doctor.name,
                department=doctor.department,
                new_patient_fee=doctor.new_patient_fee,
                followup_fee=doctor.followup_fee
            )
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating OPD visit: {str(e)}"
        )


@router.post("/opd/followup", response_model=VisitDetailResponse, status_code=status.HTTP_201_CREATED)
async def register_followup(
    request: FollowUpRegistrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Register a follow-up patient visit
    
    - Validates patient exists and has previous visits
    - Automatically populates department from doctor
    - Generates new serial number (daily reset per doctor)
    - Calculates follow-up fee based on doctor's follow-up fee
    - Supports Cash, UPI, and Card payment modes
    """
    # Validate patient exists
    patient = await patient_crud.get_patient_by_id(db, request.patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {request.patient_id} not found"
        )
    
    # Check if patient has previous visits
    previous_visits = await visit_crud.get_patient_visits(db, request.patient_id, limit=1)
    if not previous_visits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient has no previous visits. Please register as new OPD patient."
        )
    
    # Validate doctor exists and is active
    doctor = await doctor_crud.get_doctor_by_id(db, request.doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {request.doctor_id} not found"
        )
    
    try:
        # Create follow-up visit
        visit = await visit_crud.create_visit(
            db=db,
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            visit_type=VisitType.OPD_FOLLOWUP,
            payment_mode=PaymentMode[request.payment_mode],
            visit_date=request.visit_date,
            visit_time=request.visit_time
        )
        
        # Prepare response with patient and doctor info
        response = VisitDetailResponse(
            visit_id=visit.visit_id,
            patient_id=visit.patient_id,
            visit_type=visit.visit_type.value,
            doctor_id=visit.doctor_id,
            department=visit.department,
            serial_number=visit.serial_number,
            visit_date=visit.visit_date,
            visit_time=visit.visit_time,
            opd_fee=visit.opd_fee,
            payment_mode=visit.payment_mode.value,
            status=visit.status.value,
            created_date=visit.created_date,
            patient=PatientInfo(
                patient_id=patient.patient_id,
                name=patient.name,
                age=patient.age,
                gender=patient.gender.value,
                mobile_number=patient.mobile_number
            ),
            doctor=DoctorInfo(
                doctor_id=doctor.doctor_id,
                name=doctor.name,
                department=doctor.department,
                new_patient_fee=doctor.new_patient_fee,
                followup_fee=doctor.followup_fee
            )
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating follow-up visit: {str(e)}"
        )


@router.get("/followup/search", response_model=List[FollowUpPatientInfo])
async def search_followup_patients(
    search_term: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Search for patients eligible for follow-up visits
    
    - Search by patient ID or mobile number
    - Returns patients with previous visit history
    - Shows last visit information
    """
    try:
        follow_up_data = await visit_crud.get_follow_up_patients(db, search_term)
        
        results = []
        for data in follow_up_data:
            patient = data["patient"]
            last_visit = data["last_visit"]
            
            results.append(FollowUpPatientInfo(
                patient=PatientInfo(
                    patient_id=patient.patient_id,
                    name=patient.name,
                    age=patient.age,
                    gender=patient.gender.value,
                    mobile_number=patient.mobile_number
                ),
                last_visit_date=last_visit.visit_date,
                last_visit_doctor=last_visit.doctor_id,
                last_visit_department=last_visit.department
            ))
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching follow-up patients: {str(e)}"
        )


@router.get("/{visit_id}", response_model=VisitDetailResponse)
async def get_visit(
    visit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get visit details by ID with patient and doctor information"""
    visit = await visit_crud.get_visit_with_details(db, visit_id)
    if not visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visit with ID {visit_id} not found"
        )
    
    # Prepare response
    response = VisitDetailResponse(
        visit_id=visit.visit_id,
        patient_id=visit.patient_id,
        visit_type=visit.visit_type.value,
        doctor_id=visit.doctor_id,
        department=visit.department,
        serial_number=visit.serial_number,
        visit_date=visit.visit_date,
        visit_time=visit.visit_time,
        opd_fee=visit.opd_fee,
        payment_mode=visit.payment_mode.value,
        status=visit.status.value,
        created_date=visit.created_date
    )
    
    # Add patient info if available
    if visit.patient:
        response.patient = PatientInfo(
            patient_id=visit.patient.patient_id,
            name=visit.patient.name,
            age=visit.patient.age,
            gender=visit.patient.gender.value,
            mobile_number=visit.patient.mobile_number
        )
    
    # Add doctor info if available
    if visit.doctor:
        response.doctor = DoctorInfo(
            doctor_id=visit.doctor.doctor_id,
            name=visit.doctor.name,
            department=visit.doctor.department,
            new_patient_fee=visit.doctor.new_patient_fee,
            followup_fee=visit.doctor.followup_fee
        )
    
    return response


@router.get("/recent/list", response_model=List[VisitDetailResponse])
async def get_recent_visits(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent visits (Public endpoint for dashboard)
    
    - Returns most recent visits with patient and doctor info
    - No authentication required for dashboard display
    """
    try:
        visits = await visit_crud.get_recent_visits(db, limit=limit)
        
        results = []
        for visit in visits:
            response = VisitDetailResponse(
                visit_id=visit.visit_id,
                patient_id=visit.patient_id,
                visit_type=visit.visit_type.value,
                doctor_id=visit.doctor_id,
                department=visit.department,
                serial_number=visit.serial_number,
                visit_date=visit.visit_date,
                visit_time=visit.visit_time,
                opd_fee=visit.opd_fee,
                payment_mode=visit.payment_mode.value,
                status=visit.status.value,
                created_date=visit.created_date
            )
            
            # Add patient info if available
            if visit.patient:
                response.patient = PatientInfo(
                    patient_id=visit.patient.patient_id,
                    name=visit.patient.name,
                    age=visit.patient.age,
                    gender=visit.patient.gender.value,
                    mobile_number=visit.patient.mobile_number
                )
            
            # Add doctor info if available
            if visit.doctor:
                response.doctor = DoctorInfo(
                    doctor_id=visit.doctor.doctor_id,
                    name=visit.doctor.name,
                    department=visit.doctor.department,
                    new_patient_fee=visit.doctor.new_patient_fee,
                    followup_fee=visit.doctor.followup_fee
                )
            
            results.append(response)
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving recent visits: {str(e)}"
        )


@router.get("/patient/{patient_id}", response_model=List[VisitDetailResponse])
async def get_patient_visits(
    patient_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all visits for a patient (Public endpoint for billing)
    
    - Returns patient's visit history
    - Most recent visits first
    - No authentication required for billing workflow
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.visit import Visit
    
    try:
        # Load visits with relationships
        result = await db.execute(
            select(Visit)
            .options(selectinload(Visit.patient), selectinload(Visit.doctor))
            .where(Visit.patient_id == patient_id)
            .order_by(Visit.visit_date.desc(), Visit.visit_time.desc())
            .limit(limit)
        )
        visits = result.scalars().all()
        
        results = []
        for visit in visits:
            response = VisitDetailResponse(
                visit_id=visit.visit_id,
                patient_id=visit.patient_id,
                visit_type=visit.visit_type.value,
                doctor_id=visit.doctor_id,
                department=visit.department,
                serial_number=visit.serial_number,
                visit_date=visit.visit_date,
                visit_time=visit.visit_time,
                opd_fee=visit.opd_fee,
                payment_mode=visit.payment_mode.value,
                status=visit.status.value,
                created_date=visit.created_date
            )
            
            # Add patient info if available
            if visit.patient:
                response.patient = PatientInfo(
                    patient_id=visit.patient.patient_id,
                    name=visit.patient.name,
                    age=visit.patient.age,
                    gender=visit.patient.gender.value,
                    mobile_number=visit.patient.mobile_number
                )
            
            # Add doctor info if available
            if visit.doctor:
                response.doctor = DoctorInfo(
                    doctor_id=visit.doctor.doctor_id,
                    name=visit.doctor.name,
                    department=visit.doctor.department,
                    new_patient_fee=visit.doctor.new_patient_fee,
                    followup_fee=visit.doctor.followup_fee
                )
            
            results.append(response)
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving patient visits: {str(e)}"
        )


@router.get("/{visit_id}/slip")
async def generate_visit_slip(
    visit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate and return visit slip"""
    # TODO: Implement slip generation logic in Task 11.1
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Slip generation will be implemented in Task 11.1"
    )