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
    
    async def generate_patient_id(self) -> str:
        """Generate unique patient ID: P + YYYYMMDD + 4-digit sequence"""
        async with self._lock:
            today = datetime.now().strftime("%Y%m%d")
            key = f"patient_{today}"
            
            if key not in self._counters:
                self._counters[key] = 0
            
            self._counters[key] += 1
            sequence = str(self._counters[key]).zfill(4)
            
            return f"P{today}{sequence}"
    
    async def generate_visit_id(self) -> str:
        """Generate unique visit ID: V + YYYYMMDD + HHMMSS + 3-digit sequence"""
        async with self._lock:
            now = datetime.now()
            date_time = now.strftime("%Y%m%d%H%M%S")
            key = f"visit_{date_time}"
            
            if key not in self._counters:
                self._counters[key] = 0
            
            self._counters[key] += 1
            sequence = str(self._counters[key]).zfill(3)
            
            return f"V{date_time}{sequence}"
    
    async def generate_ipd_id(self) -> str:
        """Generate unique IPD ID: IPD + YYYYMMDD + 4-digit sequence"""
        async with self._lock:
            today = datetime.now().strftime("%Y%m%d")
            key = f"ipd_{today}"
            
            if key not in self._counters:
                self._counters[key] = 0
            
            self._counters[key] += 1
            sequence = str(self._counters[key]).zfill(4)
            
            return f"IPD{today}{sequence}"
    
    async def generate_charge_id(self) -> str:
        """Generate unique charge ID: C + YYYYMMDD + HHMMSS + 3-digit sequence"""
        async with self._lock:
            now = datetime.now()
            date_time = now.strftime("%Y%m%d%H%M%S")
            key = f"charge_{date_time}"
            
            if key not in self._counters:
                self._counters[key] = 0
            
            self._counters[key] += 1
            sequence = str(self._counters[key]).zfill(3)
            
            return f"C{date_time}{sequence}"
    
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
        """Generate unique OT ID: OT + YYYYMMDD + HHMMSS + 3-digit sequence"""
        async with self._lock:
            now = datetime.now()
            date_time = now.strftime("%Y%m%d%H%M%S")
            key = f"ot_{date_time}"
            
            if key not in self._counters:
                self._counters[key] = 0
            
            self._counters[key] += 1
            sequence = str(self._counters[key]).zfill(3)
            
            return f"OT{date_time}{sequence}"
    
    async def generate_id(self, prefix: str) -> str:
        """Generate generic ID with given prefix"""
        async with self._lock:
            now = datetime.now()
            date_time = now.strftime("%Y%m%d%H%M%S")
            key = f"{prefix.lower()}_{date_time}"
            
            if key not in self._counters:
                self._counters[key] = 0
            
            self._counters[key] += 1
            sequence = str(self._counters[key]).zfill(3)
            
            return f"{prefix}{date_time}{sequence}"


# Global ID generator instance
id_generator = IDGenerator()


# Convenience functions for database operations
async def generate_patient_id(db=None) -> str:
    """Generate patient ID"""
    return await id_generator.generate_patient_id()


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