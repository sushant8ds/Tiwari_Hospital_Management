"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, patients, doctors, visits, ipd, billing, ot, payments, slips, discharge, audit, employees, reports, backup, dashboard

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
api_router.include_router(visits.router, prefix="/visits", tags=["visits"])
api_router.include_router(ipd.router, prefix="/ipd", tags=["ipd"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(ot.router, prefix="/ot", tags=["operation-theater"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(slips.router, prefix="/slips", tags=["slips"])
api_router.include_router(discharge.router, prefix="/discharge", tags=["discharge"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(backup.router, prefix="/backup", tags=["backup"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])