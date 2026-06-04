"""
Schemas for backup and recovery endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class BackupCreateRequest(BaseModel):
    """Request schema for creating a backup"""
    backup_name: Optional[str] = Field(None, description="Optional custom backup name")


class BackupResponse(BaseModel):
    """Response schema for backup creation"""
    backup_name: str
    backup_file: str
    backup_date: str
    file_size_bytes: int
    file_size_mb: float
    record_counts: Dict[str, int]


class BackupListResponse(BaseModel):
    """Response schema for listing backups"""
    backup_name: str
    backup_file: str
    file_size_bytes: int
    file_size_mb: float
    created_date: str


class BackupValidationResponse(BaseModel):
    """Response schema for backup validation"""
    valid: bool
    backup_name: Optional[str] = None
    backup_date: Optional[str] = None
    record_counts: Optional[Dict[str, int]] = None
    error: Optional[str] = None


class BackupRestoreRequest(BaseModel):
    """Request schema for restoring a backup"""
    backup_name: str = Field(..., description="Name of the backup to restore")
    clear_existing: bool = Field(False, description="Whether to clear existing data before restore")


class BackupRestoreResponse(BaseModel):
    """Response schema for backup restoration"""
    restored: bool
    backup_name: str
    backup_date: str
    restore_date: str
    record_counts: Dict[str, int]
    note: str


class DataExportRequest(BaseModel):
    """Request schema for data export"""
    export_type: str = Field("all", description="Type of data to export: all, patients, billing, visits, ipd")
    start_date: Optional[str] = Field(None, description="Start date for filtered export (ISO format)")
    end_date: Optional[str] = Field(None, description="End date for filtered export (ISO format)")


class DataExportResponse(BaseModel):
    """Response schema for data export"""
    export_name: str
    export_file: str
    export_date: str
    file_size_bytes: int
    file_size_mb: float
