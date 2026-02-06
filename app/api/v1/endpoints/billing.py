"""
Billing management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.billing import (
    BillingChargeCreate, 
    BillingChargeResponse,
    InvestigationChargeRequest,
    ProcedureChargeRequest,
    ServiceChargeRequest,
    ManualChargeRequest,
    DischargeBillResponse
)
from app.crud.billing import billing_crud
from app.models.user import User

router = APIRouter()


@router.post("/{visit_id}/investigations", response_model=List[BillingChargeResponse])
async def add_investigation_charges(
    visit_id: str,
    investigations: List[InvestigationChargeRequest],
    db: AsyncSession = Depends(get_db)
):
    """Add investigation charges to a visit (Public endpoint for reception)"""
    try:
        # Convert to dict format for CRUD
        investigation_data = [
            {
                "name": inv.charge_name,
                "rate": inv.rate,
                "quantity": inv.quantity
            }
            for inv in investigations
        ]
        
        charges = await billing_crud.add_investigation_charges(
            db=db,
            visit_id=visit_id,
            ipd_id=None,
            investigations=investigation_data,
            created_by="SYSTEM"  # Default user for public endpoint
        )
        
        return charges
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{visit_id}/procedures", response_model=List[BillingChargeResponse])
async def add_procedure_charges(
    visit_id: str,
    procedures: List[ProcedureChargeRequest],
    db: AsyncSession = Depends(get_db)
):
    """Add procedure charges to a visit (Public endpoint for reception)"""
    try:
        # Convert to dict format for CRUD
        procedure_data = [
            {
                "name": proc.charge_name,
                "rate": proc.rate,
                "quantity": proc.quantity
            }
            for proc in procedures
        ]
        
        charges = await billing_crud.add_procedure_charges(
            db=db,
            visit_id=visit_id,
            ipd_id=None,
            procedures=procedure_data,
            created_by="SYSTEM"
        )
        
        return charges
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{visit_id}/services", response_model=List[BillingChargeResponse])
async def add_service_charges(
    visit_id: str,
    services: List[ServiceChargeRequest],
    db: AsyncSession = Depends(get_db)
):
    """Add service charges to a visit with time calculation (Public endpoint for reception)"""
    try:
        # Convert to dict format for CRUD
        service_data = [
            {
                "name": svc.charge_name,
                "rate": svc.rate,
                "quantity": svc.quantity,
                "start_time": svc.start_time,
                "end_time": svc.end_time
            }
            for svc in services
        ]
        
        charges = await billing_crud.add_service_charges(
            db=db,
            visit_id=visit_id,
            ipd_id=None,
            services=service_data,
            created_by="SYSTEM"
        )
        
        return charges
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{visit_id}/manual-charges", response_model=List[BillingChargeResponse])
async def add_manual_charges(
    visit_id: str,
    manual_charges: List[ManualChargeRequest],
    db: AsyncSession = Depends(get_db)
):
    """Add manual charges to a visit (Public endpoint for reception)"""
    try:
        # Convert to dict format for CRUD
        manual_data = [
            {
                "name": charge.charge_name,
                "rate": charge.rate,
                "quantity": charge.quantity
            }
            for charge in manual_charges
        ]
        
        charges = await billing_crud.add_manual_charges(
            db=db,
            visit_id=visit_id,
            ipd_id=None,
            manual_charges=manual_data,
            created_by="SYSTEM"
        )
        
        return charges
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{visit_id}/charges", response_model=List[BillingChargeResponse])
async def get_visit_charges(
    visit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all charges for a visit"""
    try:
        charges = await billing_crud.get_charges_by_visit(db, visit_id)
        return charges
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{visit_id}/total", response_model=dict)
async def get_visit_total(
    visit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get total charges for a visit"""
    try:
        total = await billing_crud.calculate_total_charges(db, visit_id=visit_id)
        return {"visit_id": visit_id, "total_charges": total}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/ipd/{ipd_id}/investigations", response_model=List[BillingChargeResponse])
async def add_ipd_investigation_charges(
    ipd_id: str,
    investigations: List[InvestigationChargeRequest],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add investigation charges to an IPD admission"""
    try:
        # Convert to dict format for CRUD
        investigation_data = [
            {
                "name": inv.charge_name,
                "rate": inv.rate,
                "quantity": inv.quantity
            }
            for inv in investigations
        ]
        
        charges = await billing_crud.add_investigation_charges(
            db=db,
            visit_id=None,
            ipd_id=ipd_id,
            investigations=investigation_data,
            created_by=current_user.user_id
        )
        
        return charges
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/ipd/{ipd_id}/procedures", response_model=List[BillingChargeResponse])
async def add_ipd_procedure_charges(
    ipd_id: str,
    procedures: List[ProcedureChargeRequest],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add procedure charges to an IPD admission"""
    try:
        # Convert to dict format for CRUD
        procedure_data = [
            {
                "name": proc.charge_name,
                "rate": proc.rate,
                "quantity": proc.quantity
            }
            for proc in procedures
        ]
        
        charges = await billing_crud.add_procedure_charges(
            db=db,
            visit_id=None,
            ipd_id=ipd_id,
            procedures=procedure_data,
            created_by=current_user.user_id
        )
        
        return charges
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/ipd/{ipd_id}/services", response_model=List[BillingChargeResponse])
async def add_ipd_service_charges(
    ipd_id: str,
    services: List[ServiceChargeRequest],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add service charges to an IPD admission with time calculation"""
    try:
        # Convert to dict format for CRUD
        service_data = [
            {
                "name": svc.charge_name,
                "rate": svc.rate,
                "quantity": svc.quantity,
                "start_time": svc.start_time,
                "end_time": svc.end_time
            }
            for svc in services
        ]
        
        charges = await billing_crud.add_service_charges(
            db=db,
            visit_id=None,
            ipd_id=ipd_id,
            services=service_data,
            created_by=current_user.user_id
        )
        
        return charges
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/ipd/{ipd_id}/charges", response_model=List[BillingChargeResponse])
async def get_ipd_charges(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all charges for an IPD admission"""
    try:
        charges = await billing_crud.get_charges_by_ipd(db, ipd_id)
        return charges
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/ipd/{ipd_id}/discharge-bill")
async def generate_discharge_bill(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate discharge bill for IPD patient"""
    try:
        # Get all charges for the IPD admission
        charges = await billing_crud.get_charges_by_ipd(db, ipd_id)
        total = await billing_crud.calculate_total_charges(db, ipd_id=ipd_id)
        
        # Group charges by type
        charges_by_type = {}
        for charge in charges:
            charge_type = charge.charge_type.value
            if charge_type not in charges_by_type:
                charges_by_type[charge_type] = []
            charges_by_type[charge_type].append(charge)
        
        return {
            "ipd_id": ipd_id,
            "charges": charges,
            "charges_by_type": charges_by_type,
            "total_charges": total
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )