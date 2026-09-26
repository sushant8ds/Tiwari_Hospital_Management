"""
API endpoints for discharge processing
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.config import settings
from app.core.templates import templates
from app.crud.discharge import discharge_crud
from app.schemas.discharge import (
    DischargeProcessRequest,
    DischargeBillResponse,
    DischargeResponse
)
from app.models.user import User

router = APIRouter()


@router.get("/{ipd_id}/bill", response_model=DischargeBillResponse)
async def get_discharge_bill(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate discharge bill for IPD"""
    try:
        bill = await discharge_crud.generate_discharge_bill(db, ipd_id)
        return bill
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{ipd_id}/process", response_model=DischargeResponse)
async def process_discharge(
    ipd_id: str,
    request: DischargeProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process patient discharge"""
    try:
        ipd = await discharge_crud.process_discharge(
            db=db,
            ipd_id=ipd_id,
            discharge_date=request.discharge_date
        )
        return ipd
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{ipd_id}/pending-amount")
async def get_pending_amount(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending amount for IPD"""
    try:
        pending = await discharge_crud.calculate_pending_amount(db, ipd_id)
        return {"ipd_id": ipd_id, "pending_amount": float(pending)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{ipd_id}/summary", response_class=HTMLResponse)
async def get_discharge_summary_view(
    request: Request,
    ipd_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate printable clinical discharge summary HTML matching sample PDF"""
    try:
        from app.crud.ipd import ipd_crud
        from datetime import datetime, timedelta
        
        ipd = await ipd_crud.get_ipd_by_id(db, ipd_id)
        if not ipd:
            raise HTTPException(status_code=404, detail="IPD record not found")
        
        admission_date_formatted = ipd.admission_date.strftime("%d-%b-%Y, %I:%M %p") if ipd.admission_date else datetime.now().strftime("%d-%b-%Y, %I:%M %p")
        discharge_date_formatted = ipd.discharge_date.strftime("%d-%b-%Y, %I:%M %p") if ipd.discharge_date else datetime.now().strftime("%d-%b-%Y, %I:%M %p")
        operation_date_formatted = ipd.operation_date.strftime("%d-%b-%Y") if ipd.operation_date else (ipd.admission_date.strftime("%d-%b-%Y") if ipd.admission_date else datetime.now().strftime("%d-%b-%Y"))
        
        follow_up_dt = (ipd.discharge_date or datetime.now()) + timedelta(days=5)
        follow_up_date_formatted = follow_up_dt.strftime("%d-%b-%Y (%A)")
        
        return templates.TemplateResponse(
            request=request,
            name="slips/discharge_summary.html",
            context={
                "ipd": ipd,
                "patient": ipd.patient,
                "doctor": ipd.attending_doctor,
                "admission_date_formatted": admission_date_formatted,
                "discharge_date_formatted": discharge_date_formatted,
                "operation_date_formatted": operation_date_formatted,
                "follow_up_date_formatted": follow_up_date_formatted,
                "hospital_name": settings.HOSPITAL_NAME,
                "hospital_address": settings.HOSPITAL_ADDRESS,
                "hospital_phone": settings.HOSPITAL_PHONE
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating discharge summary: {str(e)}")

