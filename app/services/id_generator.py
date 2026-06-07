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
        """Generate unique patient ID: P-YYMMM-XXXX"""
        from sqlalchemy import select
        from app.models.patient import Patient
        
        async with self._lock:
            now = datetime.now()
            yymm = now.strftime("%y%b").upper()
            prefix = f"P-{yymm}-"
            key = f"patient_{yymm}"
            
            if key not in self._counters:
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
                            self._counters[key] = last_seq
                        except ValueError:
                            self._counters[key] = 0
                    else:
                        self._counters[key] = 0
                else:
                    self._counters[key] = 0
                    
            self._counters[key] += 1
            new_sequence = self._counters[key]
            return f"{prefix}{new_sequence:04d}"
    
    async def generate_visit_id(self, db=None) -> str:
        """Generate unique visit ID: V + YYYYMMDD + HHMMSS + 3-digit counter.
        
        Format: VYYYYMMDDHHMMSSXXX (18 characters total)
        """
        from sqlalchemy import select
        from app.models.visit import Visit

        async with self._lock:
            now = datetime.now()
            date_str = now.strftime("%Y%m%d")
            time_str = now.strftime("%H%M%S")
            prefix = f"V{date_str}{time_str}"
            second_key = f"visit_{date_str}{time_str}"
            
            if second_key not in self._counters:
                if db:
                    result = await db.execute(
                        select(Visit.visit_id)
                        .where(Visit.visit_id.like(f"{prefix}%"))
                        .order_by(Visit.visit_id.desc())
                        .limit(1)
                    )
                    last_id = result.scalar()
                    if last_id:
                        try:
                            last_seq_str = last_id[len(prefix):]
                            self._counters[second_key] = int(last_seq_str)
                        except (ValueError, IndexError):
                            self._counters[second_key] = 0
                    else:
                        self._counters[second_key] = 0
                else:
                    self._counters[second_key] = 0
                    
            self._counters[second_key] += 1
            new_sequence = self._counters[second_key]
            
            display_seq = (new_sequence - 1) % 1000
            return f"{prefix}{display_seq:03d}"
    
    async def generate_ipd_id(self, db=None) -> str:
        """Generate unique IPD ID: IPD + YYYYMMDD + 4-digit sequential counter.
        
        Format: IPDYYYYMMDDXXXX (15 characters total)
        """
        from sqlalchemy import select
        from app.models.ipd import IPD

        async with self._lock:
            now = datetime.now()
            today = now.strftime("%Y%m%d")
            prefix = f"IPD{today}"
            key = f"ipd_{today}"
            
            if key not in self._counters:
                if db:
                    result = await db.execute(
                        select(IPD.ipd_id)
                        .where(IPD.ipd_id.like(f"{prefix}%"))
                        .order_by(IPD.ipd_id.desc())
                        .limit(1)
                    )
                    last_id = result.scalar()
                    if last_id:
                        try:
                            last_seq_str = last_id[len(prefix):]
                            self._counters[key] = int(last_seq_str)
                        except (ValueError, IndexError):
                            self._counters[key] = 0
                    else:
                        self._counters[key] = 0
                else:
                    self._counters[key] = 0
                    
            self._counters[key] += 1
            new_sequence = self._counters[key]
            
            display_seq = ((new_sequence - 1) % 9999) + 1
            return f"{prefix}{display_seq:04d}"
    
    async def generate_charge_id(self) -> str:
        """Generate unique charge ID: C + YYYYMMDD + HHMMSS + microsecond + random"""
        async with self._lock:
            import random
            now = datetime.now()
            date_time = now.strftime("%Y%m%d%H%M%S")
            micro = f"{now.microsecond:06d}"
            rand = f"{random.randint(0, 999):03d}"
            return f"C{date_time}{micro}{rand}"
    
    async def generate_user_id(self, db=None) -> str:
        """Generate unique user ID: U + YYYYMMDD + 3-digit sequence"""
        from sqlalchemy import select
        from app.models.user import User

        async with self._lock:
            now = datetime.now()
            today = now.strftime("%Y%m%d")
            prefix = f"U{today}"
            key = f"user_{today}"
            
            if key not in self._counters:
                if db:
                    result = await db.execute(
                        select(User.user_id)
                        .where(User.user_id.like(f"{prefix}%"))
                        .order_by(User.user_id.desc())
                        .limit(1)
                    )
                    last_id = result.scalar()
                    if last_id:
                        try:
                            last_seq_str = last_id[len(prefix):]
                            self._counters[key] = int(last_seq_str)
                        except (ValueError, IndexError):
                            self._counters[key] = 0
                    else:
                        self._counters[key] = 0
                else:
                    self._counters[key] = 0
                    
            self._counters[key] += 1
            new_sequence = self._counters[key]
            
            display_seq = ((new_sequence - 1) % 999) + 1
            sequence = str(display_seq).zfill(3)
            return f"{prefix}{sequence}"
    
    async def generate_doctor_id(self, db=None) -> str:
        """Generate unique doctor ID: D + YYYYMMDD + 3-digit sequence"""
        from sqlalchemy import select
        from app.models.doctor import Doctor

        async with self._lock:
            now = datetime.now()
            today = now.strftime("%Y%m%d")
            prefix = f"D{today}"
            key = f"doctor_{today}"
            
            if key not in self._counters:
                if db:
                    result = await db.execute(
                        select(Doctor.doctor_id)
                        .where(Doctor.doctor_id.like(f"{prefix}%"))
                        .order_by(Doctor.doctor_id.desc())
                        .limit(1)
                    )
                    last_id = result.scalar()
                    if last_id:
                        try:
                            last_seq_str = last_id[len(prefix):]
                            self._counters[key] = int(last_seq_str)
                        except (ValueError, IndexError):
                            self._counters[key] = 0
                    else:
                        self._counters[key] = 0
                else:
                    self._counters[key] = 0
                    
            self._counters[key] += 1
            new_sequence = self._counters[key]
            
            display_seq = ((new_sequence - 1) % 999) + 1
            sequence = str(display_seq).zfill(3)
            return f"{prefix}{sequence}"
    
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
    return await id_generator.generate_visit_id(db)


async def generate_ipd_id(db=None) -> str:
    """Generate IPD ID"""
    return await id_generator.generate_ipd_id(db)


async def generate_charge_id(db=None) -> str:
    """Generate charge ID"""
    return await id_generator.generate_charge_id()


async def generate_user_id(db=None) -> str:
    """Generate user ID"""
    return await id_generator.generate_user_id(db)


async def generate_doctor_id(db=None) -> str:
    """Generate doctor ID"""
    return await id_generator.generate_doctor_id(db)


async def generate_ot_id(db=None) -> str:
    """Generate OT ID"""
    return await id_generator.generate_ot_id()


async def generate_id(prefix: str, db=None) -> str:
    """Generate generic ID with prefix"""
    return await id_generator.generate_id(prefix)