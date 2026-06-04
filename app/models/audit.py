"""
Audit log model for tracking system changes
"""

from sqlalchemy import Column, String, Text, DateTime, Enum
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.core.database import Base


class ActionType(PyEnum):
    """Audit action type options"""
    MANUAL_CHARGE_ADD = "MANUAL_CHARGE_ADD"
    MANUAL_CHARGE_EDIT = "MANUAL_CHARGE_EDIT"
    RATE_CHANGE = "RATE_CHANGE"


class AuditLog(Base):
    """Audit log model for tracking system changes"""
    
    __tablename__ = "audit_logs"
    
    log_id = Column(String(30), primary_key=True)
    user_id = Column(String(20), nullable=False)
    action_type = Column(Enum(ActionType), nullable=False)
    table_name = Column(String(50), nullable=False)
    record_id = Column(String(30), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AuditLog(log_id='{self.log_id}', action='{self.action_type}', user='{self.user_id}')>"