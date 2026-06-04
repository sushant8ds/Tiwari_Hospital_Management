"""
Pydantic schemas for audit logs
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models.audit import ActionType


class AuditLogResponse(BaseModel):
    """Audit log response schema"""
    log_id: str
    user_id: str
    action_type: ActionType
    table_name: str
    record_id: str
    old_value: Optional[str]
    new_value: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True
        orm_mode = True
