"""
IPD management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.ipd import (
    IPDCreate, IPDResponse, BedCreate, BedResponse,
    BedChangeRequest, DischargeRequest, BedOccupancyResponse
)
from app.schemas.auth import UserResponse
from app.crud.ipd import ipd_crud, bed_crud
from app.models.bed import WardType, BedStatus
from app.models.ipd import IPDStatus

router = APIRouter()


@router.post("/admit", response_model=IPDResponse)
async def admit_patient(
    ipd: IPDCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Admit a patient to IPD (Public endpoint for reception)
    
    - Converts OPD to IPD or admits new patient
    - Generates unique IPD_Number
    - Charges one-time file charge
    - Allocates bed
    """
    try:
        ipd_admission = await ipd_crud.admit_patient(
            db=db,
            patient_id=ipd.patient_id,
            bed_id=ipd.bed_id,
            file_charge=ipd.file_charge,
            visit_id=ipd.visit_id,
            admission_date=ipd.admission_date
        )
        return ipd_admission
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error admitting patient: {str(e)}")


@router.get("/{ipd_id}", response_model=IPDResponse)
async def get_ipd(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get IPD details by ID"""
    ipd = await ipd_crud.get_ipd_by_id(db, ipd_id)
    if not ipd:
        raise HTTPException(status_code=404, detail="IPD admission not found")
    return ipd


@router.get("/patient/{patient_id}", response_model=List[IPDResponse])
async def get_patient_ipd_history(
    patient_id: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all IPD admissions for a patient"""
    try:
        ipd_status = IPDStatus[status] if status else None
        admissions = await ipd_crud.get_ipd_by_patient(db, patient_id, ipd_status)
        return admissions
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving IPD history: {str(e)}")


@router.get("/active/list", response_model=List[IPDResponse])
async def get_active_admissions(
    db: AsyncSession = Depends(get_db)
):
    """Get all active IPD admissions (Public endpoint for dashboard)"""
    admissions = await ipd_crud.get_active_ipd_admissions(db)
    return admissions


@router.post("/{ipd_id}/change-bed", response_model=IPDResponse)
async def change_bed(
    ipd_id: str,
    bed_change: BedChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Change bed allocation for an IPD patient"""
    try:
        ipd = await ipd_crud.change_bed(db, ipd_id, bed_change.new_bed_id)
        return ipd
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error changing bed: {str(e)}")


@router.post("/{ipd_id}/discharge", response_model=IPDResponse)
async def discharge_patient(
    ipd_id: str,
    discharge_req: DischargeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Discharge a patient from IPD"""
    try:
        ipd = await ipd_crud.discharge_patient(db, ipd_id, discharge_req.discharge_date)
        return ipd
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discharging patient: {str(e)}")


@router.get("/{ipd_id}/bed-charges")
async def get_bed_charges(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Calculate total bed charges for an IPD admission"""
    try:
        total_charges = await ipd_crud.calculate_bed_charges(db, ipd_id)
        return {"ipd_id": ipd_id, "total_bed_charges": total_charges}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating bed charges: {str(e)}")


# Bed Management Endpoints

@router.post("/beds", response_model=BedResponse)
async def create_bed(
    bed: BedCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new bed (Admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admin can create beds")
    
    try:
        ward_type = WardType[bed.ward_type]
        new_bed = await bed_crud.create_bed(
            db=db,
            bed_number=bed.bed_number,
            ward_type=ward_type,
            per_day_charge=bed.per_day_charge
        )
        return new_bed
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid ward type: {bed.ward_type}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating bed: {str(e)}")


@router.get("/beds/available", response_model=List[BedResponse])
async def get_available_beds(
    ward_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all available beds (Public endpoint for reception)"""
    try:
        ward_type_enum = WardType[ward_type] if ward_type else None
        beds = await bed_crud.get_available_beds(db, ward_type_enum)
        return beds
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid ward type: {ward_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving beds: {str(e)}")


@router.get("/beds/occupancy", response_model=BedOccupancyResponse)
async def get_bed_occupancy(
    db: AsyncSession = Depends(get_db)
):
    """Get current bed occupancy status (Public endpoint)"""
    try:
        stats = await bed_crud.get_bed_occupancy_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving occupancy stats: {str(e)}")


@router.get("/beds/{bed_id}", response_model=BedResponse)
async def get_bed(
    bed_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get bed details by ID"""
    bed = await bed_crud.get_bed_by_id(db, bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    return bed


@router.get("/beds/ward/{ward_type}", response_model=List[BedResponse])
async def get_beds_by_ward(
    ward_type: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get beds by ward type"""
    try:
        ward_type_enum = WardType[ward_type]
        bed_status = BedStatus[status] if status else None
        beds = await bed_crud.get_beds_by_ward_type(db, ward_type_enum, bed_status)
        return beds
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving beds: {str(e)}")