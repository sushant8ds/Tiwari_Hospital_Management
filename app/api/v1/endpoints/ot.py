"""
Operation Theater (OT) endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.ot import (
    OTProcedureCreate,
    OTProcedureResponse,
    OTChargesRequest,
    OTChargesResponse
)
from app.schemas.billing import BillingChargeResponse
from app.crud.ot import ot_crud
from decimal import Decimal


router = APIRouter()


@router.post("/procedures", response_model=OTProcedureResponse, status_code=status.HTTP_201_CREATED)
async def create_ot_procedure(
    procedure_data: OTProcedureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new OT procedure record
    
    - **ipd_id**: IPD admission ID
    - **operation_name**: Name of the operation
    - **operation_date**: Date and time of operation
    - **duration_minutes**: Duration in minutes
    - **surgeon_name**: Name of the surgeon
    - **anesthesia_type**: Type of anesthesia (optional)
    - **notes**: Additional notes (optional)
    """
    try:
        ot_procedure = await ot_crud.create_ot_procedure(
            db=db,
            ipd_id=procedure_data.ipd_id,
            operation_name=procedure_data.operation_name,
            operation_date=procedure_data.operation_date,
            duration_minutes=procedure_data.duration_minutes,
            surgeon_name=procedure_data.surgeon_name,
            anesthesia_type=procedure_data.anesthesia_type,
            notes=procedure_data.notes,
            created_by=current_user.user_id
        )
        return ot_procedure
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create OT procedure: {str(e)}"
        )


@router.post("/{ot_id}/charges", response_model=List[BillingChargeResponse], status_code=status.HTTP_201_CREATED)
async def add_ot_charges(
    ot_id: str,
    charges_data: OTChargesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add OT charges to billing
    
    - **ot_id**: OT procedure ID
    - **surgeon_charge**: Surgeon fee
    - **anesthesia_charge**: Anesthesia fee
    - **facility_charge**: OT facility fee
    - **assistant_charge**: Assistant fee (optional)
    """
    try:
        # Get OT procedure to get IPD ID
        ot_procedure = await ot_crud.get_ot_procedure_by_id(db, ot_id)
        if not ot_procedure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OT procedure not found"
            )
        
        charges = await ot_crud.add_ot_charges(
            db=db,
            ipd_id=ot_procedure.ipd_id,
            ot_id=ot_id,
            surgeon_charge=charges_data.surgeon_charge,
            anesthesia_charge=charges_data.anesthesia_charge,
            facility_charge=charges_data.facility_charge,
            assistant_charge=charges_data.assistant_charge,
            created_by=current_user.user_id
        )
        return charges
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add OT charges: {str(e)}"
        )


@router.get("/procedures/{ot_id}", response_model=OTProcedureResponse)
async def get_ot_procedure(
    ot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get OT procedure by ID"""
    ot_procedure = await ot_crud.get_ot_procedure_by_id(db, ot_id)
    if not ot_procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OT procedure not found"
        )
    return ot_procedure


@router.get("/ipd/{ipd_id}/procedures", response_model=List[OTProcedureResponse])
async def get_ipd_ot_procedures(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all OT procedures for an IPD admission"""
    procedures = await ot_crud.get_ot_procedures_by_ipd(db, ipd_id)
    return procedures


@router.get("/ipd/{ipd_id}/charges", response_model=List[BillingChargeResponse])
async def get_ipd_ot_charges(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all OT charges for an IPD admission"""
    charges = await ot_crud.get_ot_charges_by_ipd(db, ipd_id)
    return charges
