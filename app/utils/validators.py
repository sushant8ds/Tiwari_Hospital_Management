"""
Validation utilities
"""

import re
from typing import Optional


def validate_mobile_number(mobile: str) -> bool:
    """Validate Indian mobile number format"""
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, mobile))


def validate_patient_id(patient_id: str) -> bool:
    """Validate patient ID format: P + YYYYMMDD + 4-digit sequence"""
    pattern = r'^P\d{8}\d{4}$'
    return bool(re.match(pattern, patient_id))


def validate_visit_id(visit_id: str) -> bool:
    """Validate visit ID format: V + YYYYMMDD + HHMMSS + 3-digit sequence"""
    pattern = r'^V\d{8}\d{6}\d{3}$'
    return bool(re.match(pattern, visit_id))


def validate_ipd_id(ipd_id: str) -> bool:
    """Validate IPD ID format: IPD + YYYYMMDD + 4-digit sequence"""
    pattern = r'^IPD\d{8}\d{4}$'
    return bool(re.match(pattern, ipd_id))


def sanitize_string(value: Optional[str]) -> Optional[str]:
    """Sanitize string input"""
    if not value:
        return value
    return value.strip().title() if value.strip() else None


def validate_age(age: int) -> bool:
    """Validate age range"""
    return 0 <= age <= 150