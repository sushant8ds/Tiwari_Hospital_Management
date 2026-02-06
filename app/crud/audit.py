"""
CRUD operations for audit logging
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional, List
import json

from app.models.audit import AuditLog, ActionType
from app.services.id_generator import generate_id


class AuditCRUD:
    """CRUD operations for audit logs"""
    
    async def create_audit_log(
        self,
        db: AsyncSession,
        user_id: str,
        action_type: ActionType,
        table_name: str,
        record_id: str,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None
    ) -> AuditLog:
        """Create a new audit log entry"""
        try:
            # Generate log ID
            log_id = await generate_id("LOG")
            
            # Convert dict values to JSON strings
            old_value_str = json.dumps(old_value) if old_value else None
            new_value_str = json.dumps(new_value) if new_value else None
            
            # Create audit log
            audit_log = AuditLog(
                log_id=log_id,
                user_id=user_id,
                action_type=action_type,
                table_name=table_name,
                record_id=record_id,
                old_value=old_value_str,
                new_value=new_value_str
            )
            
            db.add(audit_log)
            await db.commit()
            await db.refresh(audit_log)
            
            return audit_log
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def log_manual_charge_add(
        self,
        db: AsyncSession,
        user_id: str,
        charge_id: str,
        charge_data: dict
    ) -> AuditLog:
        """Log manual charge addition"""
        return await self.create_audit_log(
            db=db,
            user_id=user_id,
            action_type=ActionType.MANUAL_CHARGE_ADD,
            table_name="billing_charges",
            record_id=charge_id,
            new_value=charge_data
        )
    
    async def log_manual_charge_edit(
        self,
        db: AsyncSession,
        user_id: str,
        charge_id: str,
        old_data: dict,
        new_data: dict
    ) -> AuditLog:
        """Log manual charge edit"""
        return await self.create_audit_log(
            db=db,
            user_id=user_id,
            action_type=ActionType.MANUAL_CHARGE_EDIT,
            table_name="billing_charges",
            record_id=charge_id,
            old_value=old_data,
            new_value=new_data
        )
    
    async def log_rate_change(
        self,
        db: AsyncSession,
        user_id: str,
        table_name: str,
        record_id: str,
        old_rate: float,
        new_rate: float
    ) -> AuditLog:
        """Log rate change"""
        return await self.create_audit_log(
            db=db,
            user_id=user_id,
            action_type=ActionType.RATE_CHANGE,
            table_name=table_name,
            record_id=record_id,
            old_value={"rate": old_rate},
            new_value={"rate": new_rate}
        )
    
    async def get_audit_log_by_id(
        self,
        db: AsyncSession,
        log_id: str
    ) -> Optional[AuditLog]:
        """Get audit log by ID"""
        result = await db.execute(
            select(AuditLog).where(AuditLog.log_id == log_id)
        )
        return result.scalar_one_or_none()
    
    async def get_audit_logs_by_user(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific user"""
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_audit_logs_by_record(
        self,
        db: AsyncSession,
        table_name: str,
        record_id: str
    ) -> List[AuditLog]:
        """Get all audit logs for a specific record"""
        result = await db.execute(
            select(AuditLog)
            .where(
                AuditLog.table_name == table_name,
                AuditLog.record_id == record_id
            )
            .order_by(AuditLog.timestamp.desc())
        )
        return result.scalars().all()
    
    async def get_audit_logs_by_action_type(
        self,
        db: AsyncSession,
        action_type: ActionType,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs by action type"""
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.action_type == action_type)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_recent_audit_logs(
        self,
        db: AsyncSession,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get recent audit logs"""
        result = await db.execute(
            select(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()


# Global instance
audit_crud = AuditCRUD()
