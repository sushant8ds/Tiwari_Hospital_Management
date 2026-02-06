"""
API endpoints for slip generation and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json

from app.core.dependencies import get_db, get_current_user
from app.crud.slip import slip_crud
from app.schemas.slip import (
    SlipGenerateRequest,
    SlipReprintRequest,
    SlipResponse,
    SlipContentResponse,
    PrinterFormatEnum
)
from app.models.slip import PrinterFormat
from app.models.user import User

router = APIRouter()


@router.post("/generate/opd/{visit_id}", response_model=SlipContentResponse)
async def generate_opd_slip(
    visit_id: str,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate OPD slip"""
    try:
        slip = await slip_crud.generate_opd_slip(
            db=db,
            visit_id=visit_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate/investigation", response_model=SlipContentResponse)
async def generate_investigation_slip(
    visit_id: str = None,
    ipd_id: str = None,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate investigation slip"""
    try:
        slip = await slip_crud.generate_investigation_slip(
            db=db,
            visit_id=visit_id,
            ipd_id=ipd_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate/procedure", response_model=SlipContentResponse)
async def generate_procedure_slip(
    visit_id: str = None,
    ipd_id: str = None,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate procedure slip"""
    try:
        slip = await slip_crud.generate_procedure_slip(
            db=db,
            visit_id=visit_id,
            ipd_id=ipd_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate/service", response_model=SlipContentResponse)
async def generate_service_slip(
    visit_id: str = None,
    ipd_id: str = None,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate service slip"""
    try:
        slip = await slip_crud.generate_service_slip(
            db=db,
            visit_id=visit_id,
            ipd_id=ipd_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate/ot/{ipd_id}", response_model=SlipContentResponse)
async def generate_ot_slip(
    ipd_id: str,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate OT slip"""
    try:
        slip = await slip_crud.generate_ot_slip(
            db=db,
            ipd_id=ipd_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate/discharge/{ipd_id}", response_model=SlipContentResponse)
async def generate_discharge_slip(
    ipd_id: str,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate discharge slip"""
    try:
        slip = await slip_crud.generate_discharge_slip(
            db=db,
            ipd_id=ipd_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/reprint/{slip_id}", response_model=SlipContentResponse)
async def reprint_slip(
    slip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reprint an existing slip"""
    try:
        slip = await slip_crud.reprint_slip(
            db=db,
            original_slip_id=slip_id,
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{slip_id}", response_model=SlipContentResponse)
async def get_slip(
    slip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get slip by ID"""
    slip = await slip_crud.get_slip_by_id(db, slip_id)
    if not slip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slip not found")
    
    return SlipContentResponse(
        slip_id=slip.slip_id,
        patient_id=slip.patient_id,
        slip_type=slip.slip_type.value,
        barcode_data=slip.barcode_data,
        barcode_image=slip.barcode_image,
        content=json.loads(slip.slip_content),
        printer_format=slip.printer_format.value,
        generated_date=slip.generated_date
    )


@router.get("/patient/{patient_id}", response_model=List[SlipResponse])
async def get_patient_slips(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all slips for a patient"""
    slips = await slip_crud.get_slips_by_patient(db, patient_id)
    return slips


@router.get("/visit/{visit_id}", response_model=List[SlipResponse])
async def get_visit_slips(
    visit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all slips for a visit"""
    slips = await slip_crud.get_slips_by_visit(db, visit_id)
    return slips


@router.get("/ipd/{ipd_id}", response_model=List[SlipResponse])
async def get_ipd_slips(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all slips for an IPD admission"""
    slips = await slip_crud.get_slips_by_ipd(db, ipd_id)
    return slips
