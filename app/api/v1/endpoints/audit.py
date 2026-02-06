"""
API endpoints for audit log management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.crud.audit import audit_crud
from app.schemas.audit import AuditLogResponse
from app.models.user import User, UserRole
from app.models.audit import ActionType

router = APIRouter()


@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent audit logs (Admin only)
    
    - **limit**: Maximum number of logs to return (default: 100, max: 1000)
    """
    # Only admin users can view audit logs
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logs = await audit_crud.get_recent_audit_logs(db, limit=limit)
    return logs


@router.get("/user/{user_id}", response_model=List[AuditLogResponse])
async def get_audit_logs_by_user(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit logs for a specific user (Admin only)
    
    - **user_id**: User ID to filter logs
    - **limit**: Maximum number of logs to return
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logs = await audit_crud.get_audit_logs_by_user(db, user_id=user_id, limit=limit)
    return logs


@router.get("/record/{table_name}/{record_id}", response_model=List[AuditLogResponse])
async def get_audit_logs_by_record(
    table_name: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit logs for a specific record (Admin only)
    
    - **table_name**: Table name (e.g., "billing_charges")
    - **record_id**: Record ID to filter logs
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logs = await audit_crud.get_audit_logs_by_record(
        db, 
        table_name=table_name, 
        record_id=record_id
    )
    return logs


@router.get("/action/{action_type}", response_model=List[AuditLogResponse])
async def get_audit_logs_by_action(
    action_type: ActionType,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit logs by action type (Admin only)
    
    - **action_type**: Action type to filter (MANUAL_CHARGE_ADD, MANUAL_CHARGE_EDIT, RATE_CHANGE)
    - **limit**: Maximum number of logs to return
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logs = await audit_crud.get_audit_logs_by_action_type(
        db, 
        action_type=action_type, 
        limit=limit
    )
    return logs
