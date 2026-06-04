"""
Pydantic schemas for discharge operations
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class DischargeProcessRequest(BaseModel):
    """Request schema for processing discharge"""
    discharge_date: Optional[datetime] = None


class DischargeBillResponse(BaseModel):
    """Response schema for discharge bill"""
    ipd_id: str
    patient: Dict[str, Any]
    admission: Dict[str, Any]
    charges_by_type: Dict[str, List[Dict[str, Any]]]
    payments: List[Dict[str, Any]]
    summary: Dict[str, float]
    generated_date: str


class DischargeResponse(BaseModel):
    """Response schema for discharge processing"""
    ipd_id: str
    patient_id: str
    admission_date: datetime
    discharge_date: Optional[datetime]
    status: str
    
    class Config:
        from_attributes = True
