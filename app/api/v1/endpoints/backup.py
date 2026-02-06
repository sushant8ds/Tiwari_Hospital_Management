"""
API endpoints for backup and recovery operations
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.crud.backup import backup_crud
from app.schemas.backup import (
    BackupCreateRequest,
    BackupResponse,
    BackupListResponse,
    BackupValidationResponse,
    BackupRestoreRequest,
    BackupRestoreResponse,
    DataExportRequest,
    DataExportResponse
)


router = APIRouter()


@router.post("/create", response_model=BackupResponse)
async def create_backup(
    request: BackupCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """
    Create a complete database backup (Admin only)
    
    Creates a JSON backup file containing all patient, billing, and system data.
    """
    try:
        backup_result = await backup_crud.create_backup(
            db=db,
            backup_name=request.backup_name
        )
        return backup_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup creation failed: {str(e)}"
        )


@router.get("/list", response_model=List[BackupListResponse])
async def list_backups(
    current_user: User = Depends(require_admin())
):
    """
    List all available backups (Admin only)
    
    Returns a list of all backup files with metadata.
    """
    try:
        backups = backup_crud.list_backups()
        return backups
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.get("/validate/{backup_name}", response_model=BackupValidationResponse)
async def validate_backup(
    backup_name: str,
    current_user: User = Depends(require_admin())
):
    """
    Validate backup file integrity (Admin only)
    
    Checks if the backup file is valid and contains all required data.
    """
    try:
        validation_result = backup_crud.validate_backup(backup_name)
        return validation_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/restore", response_model=BackupRestoreResponse)
async def restore_backup(
    request: BackupRestoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """
    Restore database from backup (Admin only)
    
    WARNING: This operation can overwrite existing data if clear_existing=True
    """
    try:
        restore_result = await backup_crud.restore_backup(
            db=db,
            backup_name=request.backup_name,
            clear_existing=request.clear_existing
        )
        return restore_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}"
        )


@router.post("/export", response_model=DataExportResponse)
async def export_data(
    request: DataExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """
    Export specific data types (Admin only)
    
    Exports patient, billing, or other data based on the export_type parameter.
    """
    try:
        export_result = await backup_crud.export_data(
            db=db,
            export_type=request.export_type,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return export_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )
