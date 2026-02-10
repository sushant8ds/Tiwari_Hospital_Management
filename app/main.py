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
    
    # Auto-seed database with initial data if empty
    await seed_initial_data()
    
    yield
    
    # Shutdown
    print("Shutting down Hospital Management System...")


async def seed_initial_data():
    """Automatically seed database with initial doctors and beds if empty"""
    from decimal import Decimal
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy import select
    from app.models.doctor import Doctor, DoctorStatus
    from app.models.bed import Bed, WardType, BedStatus
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        # Check if doctors exist
        async with async_session() as session:
            result = await session.execute(select(Doctor))
            existing_doctors = result.scalars().all()
            
            if not existing_doctors:
                print("📊 No doctors found. Seeding initial doctors...")
                doctors_data = [
                    {"name": "Dr. Nitish Tiwari", "department": "Orthopedics", "new_fee": 500, "followup_fee": 300},
                    {"name": "Dr. Muskan Tiwari", "department": "Dentist", "new_fee": 400, "followup_fee": 250},
                    {"name": "Dr. Rajesh Kumar", "department": "General Medicine", "new_fee": 300, "followup_fee": 200},
                    {"name": "Dr. Priya Sharma", "department": "Pediatrics", "new_fee": 350, "followup_fee": 250},
                    {"name": "Dr. Amit Singh", "department": "Surgery", "new_fee": 500, "followup_fee": 300},
                ]
                
                for idx, doc_data in enumerate(doctors_data, start=1):
                    doctor = Doctor(
                        doctor_id=f"DOC{idx:05d}",
                        name=doc_data["name"],
                        department=doc_data["department"],
                        new_patient_fee=Decimal(str(doc_data["new_fee"])),
                        followup_fee=Decimal(str(doc_data["followup_fee"])),
                        status=DoctorStatus.ACTIVE
                    )
                    session.add(doctor)
                
                await session.commit()
                print(f"✅ Added {len(doctors_data)} doctors successfully")
            else:
                print(f"ℹ️  Database already has {len(existing_doctors)} doctors")
        
        # Check if beds exist
        async with async_session() as session:
            result = await session.execute(select(Bed))
            existing_beds = result.scalars().all()
            
            if not existing_beds:
                print("🛏️  No beds found. Seeding initial beds...")
                beds_data = [
                    {"ward": WardType.GENERAL, "count": 10, "charge": 500},
                    {"ward": WardType.SEMI_PRIVATE, "count": 5, "charge": 1000},
                    {"ward": WardType.PRIVATE, "count": 5, "charge": 2000},
                ]
                
                bed_counter = 1
                for ward_info in beds_data:
                    for i in range(1, ward_info["count"] + 1):
                        bed = Bed(
                            bed_id=f"BED{bed_counter:05d}",
                            bed_number=f"{ward_info['ward'].value[:3]}-{i:02d}",
                            ward_type=ward_info["ward"],
                            per_day_charge=Decimal(str(ward_info["charge"])),
                            status=BedStatus.AVAILABLE
                        )
                        session.add(bed)
                        bed_counter += 1
                
                await session.commit()
                total_beds = sum(w["count"] for w in beds_data)
                print(f"✅ Added {total_beds} beds successfully")
            else:
                print(f"ℹ️  Database already has {len(existing_beds)} beds")
        
        print("✅ Database initialization complete!")
        
    except Exception as e:
        print(f"⚠️  Error seeding initial data: {str(e)}")
        print("   You may need to run: python init_render_db.py manually")


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


@app.get("/owner")
async def owner_dashboard_page(request: Request):
    """Owner dashboard page (Admin only)"""
    return templates.TemplateResponse(
        "owner/dashboard.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/owner/employees")
async def owner_employees_page(request: Request):
    """Owner employees management page (Admin only)"""
    return templates.TemplateResponse(
        "owner/employees.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/owner/salaries")
async def owner_salaries_page(request: Request):
    """Owner salary management page (Admin only)"""
    return templates.TemplateResponse(
        "owner/salaries.html",
        {
            "request": request,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/owner/doctors")
async def owner_doctors_page(request: Request):
    """Owner doctors management page (Admin only)"""
    return templates.TemplateResponse(
        "owner/doctors.html",
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