"""
API endpoints for discharge processing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
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
