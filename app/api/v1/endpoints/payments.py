"""
Payment endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.payment import PaymentType
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    AdvancePaymentRequest,
    PaymentHistoryResponse,
    PatientBalanceResponse
)
from app.crud.payment import payment_crud
from decimal import Decimal


router = APIRouter()


@router.post("/create", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_public(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new payment record (Public endpoint for billing workflow)
    
    - **patient_id**: Patient ID
    - **amount**: Payment amount
    - **payment_mode**: Payment mode (CASH, UPI, CARD)
    - **payment_type**: Type of payment
    - **visit_id**: Visit ID (optional)
    - **ipd_id**: IPD ID (optional)
    - **transaction_reference**: Transaction reference for UPI/Card (optional)
    - **notes**: Additional notes (optional)
    """
    try:
        # Convert payment_type string to enum
        try:
            payment_type_enum = PaymentType[payment_data.payment_type.upper()]
        except KeyError:
            raise ValueError(f"Invalid payment type: {payment_data.payment_type}")
        
        payment = await payment_crud.create_payment(
            db=db,
            patient_id=payment_data.patient_id,
            amount=payment_data.amount,
            payment_mode=payment_data.payment_mode,
            payment_type=payment_type_enum,
            created_by=payment_data.created_by or "SYSTEM",
            visit_id=payment_data.visit_id,
            ipd_id=payment_data.ipd_id,
            transaction_reference=payment_data.transaction_reference,
            notes=payment_data.notes
        )
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new payment record
    
    - **patient_id**: Patient ID
    - **amount**: Payment amount
    - **payment_mode**: Payment mode (CASH, UPI, CARD)
    - **payment_type**: Type of payment
    - **visit_id**: Visit ID (optional)
    - **ipd_id**: IPD ID (optional)
    - **transaction_reference**: Transaction reference for UPI/Card (optional)
    - **notes**: Additional notes (optional)
    """
    try:
        # Convert payment_type string to enum
        try:
            payment_type_enum = PaymentType[payment_data.payment_type.upper()]
        except KeyError:
            raise ValueError(f"Invalid payment type: {payment_data.payment_type}")
        
        payment = await payment_crud.create_payment(
            db=db,
            patient_id=payment_data.patient_id,
            amount=payment_data.amount,
            payment_mode=payment_data.payment_mode,
            payment_type=payment_type_enum,
            created_by=current_user.user_id,
            visit_id=payment_data.visit_id,
            ipd_id=payment_data.ipd_id,
            transaction_reference=payment_data.transaction_reference,
            notes=payment_data.notes
        )
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.post("/ipd/{ipd_id}/advance", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_advance_payment(
    ipd_id: str,
    payment_data: AdvancePaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record an advance payment for IPD admission
    
    - **ipd_id**: IPD admission ID
    - **amount**: Advance payment amount
    - **payment_mode**: Payment mode (CASH, UPI, CARD)
    - **transaction_reference**: Transaction reference for UPI/Card (optional)
    - **notes**: Additional notes (optional)
    """
    try:
        payment = await payment_crud.record_advance_payment(
            db=db,
            ipd_id=ipd_id,
            amount=payment_data.amount,
            payment_mode=payment_data.payment_mode,
            created_by=current_user.user_id,
            transaction_reference=payment_data.transaction_reference,
            notes=payment_data.notes
        )
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record advance payment: {str(e)}"
        )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment by ID"""
    payment = await payment_crud.get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment


@router.get("/patient/{patient_id}", response_model=PaymentHistoryResponse)
async def get_patient_payments(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all payments for a patient"""
    payments = await payment_crud.get_payments_by_patient(db, patient_id)
    total_paid = sum(p.amount for p in payments)
    
    return {
        "payments": payments,
        "total_paid": total_paid
    }


@router.get("/visit/{visit_id}", response_model=List[PaymentResponse])
async def get_visit_payments(
    visit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all payments for a visit"""
    payments = await payment_crud.get_payments_by_visit(db, visit_id)
    return payments


@router.get("/ipd/{ipd_id}", response_model=List[PaymentResponse])
async def get_ipd_payments(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all payments for an IPD admission"""
    payments = await payment_crud.get_payments_by_ipd(db, ipd_id)
    return payments


@router.get("/ipd/{ipd_id}/advance", response_model=List[PaymentResponse])
async def get_ipd_advance_payments(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all advance payments for an IPD admission"""
    payments = await payment_crud.get_advance_payments(db, ipd_id)
    return payments


@router.get("/patient/{patient_id}/balance", response_model=PatientBalanceResponse)
async def get_patient_balance(
    patient_id: str,
    visit_id: str = None,
    ipd_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get patient balance (charges - payments)
    
    - **patient_id**: Patient ID
    - **visit_id**: Visit ID (optional, for visit-specific balance)
    - **ipd_id**: IPD ID (optional, for IPD-specific balance)
    """
    try:
        balance = await payment_crud.calculate_patient_balance(
            db=db,
            patient_id=patient_id,
            visit_id=visit_id,
            ipd_id=ipd_id
        )
        return balance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate balance: {str(e)}"
        )
