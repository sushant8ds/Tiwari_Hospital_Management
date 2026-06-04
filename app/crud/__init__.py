"""
CRUD operations for Hospital Management System
"""

from app.crud.user import user_crud
from app.crud.patient import patient_crud
from app.crud.doctor import doctor_crud
from app.crud.visit import visit_crud

__all__ = [
    "user_crud",
    "patient_crud", 
    "doctor_crud",
    "visit_crud"
]