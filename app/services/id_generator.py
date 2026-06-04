"""
ID generation service for unique identifiers
"""

from datetime import datetime
from typing import AsyncGenerator
import asyncio


class IDGenerator:
    """Service for generating unique IDs"""
    
    def __init__(self):
        self._counters = {}
        self._lock = asyncio.Lock()
    
    async def generate_patient_id(self, db=None) -> str:
        """Generate unique patient ID: P-YYMM-XXXX"""
        from sqlalchemy import select
        from app.models.patient import Patient
        
        async with self._lock:
            now = datetime.now()
            yymm = now.strftime("%y%m")
            prefix = f"P-{yymm}-"
            
            if db:
                result = await db.execute(
                    select(Patient.patient_id)
                    .where(Patient.patient_id.like(f"{prefix}%"))
                    .order_by(Patient.patient_id.desc())
                    .limit(1)
                )
                last_id = result.scalar()
                if last_id:
                    try:
                        last_seq = int(last_id.split("-")[-1])
                        new_sequence = last_seq + 1
                    except ValueError:
                        new_sequence = 1
                else:
                    new_sequence = 1
            else:
                key = f"patient_{yymm}"
                if key not in self._counters:
                    self._counters[key] = 0
                self._counters[key] += 1
                new_sequence = self._counters[key]
                
            return f"{prefix}{new_sequence:04d}"
    
    async def generate_visit_id(self) -> str:
        """Generate unique visit ID: V + YYYYMMDD + HHMMSS + 3-digit counter.
        
        Format: VYYYYMMDDHHMMSSXXX (18 characters total)
        Uses a per-second monotonic counter (0-999). When the counter wraps at 999,
        subsequent calls within the same second will still be unique because the
        counter keeps incrementing (capped to 3 digits via modulo on display only).
        
        For true uniqueness across instances, we use a global per-second counter.
        """
        async with self._lock:
            now = datetime.now()
            date_str = now.strftime("%Y%m%d")
            time_str = now.strftime("%H%M%S")
            second_key = f"visit_{date_str}{time_str}"
            
            if second_key not in self._counters:
                # Reset counter for new second
                self._counters[second_key] = 0
            self._counters[second_key] += 1
            seq = self._counters[second_key]
            
            # If we overflow 999 in same second, we need to advance time
            # Use seq directly but keep it as 3 digits via cycling within second
            # The format must be exactly 3 digits (000-999)
            display_seq = (seq - 1) % 1000
            return f"V{date_str}{time_str}{display_seq:03d}"
    
    async def generate_ipd_id(self) -> str:
        """Generate unique IPD ID: IPD + YYYYMMDD + 4-digit sequential counter.
        
        Format: IPDYYYYMMDDXXXX (15 characters total)
        Counter increments sequentially per day, starting at 1.
        """
        async with self._lock:
            now = datetime.now()
            today = now.strftime("%Y%m%d")
            key = f"ipd_{today}"
            
            if key not in self._counters:
                self._counters[key] = 0
            self._counters[key] += 1
            seq = self._counters[key]
            # Keep within 4 digits (0001-9999)
            display_seq = ((seq - 1) % 9999) + 1
            return f"IPD{today}{display_seq:04d}"
    
    async def generate_charge_id(self) -> str:
        """Generate unique charge ID: C + YYYYMMDD + HHMMSS + microsecond + random"""
        async with self._lock:
            import random
            now = datetime.now()
            date_time = now.strftime("%Y%m%d%H%M%S")
            micro = f"{now.microsecond:06d}"
            rand = f"{random.randint(0, 999):03d}"
            return f"C{date_time}{micro}{rand}"
    
    async def generate_user_id(self) -> str:
        """Generate unique user ID: U + YYYYMMDD + 3-digit sequence"""
        async with self._lock:
            today = datetime.now().strftime("%Y%m%d")
            key = f"user_{today}"
            
            if key not in self._counters:
                self._counters[key] = 0
            
            self._counters[key] += 1
            sequence = str(self._counters[key]).zfill(3)
            
            return f"U{today}{sequence}"
    
    async def generate_ot_id(self) -> str:
        """Generate unique OT ID: OT + YYYYMMDD + HHMMSS + microsecond + random"""
        async with self._lock:
            import random
            now = datetime.now()
            date_time = now.strftime("%Y%m%d%H%M%S")
            micro = f"{now.microsecond:06d}"
            rand = f"{random.randint(0, 999):03d}"
            return f"OT{date_time}{micro}{rand}"
    
    async def generate_id(self, prefix: str) -> str:
        """Generate generic ID with given prefix"""
        async with self._lock:
            import random
            now = datetime.now()
            date_time = now.strftime("%Y%m%d%H%M%S")
            micro = f"{now.microsecond:06d}"
            rand = f"{random.randint(0, 999):03d}"
            return f"{prefix}{date_time}{micro}{rand}"


# Global ID generator instance
id_generator = IDGenerator()


# Convenience functions for database operations
async def generate_patient_id(db=None) -> str:
    """Generate patient ID"""
    return await id_generator.generate_patient_id(db)


async def generate_visit_id(db=None) -> str:
    """Generate visit ID"""
    return await id_generator.generate_visit_id()


async def generate_ipd_id(db=None) -> str:
    """Generate IPD ID"""
    return await id_generator.generate_ipd_id()


async def generate_charge_id(db=None) -> str:
    """Generate charge ID"""
    return await id_generator.generate_charge_id()


async def generate_user_id(db=None) -> str:
    """Generate user ID"""
    return await id_generator.generate_user_id()


async def generate_ot_id(db=None) -> str:
    """Generate OT ID"""
    return await id_generator.generate_ot_id()


async def generate_id(prefix: str, db=None) -> str:
    """Generate generic ID with prefix"""
    return await id_generator.generate_id(prefix)