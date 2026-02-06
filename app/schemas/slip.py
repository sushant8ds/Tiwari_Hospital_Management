"""
Pydantic schemas for Slip operations
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SlipTypeEnum(str, Enum):
    """Slip type options"""
    OPD = "OPD"
    INVESTIGATION = "INVESTIGATION"
    PROCEDURE = "PROCEDURE"
    SERVICE = "SERVICE"
    OT = "OT"
    DISCHARGE = "DISCHARGE"


class PrinterFormatEnum(str, Enum):
    """Printer format options"""
    A4 = "A4"
    THERMAL = "THERMAL"


class SlipGenerateRequest(BaseModel):
    """Request schema for generating a slip"""
    visit_id: Optional[str] = None
    ipd_id: Optional[str] = None
    slip_type: SlipTypeEnum
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4


class SlipReprintRequest(BaseModel):
    """Request schema for reprinting a slip"""
    original_slip_id: str


class SlipResponse(BaseModel):
    """Response schema for slip"""
    slip_id: str
    patient_id: str
    visit_id: Optional[str]
    ipd_id: Optional[str]
    slip_type: str
    barcode_data: str
    barcode_image: Optional[str]
    slip_content: str
    printer_format: str
    is_reprinted: bool
    original_slip_id: Optional[str]
    generated_date: datetime
    generated_by: str
    
    class Config:
        from_attributes = True


class SlipContentResponse(BaseModel):
    """Response schema for slip content (parsed JSON)"""
    slip_id: str
    patient_id: str
    slip_type: str
    barcode_data: str
    barcode_image: Optional[str]
    content: Dict[str, Any]
    printer_format: str
    generated_date: datetime
    
    class Config:
        from_attributes = True
