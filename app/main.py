"""
Hospital OPD-IPD Management System
Main FastAPI application entry point
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting Hospital Management System...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    print("Shutting down Hospital Management System...")


# Create FastAPI application
app = FastAPI(
    title="Hospital OPD-IPD Management System",
    description="Comprehensive hospital management system for OPD, IPD, billing, and operations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Templates
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root(request: Request):
    """Root endpoint - redirect to dashboard"""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/patients/register")
async def patient_registration_page(request: Request):
    """Patient registration page"""
    return templates.TemplateResponse(
        "patients/register.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/patients/{patient_id}")
async def patient_details_page(request: Request, patient_id: str):
    """Patient details page"""
    return templates.TemplateResponse(
        "patients/details.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE,
            "patient_id": patient_id
        }
    )


@app.get("/opd/new")
async def opd_new_page(request: Request):
    """New OPD registration page"""
    return templates.TemplateResponse(
        "opd/new.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/opd/followup")
async def opd_followup_page(request: Request):
    """OPD follow-up registration page"""
    return templates.TemplateResponse(
        "opd/followup.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/opd/search")
async def opd_search_page(request: Request):
    """Patient search page"""
    return templates.TemplateResponse(
        "opd/search.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/ipd/admit")
async def ipd_admit_page(request: Request):
    """IPD admission page"""
    return templates.TemplateResponse(
        "ipd/admit.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/billing/investigations")
async def billing_investigations_page(request: Request):
    """Billing investigations page"""
    return templates.TemplateResponse(
        "billing/investigations.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/reports/daily")
async def reports_daily_page(request: Request):
    """Daily reports page"""
    return templates.TemplateResponse(
        "reports/daily.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Hospital Management System",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )